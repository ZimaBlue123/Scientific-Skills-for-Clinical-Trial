from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def _require_cols(df: pd.DataFrame, cols: Iterable[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要列: {missing}. 实际列: {list(df.columns)}")


def _ensure_positive(series: pd.Series, name: str) -> None:
    if (series <= 0).any():
        bad = series[series <= 0].head(10).to_list()
        raise ValueError(f"列 {name} 必须全为正数（用于对数变换）。示例异常值: {bad}")


def _z_value(alpha: float) -> float:
    # 近似：alpha=0.05 -> 1.96
    # 避免引入 scipy 依赖；监管递交中通常也接受正态近似说明
    if not (0 < alpha < 1):
        raise ValueError("alpha 必须在 (0,1) 内。")
    if abs(alpha - 0.05) < 1e-12:
        return 1.959963984540054
    if abs(alpha - 0.01) < 1e-12:
        return 2.5758293035489004
    if abs(alpha - 0.10) < 1e-12:
        return 1.6448536269514722
    return 1.959963984540054


def main() -> int:
    ap = argparse.ArgumentParser(description="个体水平 MixedLM：log-log 幂律衰减（用于组间斜率推断与预测）。")
    ap.add_argument("--in", dest="infile", required=True, help="输入CSV，至少包含 USUBJID,Group,t_post,以及滴度列")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--titer-col", default="TITER", help="滴度/浓度列名（默认 TITER）")
    ap.add_argument("--alpha", type=float, default=0.05, help="置信水平：alpha=0.05 表示 95% CI")
    ap.add_argument("--target-t-post", type=float, default=30.0, help="外推最大 t_post（如 30≈M36）")
    ap.add_argument("--grid-n", type=int, default=200, help="预测网格点数")
    ap.add_argument("--threshold", type=float, default=10.0, help="保护阈值（用于反解持续时间；点估计）")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.infile)
    _require_cols(df, ["USUBJID", "Group", "t_post", args.titer_col])
    df = df.copy().dropna(subset=["USUBJID", "Group", "t_post", args.titer_col])

    _ensure_positive(df["t_post"], "t_post")
    _ensure_positive(df[args.titer_col], args.titer_col)

    df["ln_t"] = np.log(df["t_post"].astype(float))
    df["ln_titer"] = np.log(df[args.titer_col].astype(float))

    formula = "ln_titer ~ ln_t * C(Group)"
    model = smf.mixedlm(formula, df, groups=df["USUBJID"])
    result = model.fit(reml=True, method="lbfgs")

    (outdir / "mixedlm_summary.txt").write_text(str(result.summary()), encoding="utf-8")
    (outdir / "run_metadata.json").write_text(
        json.dumps(
            {
                "formula": formula,
                "reml": True,
                "method": "lbfgs",
                "alpha": float(args.alpha),
                "target_t_post": float(args.target_t_post),
                "threshold": float(args.threshold),
                "input": str(args.infile),
                "titer_col": str(args.titer_col),
                "note": "CI is for fixed-effects marginal mean using normal approx; does not include random-effect uncertainty.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fe_params = result.fe_params
    cov_fe = result.cov_params().loc[fe_params.index, fe_params.index]
    exog_names = list(result.model.exog_names)

    groups = sorted(df["Group"].astype(str).unique().tolist())
    t_grid = np.linspace(1.0, float(args.target_t_post), int(args.grid_n))
    ln_t_grid = np.log(t_grid.astype(float))
    z = _z_value(float(args.alpha))

    pred_rows: List[dict] = []
    threshold_rows: List[dict] = []

    for g in groups:
        for t_post, ln_t in zip(t_grid, ln_t_grid, strict=True):
            x = np.zeros(len(exog_names), dtype=float)
            for i, name in enumerate(exog_names):
                if name == "Intercept":
                    x[i] = 1.0
                elif name == "ln_t":
                    x[i] = float(ln_t)
                elif name.startswith("C(Group)[T.") and name.endswith("]"):
                    lvl = name[len("C(Group)[T.") : -1]
                    x[i] = 1.0 if str(g) == lvl else 0.0
                elif name.startswith("ln_t:C(Group)[T.") and name.endswith("]"):
                    lvl = name[len("ln_t:C(Group)[T.") : -1]
                    x[i] = float(ln_t) if str(g) == lvl else 0.0
                else:
                    x[i] = 0.0

            beta = fe_params.to_numpy(dtype=float)
            ln_mean = float(np.dot(x, beta))
            var = float(np.dot(x, np.dot(cov_fe.to_numpy(dtype=float), x)))
            se = math.sqrt(max(var, 0.0))

            pred_rows.append(
                {
                    "Group": str(g),
                    "t_post": float(t_post),
                    "ln_mean": ln_mean,
                    "ln_mean_ci_lower": ln_mean - z * se,
                    "ln_mean_ci_upper": ln_mean + z * se,
                    "titer_mean": float(math.exp(ln_mean)),
                    "titer_ci_lower": float(math.exp(ln_mean - z * se)),
                    "titer_ci_upper": float(math.exp(ln_mean + z * se)),
                }
            )

        # 阈值时间点估计（点估计）
        idx = {n: i for i, n in enumerate(exog_names)}
        b0 = float(fe_params.iloc[idx["Intercept"]])
        b1 = float(fe_params.iloc[idx["ln_t"]])
        add0 = 0.0
        add1 = 0.0
        for name in exog_names:
            if name.startswith("C(Group)[T.") and name.endswith("]"):
                lvl = name[len("C(Group)[T.") : -1]
                if str(g) == lvl:
                    add0 += float(fe_params.loc[name])
            if name.startswith("ln_t:C(Group)[T.") and name.endswith("]"):
                lvl = name[len("ln_t:C(Group)[T.") : -1]
                if str(g) == lvl:
                    add1 += float(fe_params.loc[name])

        lnA = b0 + add0  # t_post=1
        slope = b1 + add1
        b = -slope
        A = math.exp(lnA)
        t_thr = float((A / float(args.threshold)) ** (1.0 / b)) if b > 0 else float("nan")
        threshold_rows.append({"Group": str(g), "A_at_t1": A, "b": float(b), "threshold": float(args.threshold), "t_post_at_threshold_point": t_thr})

    pred_df = pd.DataFrame(pred_rows)
    pred_df.to_csv(outdir / "mixedlm_predictions_fixed_effects.csv", index=False)
    pd.DataFrame(threshold_rows).to_csv(outdir / "mixedlm_threshold_time_point.csv", index=False)

    try:
        import matplotlib.pyplot as plt

        plt.rcParams.update(
            {
                "figure.dpi": 300,
                "axes.spines.top": False,
                "axes.spines.right": False,
            }
        )

        fig, ax = plt.subplots(figsize=(8.0, 5.6))
        colors = ["#2ca02c", "#d62728", "#1f77b4", "#ff7f0e"]
        cmap = {g: colors[i % len(colors)] for i, g in enumerate(groups)}

        for g in groups:
            pr = pred_df[pred_df["Group"] == g]
            ax.plot(pr["t_post"], pr["titer_mean"], linestyle="--", color=cmap[g], label=f"{g} fixed-effect mean")
            ax.fill_between(pr["t_post"], pr["titer_ci_lower"], pr["titer_ci_upper"], color=cmap[g], alpha=0.15, linewidth=0)

        ax.axhline(float(args.threshold), color="grey", linestyle=":", linewidth=1.0, label=f"threshold={float(args.threshold):g}")
        ax.set_yscale("log")
        ax.set_xlabel("t_post (months; aligned)")
        ax.set_ylabel("Titer [log scale]")
        ax.set_title("Antibody persistence projection (MixedLM; fixed-effect marginal mean)")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
        fig.tight_layout()
        fig.savefig(outdir / "mixedlm_projection.png", bbox_inches="tight")
        plt.close(fig)
    except Exception as e:  # noqa: BLE001
        (outdir / "plot_error.txt").write_text(str(e), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

