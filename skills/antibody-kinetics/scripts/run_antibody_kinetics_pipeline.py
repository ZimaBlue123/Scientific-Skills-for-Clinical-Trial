from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Dict, Iterable, List, Literal, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


LogBase = Literal["e", "10"]


@dataclass(frozen=True)
class ThresholdCI:
    group: str
    threshold: float
    ln_t_post_at_threshold: float
    t_post_at_threshold: float
    ln_t_post_ci_lower: float
    ln_t_post_ci_upper: float
    t_post_ci_lower: float
    t_post_ci_upper: float


def _require_cols(df: pd.DataFrame, cols: Iterable[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要列: {missing}. 实际列: {list(df.columns)}")


def _ensure_positive(df: pd.DataFrame, col: str) -> None:
    if (df[col] <= 0).any():
        bad = df.loc[df[col] <= 0, col].head(10).to_list()
        raise ValueError(f"列 {col} 必须全为正数（用于对数变换）。示例异常值: {bad}")


def _normal_z(alpha: float) -> float:
    if not (0 < alpha < 1):
        raise ValueError("alpha 必须在 (0,1) 内。")
    return float(NormalDist().inv_cdf(1 - alpha / 2.0))


def _make_log_fns(log_base: LogBase):
    if log_base == "e":
        log_fn = np.log
        pow_fn = np.exp
        t_from_log = np.exp
        y_from_t = np.log
    elif log_base == "10":
        log_fn = np.log10
        pow_fn = lambda x: np.power(10.0, x)  # noqa: E731
        t_from_log = lambda x: np.power(10.0, x)  # noqa: E731
        y_from_t = np.log10
    else:
        raise ValueError("log_base 仅支持 'e' 或 '10'")

    return log_fn, pow_fn, t_from_log, y_from_t


def _design_vector(
    exog_names: Sequence[str],
    *,
    group: str,
    ln_t: float,
    group_ref: Optional[str],
    covar_values: Dict[str, float],
) -> np.ndarray:
    """
    依据 statsmodels formula 生成的 exog_names，把单个预测点映射到系数向量空间。

    约束：此实现假设协变量均为数值且不含复杂类别变量交互。
    """

    x = np.zeros(len(exog_names), dtype=float)
    for i, name in enumerate(exog_names):
        if name == "Intercept":
            x[i] = 1.0
        elif name == "ln_t":
            x[i] = float(ln_t)
        elif name.startswith("C(Group)[T.") and name.endswith("]"):
            lvl = name[len("C(Group)[T.") : -1]
            x[i] = 1.0 if str(group) == lvl else 0.0
        elif name.startswith("ln_t:C(Group)[T.") and name.endswith("]"):
            lvl = name[len("ln_t:C(Group)[T.") : -1]
            x[i] = float(ln_t) if str(group) == lvl else 0.0
        else:
            # 连续协变量：按名称直接映射
            if name in covar_values:
                x[i] = float(covar_values[name])
            else:
                # 如果公式里出现了我们没处理的特征（如类别哑变量等），直接报错让用户显式调整。
                raise ValueError(
                    f"无法映射 exog 列名到设计向量：{name}. "
                    "当前管线仅支持数值协变量且不包含类别哑变量交互。"
                )
    return x


def _predict_fixed_effect_mean_and_ci(
    *,
    result,
    exog_names: Sequence[str],
    groups: Sequence[str],
    t_grid: np.ndarray,
    log_base: LogBase,
    covar_values: Dict[str, float],
    alpha: float,
) -> pd.DataFrame:
    beta = result.fe_params.to_numpy(dtype=float)
    cov_fe = result.cov_params().loc[result.fe_params.index, result.fe_params.index].to_numpy(dtype=float)
    z = _normal_z(alpha)

    _, pow_fn, _, _ = _make_log_fns(log_base)

    rows: List[dict] = []
    for g in groups:
        for t_post in t_grid:
            if log_base == "e":
                ln_t = float(math.log(float(t_post)))
            else:
                ln_t = float(math.log10(float(t_post)))

            x = _design_vector(
                exog_names,
                group=str(g),
                ln_t=ln_t,
                group_ref=None,
                covar_values=covar_values,
            )
            ln_mean = float(np.dot(x, beta))
            var = float(x.T @ cov_fe @ x)
            se = math.sqrt(max(var, 0.0))
            ln_lower = ln_mean - z * se
            ln_upper = ln_mean + z * se

            t_mean = float(pow_fn(ln_mean))
            t_lower = float(pow_fn(ln_lower))
            t_upper = float(pow_fn(ln_upper))
            rows.append(
                {
                    "Group": str(g),
                    "t_post": float(t_post),
                    "ln_t": ln_t,
                    "ln_mean": ln_mean,
                    "ln_mean_ci_lower": ln_lower,
                    "ln_mean_ci_upper": ln_upper,
                    "titer_mean": t_mean,
                    "titer_ci_lower": t_lower,
                    "titer_ci_upper": t_upper,
                }
            )
    return pd.DataFrame(rows)


def _extract_group_params_from_design(
    *,
    exog_names: Sequence[str],
    result,
    group: str,
    covar_values: Dict[str, float],
) -> Tuple[float, float]:
    """
    返回：
    - lnA：在 ln_t=0（即 t_post=1）的预测水平（log 标度）
    - slope：log(titer) 对 ln_t 的斜率（线性模型中关于 ln_t 的系数）
    """
    beta = result.fe_params.to_numpy(dtype=float)

    # ln_t=0
    x0 = _design_vector(exog_names, group=str(group), ln_t=0.0, group_ref=None, covar_values=covar_values)
    lnA = float(x0 @ beta)

    # ln_t=1（用于得到 slope：y(1)-y(0)）
    x1 = _design_vector(exog_names, group=str(group), ln_t=1.0, group_ref=None, covar_values=covar_values)
    y1 = float(x1 @ beta)
    slope = y1 - lnA
    return lnA, slope


def _delta_method_threshold_ci(
    *,
    threshold: float,
    log_base: LogBase,
    alpha: float,
    result,
    exog_names: Sequence[str],
    groups: Sequence[str],
    covar_values: Dict[str, float],
) -> List[ThresholdCI]:
    beta = result.fe_params.to_numpy(dtype=float)
    cov_fe = result.cov_params().loc[result.fe_params.index, result.fe_params.index].to_numpy(dtype=float)
    z = _normal_z(alpha)

    _, pow_fn, _, y_from_t = _make_log_fns(log_base)
    y_thr = float(y_from_t(float(threshold)))

    out: List[ThresholdCI] = []

    # 有限差分步长（相对步长）
    eps_scale = 1e-5

    for g in groups:
        lnA, slope = _extract_group_params_from_design(
            exog_names=exog_names,
            result=result,
            group=str(g),
            covar_values=covar_values,
        )

        if abs(slope) < 1e-12:
            out.append(
                ThresholdCI(
                    group=str(g),
                    threshold=float(threshold),
                    ln_t_post_at_threshold=float("nan"),
                    t_post_at_threshold=float("nan"),
                    ln_t_post_ci_lower=float("nan"),
                    ln_t_post_ci_upper=float("nan"),
                    t_post_ci_lower=float("nan"),
                    t_post_ci_upper=float("nan"),
                )
            )
            continue

        ln_t_post_at_threshold = float((y_thr - lnA) / slope)  # 这是 log_base(t_post)
        t_post_at_threshold = float(pow_fn(ln_t_post_at_threshold))

        # delta method：对 ln_t_post_at_threshold 的梯度数值求导
        grad = np.zeros_like(beta, dtype=float)

        for i in range(len(beta)):
            eps = eps_scale * max(1.0, abs(beta[i]))
            beta_p = beta.copy()
            beta_m = beta.copy()
            beta_p[i] += eps
            beta_m[i] -= eps

            # 重新计算 lnA 和 slope（依赖 beta）
            # 注意：design_vector(x) 与 covar_values/ln_t/群组无关，只是 dot 产品不同。
            x0 = _design_vector(exog_names, group=str(g), ln_t=0.0, group_ref=None, covar_values=covar_values)
            x1 = _design_vector(exog_names, group=str(g), ln_t=1.0, group_ref=None, covar_values=covar_values)
            lnA_p = float(x0 @ beta_p)
            y1_p = float(x1 @ beta_p)
            slope_p = y1_p - lnA_p

            lnA_m = float(x0 @ beta_m)
            y1_m = float(x1 @ beta_m)
            slope_m = y1_m - lnA_m

            g_p = (y_thr - lnA_p) / slope_p if abs(slope_p) >= 1e-12 else float("nan")
            g_m = (y_thr - lnA_m) / slope_m if abs(slope_m) >= 1e-12 else float("nan")
            grad[i] = (g_p - g_m) / (2.0 * eps)

        var_g = float(grad.T @ cov_fe @ grad)
        se_g = math.sqrt(max(var_g, 0.0))

        ln_lower = ln_t_post_at_threshold - z * se_g
        ln_upper = ln_t_post_at_threshold + z * se_g
        t_lower = float(pow_fn(ln_lower))
        t_upper = float(pow_fn(ln_upper))

        out.append(
            ThresholdCI(
                group=str(g),
                threshold=float(threshold),
                ln_t_post_at_threshold=float(ln_t_post_at_threshold),
                t_post_at_threshold=float(t_post_at_threshold),
                ln_t_post_ci_lower=float(ln_lower),
                ln_t_post_ci_upper=float(ln_upper),
                t_post_ci_lower=float(t_lower),
                t_post_ci_upper=float(t_upper),
            )
        )

    return out


def _fit_mixedlm(
    df: pd.DataFrame,
    *,
    group_col: str,
    ln_titer_col: str,
    ln_t_col: str,
    covars: Sequence[str],
    reml: bool,
):
    covar_expr = ""
    if covars:
        # 这里假设 covars 是数值列名，且不需要 C() 包裹。
        covar_expr = " + " + " + ".join(covars)

    formula = f"{ln_titer_col} ~ {ln_t_col} * C({group_col}){covar_expr}"
    model = smf.mixedlm(formula, df, groups=df["USUBJID"])
    result = model.fit(reml=reml, method="lbfgs")
    return formula, result


def main() -> int:
    ap = argparse.ArgumentParser(description="个体水平抗体动力学（幂律形状）管线：MixedLM + M12+ 外推 + 阈值持续时间（含CI）。")
    ap.add_argument("--infile", required=True, help="输入 CSV（建议在 data/ 下；不要提交原始数据）。")
    ap.add_argument("--outdir", required=True, help="输出目录（建议用 output/ 下）。")

    ap.add_argument("--usubjid-col", default="USUBJID", help="受试者ID列名（默认 USUBJID）。")
    ap.add_argument("--group-col", default="Group", help="分组/程序列名（默认 Group）。")
    ap.add_argument("--t-post-col", default="t_post", help="t_post（末免后/月数对齐）列名（默认 t_post）。")
    ap.add_argument("--titer-col", default="TITER", help="抗体滴度/浓度列名（默认 TITER）。")

    ap.add_argument("--log-base", default="e", choices=["e", "10"], help="对数底数：e=自然对数，10=以10为底（b不变）。")
    ap.add_argument("--alpha", type=float, default=0.05, help="置信水平：alpha=0.05 对应 95% CI。")
    ap.add_argument("--reml", action="store_true", help="使用 REML（默认 False）。")

    ap.add_argument("--covars", default="", help="固定效应协变量（逗号分隔；仅支持数值列）。例如：Age,Sex,BaselineIgG")
    ap.add_argument("--covar-strategy", default="mean", choices=["mean"], help="协变量用于预测时的取值策略（默认 mean）。")

    ap.add_argument("--target-t-post", type=float, default=30.0, help="外推最大 t_post（如 30≈M36）。")
    ap.add_argument("--grid-n", type=int, default=200, help="预测网格点数。")
    ap.add_argument(
        "--key-t-post",
        default="18,30",
        help="需要在输出中直接报数的关键 t_post（逗号分隔；例如 18,30 对应 M24/M36）。",
    )
    ap.add_argument("--threshold", type=float, default=10.0, help="保护阈值（如 anti-HBs=10 mIU/mL）。用于反解持续时间。")

    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.infile)
    df = df.copy()

    # 字段重命名到管线内部约定字段名，降低公式/后续处理复杂度
    df = df.rename(
        columns={
            args.usubjid_col: "USUBJID",
            args.group_col: "Group",
            args.t_post_col: "t_post",
            args.titer_col: "TITER",
        }
    )

    _require_cols(df, ["USUBJID", "Group", "t_post", "TITER"])
    _ensure_positive(df, "t_post")
    _ensure_positive(df, "TITER")
    df = df.dropna(subset=["USUBJID", "Group", "t_post", "TITER"])

    log_base: LogBase = args.log_base  # type: ignore[assignment]
    log_fn, pow_fn, _, y_from_t = _make_log_fns(log_base)

    df["ln_t"] = log_fn(df["t_post"].astype(float))
    df["ln_titer"] = log_fn(df["TITER"].astype(float))

    covars = [c for c in (args.covars or "").split(",") if c.strip()]
    covars = [c.strip() for c in covars]
    for c in covars:
        if c not in df.columns:
            raise ValueError(f"--covars 中指定列不存在：{c}. 实际列: {list(df.columns)}")

    # 协变量用于预测时的取值
    covar_values: Dict[str, float] = {}
    if covars:
        if args.covar_strategy == "mean":
            for c in covars:
                covar_values[c] = float(df[c].astype(float).mean())
        else:
            raise ValueError("当前仅支持 covar-strategy=mean。")

    # 只允许在设计向量里用 covar_values 中出现的 exog 名称。
    # 如果 formula 里引入了额外项（如 C(covar) 类别哑变量），会在 _design_vector 时报错。
    formula, result = _fit_mixedlm(
        df,
        group_col="Group",
        ln_titer_col="ln_titer",
        ln_t_col="ln_t",
        covars=covars,
        reml=bool(args.reml),
    )

    (outdir / "mixedlm_summary.txt").write_text(str(result.summary()), encoding="utf-8")

    exog_names = list(result.model.exog_names)
    groups = sorted(df["Group"].astype(str).unique().tolist())
    key_t_post = [float(x.strip()) for x in str(args.key_t_post).split(",") if x.strip()]
    t_grid = np.linspace(1.0, float(args.target_t_post), int(args.grid_n))
    if key_t_post:
        t_grid = np.unique(np.concatenate([t_grid, np.array(key_t_post, dtype=float)]))

    pred_df = _predict_fixed_effect_mean_and_ci(
        result=result,
        exog_names=exog_names,
        groups=groups,
        t_grid=t_grid,
        log_base=log_base,
        covar_values=covar_values,
        alpha=float(args.alpha),
    )
    pred_df.to_csv(outdir / "fixed_effect_predictions.csv", index=False)

    # 关键时间点直接报数（便于 CSR/表格生成）
    key_pred = pred_df[pred_df["t_post"].isin(key_t_post)].copy()
    key_pred.to_csv(outdir / "key_timepoint_predictions.csv", index=False)

    # 阈值持续时间（含 Delta method CI）
    thresh_cis = _delta_method_threshold_ci(
        threshold=float(args.threshold),
        log_base=log_base,
        alpha=float(args.alpha),
        result=result,
        exog_names=exog_names,
        groups=groups,
        covar_values=covar_values,
    )

    thresh_df = pd.DataFrame([asdict(x) for x in thresh_cis])
    thresh_df.to_csv(outdir / "threshold_time_ci.csv", index=False)

    # 产出 power-law 参数（以 b 表示衰减斜率绝对值；b 越大衰减越快）
    rows_params: List[dict] = []
    for g in groups:
        lnA, slope = _extract_group_params_from_design(
            exog_names=exog_names,
            result=result,
            group=g,
            covar_values=covar_values,
        )
        b = -slope
        A = float(pow_fn(lnA))
        rows_params.append({"Group": g, "A_at_t_post=1": A, "b": float(b), "lnA": float(lnA), "slope_ln_scale": float(slope)})
    params_df = pd.DataFrame(rows_params)
    params_df.to_csv(outdir / "powerlaw_params_from_mixedlm.csv", index=False)

    # 组间衰减斜率差异（交互项）用于 CSR 叙述
    interaction_pvalues: Dict[str, float] = {}
    for name in result.pvalues.index.tolist():
        if name.startswith("ln_t:C(Group)[T.") and name.endswith("]"):
            lvl = name[len("ln_t:C(Group)[T.") : -1]
            interaction_pvalues[lvl] = float(result.pvalues[name])

    # statsmodels 的参考组对应 “缺失交互项”的那一组（在当前数据的 Group 水平中挑剩下的）
    nonref_levels = set(interaction_pvalues.keys())
    ref_candidates = [g for g in groups if str(g) not in nonref_levels]
    ref_group = str(ref_candidates[0]) if ref_candidates else str(groups[0])

    comp_rows: List[dict] = []
    params_df_idx = params_df.set_index("Group")
    for g in groups:
        b_row = float(params_df_idx.loc[str(g), "b"])
        slope_row = float(params_df_idx.loc[str(g), "slope_ln_scale"])
        p_vs_ref = float("nan")
        if str(g) != ref_group:
            p_vs_ref = float(interaction_pvalues.get(str(g), float("nan")))
        comp_rows.append({"Group": str(g), "b": b_row, "slope_ln_scale": slope_row, "p_vs_reference_slope": p_vs_ref, "reference_group": ref_group})

    pd.DataFrame(comp_rows).to_csv(outdir / "group_slope_comparison.csv", index=False)

    # 审计元信息
    run_metadata = {
        "pipeline": "antibody-kinetics MixedLM + extrapolation",
        "formula": formula,
        "log_base": log_base,
        "alpha": float(args.alpha),
        "reml": bool(args.reml),
        "covars": covars,
        "target_t_post": float(args.target_t_post),
        "grid_n": int(args.grid_n),
        "threshold": float(args.threshold),
        "input": str(args.infile),
        "outputs": {
            "mixedlm_summary": "mixedlm_summary.txt",
            "predictions": "fixed_effect_predictions.csv",
            "threshold_ci": "threshold_time_ci.csv",
            "powerlaw_params": "powerlaw_params_from_mixedlm.csv",
            "slope_comparison": "group_slope_comparison.csv",
        },
        "note": "预测与CI基于固定效应（固定效应边际均值）；随机效应不计入预测不确定性（CSR中需如实披露）。",
    }
    (outdir / "run_metadata.json").write_text(json.dumps(run_metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # 绘图（固定效应外推曲线）
    try:
        import matplotlib.pyplot as plt

        plot_dir = outdir / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(9, 5.8))
        colors = ["#2ca02c", "#d62728", "#1f77b4", "#ff7f0e", "#9467bd"]
        cmap = {g: colors[i % len(colors)] for i, g in enumerate(groups)}

        # 观测点：按 t_post+Group 聚合均值（避免散点过密）
        obs = df.groupby(["Group", "t_post"], as_index=False)["TITER"].mean()
        for g in groups:
            sub_obs = obs[obs["Group"].astype(str) == str(g)]
            ax.scatter(sub_obs["t_post"], sub_obs["TITER"], s=16, alpha=0.6, color=cmap[g], label=f"{g} observed (mean)")

            sub_pred = pred_df[pred_df["Group"].astype(str) == str(g)].sort_values("t_post")
            ax.plot(sub_pred["t_post"], sub_pred["titer_mean"], color=cmap[g], linestyle="--", linewidth=2.0, label=f"{g} fitted mean")
            ax.fill_between(sub_pred["t_post"], sub_pred["titer_ci_lower"], sub_pred["titer_ci_upper"], color=cmap[g], alpha=0.15)

        ax.axhline(float(args.threshold), color="grey", linestyle=":", linewidth=1.2, label=f"threshold={float(args.threshold):g}")
        ax.set_yscale("log")
        ax.set_xlabel("t_post (months; aligned)")
        ax.set_ylabel("Titer (log scale)")
        ax.set_title("Antibody persistence projection (MixedLM; fixed-effect marginal mean)")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
        fig.tight_layout()
        fig.savefig(plot_dir / "persistence_projection.png", bbox_inches="tight")
        plt.close(fig)
    except Exception as e:  # noqa: BLE001
        (outdir / "plot_error.txt").write_text(str(e), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

