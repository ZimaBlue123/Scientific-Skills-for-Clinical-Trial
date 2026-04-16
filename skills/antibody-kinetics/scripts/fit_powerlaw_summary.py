from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True)
class PowerLawFit:
    group: str
    lnA: float
    slope_ln_t: float  # ln(GMC) = lnA + slope*ln(t); b = -slope
    b: float
    r2: float


def _require_cols(df: pd.DataFrame, cols: Iterable[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要列: {missing}. 实际列: {list(df.columns)}")


def _ensure_positive(series: pd.Series, name: str) -> None:
    if (series <= 0).any():
        bad = series[series <= 0].head(10).to_list()
        raise ValueError(f"列 {name} 必须全为正数（用于对数变换）。示例异常值: {bad}")


def fit_powerlaw_by_group(df: pd.DataFrame) -> Tuple[Dict[str, sm.regression.linear_model.RegressionResultsWrapper], List[PowerLawFit]]:
    _require_cols(df, ["Group", "t_post", "GMC"])
    df = df.copy()

    _ensure_positive(df["t_post"], "t_post")
    _ensure_positive(df["GMC"], "GMC")

    df["ln_t"] = np.log(df["t_post"].astype(float))
    df["ln_gmc"] = np.log(df["GMC"].astype(float))

    models: Dict[str, sm.regression.linear_model.RegressionResultsWrapper] = {}
    fits: List[PowerLawFit] = []

    for group, g in df.groupby("Group", sort=True):
        if len(g) < 2:
            raise ValueError(f"组 {group} 的记录数不足（至少2个时间点才能拟合）。")
        X = sm.add_constant(g["ln_t"])
        y = g["ln_gmc"]
        model = sm.OLS(y, X).fit()
        models[str(group)] = model

        lnA = float(model.params["const"])
        slope = float(model.params["ln_t"])
        fits.append(
            PowerLawFit(
                group=str(group),
                lnA=lnA,
                slope_ln_t=slope,
                b=-slope,
                r2=float(model.rsquared),
            )
        )

    return models, fits


def predict_curve(
    model: sm.regression.linear_model.RegressionResultsWrapper,
    t_post_grid: np.ndarray,
    alpha: float = 0.05,
) -> pd.DataFrame:
    ln_t = np.log(t_post_grid.astype(float))
    Xp = sm.add_constant(ln_t, has_constant="add")
    pred = model.get_prediction(Xp).summary_frame(alpha=alpha)
    out = pd.DataFrame(
        {
            "t_post": t_post_grid,
            "ln_mean": pred["mean"].to_numpy(),
            "ln_mean_ci_lower": pred["mean_ci_lower"].to_numpy(),
            "ln_mean_ci_upper": pred["mean_ci_upper"].to_numpy(),
        }
    )
    out["gmc_mean"] = np.exp(out["ln_mean"])
    out["gmc_ci_lower"] = np.exp(out["ln_mean_ci_lower"])
    out["gmc_ci_upper"] = np.exp(out["ln_mean_ci_upper"])
    return out


def threshold_time_from_params(A: float, b: float, threshold: float) -> float:
    if A <= 0 or b <= 0 or threshold <= 0:
        raise ValueError("A、b、threshold 必须为正数。")
    return float((A / threshold) ** (1.0 / b))


def main() -> int:
    ap = argparse.ArgumentParser(description="Power-law(幂律)模型：基于汇总GMC的log-log拟合、外推、绘图。")
    ap.add_argument("--in", dest="infile", required=True, help="输入CSV，至少包含 Group,t_post,GMC")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--target-t-post", type=float, default=30.0, help="外推的最大 t_post（如 30≈M36）")
    ap.add_argument("--grid-n", type=int, default=200, help="预测网格点数")
    ap.add_argument("--threshold", type=float, default=10.0, help="保护阈值（用于反解持续时间）")
    ap.add_argument("--alpha", type=float, default=0.05, help="置信水平：alpha=0.05 表示 95% CI")
    ap.add_argument("--study-month-offset", type=float, default=0.0, help="若未提供StudyMonth，则用 StudyMonth=t_post+offset")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.infile)
    models, fits = fit_powerlaw_by_group(df)

    # 预测与阈值时间
    t_grid = np.linspace(1.0, float(args.target_t_post), int(args.grid_n))
    pred_rows: List[pd.DataFrame] = []
    threshold_rows: List[dict] = []
    for f in fits:
        model = models[f.group]
        pred = predict_curve(model, t_grid, alpha=float(args.alpha))
        pred.insert(0, "Group", f.group)
        pred_rows.append(pred)

        A = math.exp(f.lnA)
        t_thr = threshold_time_from_params(A=A, b=f.b, threshold=float(args.threshold))
        threshold_rows.append({"Group": f.group, "A": A, "b": f.b, "threshold": float(args.threshold), "t_post_at_threshold": t_thr})

    pred_df = pd.concat(pred_rows, ignore_index=True)
    pred_df.to_csv(outdir / "powerlaw_predictions.csv", index=False)

    fit_df = pd.DataFrame([asdict(x) for x in fits]).sort_values(["group"])
    fit_df.to_csv(outdir / "powerlaw_fits.csv", index=False)

    pd.DataFrame(threshold_rows).to_csv(outdir / "powerlaw_threshold_time.csv", index=False)
    (outdir / "run_metadata.json").write_text(
        json.dumps(
            {
                "method": "OLS on ln(GMC) ~ const + ln(t_post) by Group (summary-level; exploratory)",
                "alpha": float(args.alpha),
                "target_t_post": float(args.target_t_post),
                "threshold": float(args.threshold),
                "input": str(args.infile),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 绘图（延迟导入 matplotlib，避免无图环境报错阻断表格输出）
    try:
        import matplotlib.pyplot as plt

        plt.rcParams.update(
            {
                "figure.dpi": 300,
                "axes.spines.top": False,
                "axes.spines.right": False,
            }
        )

        # 观测点（若提供 StudyMonth 则优先）
        plot_df = df.copy()
        if "StudyMonth" not in plot_df.columns:
            plot_df["StudyMonth"] = plot_df["t_post"].astype(float) + float(args.study_month_offset)

        pred_plot = pred_df.copy()
        pred_plot["StudyMonth"] = pred_plot["t_post"].astype(float) + float(args.study_month_offset)

        fig, ax = plt.subplots(figsize=(8.0, 5.6))
        groups = sorted(pred_plot["Group"].unique().tolist())
        colors = ["#2ca02c", "#d62728", "#1f77b4", "#ff7f0e"]
        cmap = {g: colors[i % len(colors)] for i, g in enumerate(groups)}

        for g in groups:
            obs = plot_df[plot_df["Group"] == g]
            pr = pred_plot[pred_plot["Group"] == g]

            ax.scatter(obs["StudyMonth"], obs["GMC"], s=40, color=cmap[g], label=f"{g} observed", zorder=3)
            ax.plot(pr["StudyMonth"], pr["gmc_mean"], linestyle="--", color=cmap[g], label=f"{g} power-law fit")
            ax.fill_between(pr["StudyMonth"], pr["gmc_ci_lower"], pr["gmc_ci_upper"], color=cmap[g], alpha=0.15, linewidth=0)

        ax.axhline(float(args.threshold), color="grey", linestyle=":", linewidth=1.0, label=f"threshold={float(args.threshold):g}")
        ax.set_yscale("log")
        ax.set_xlabel("Time (Study Month)")
        ax.set_ylabel("GMC [log scale]")
        ax.set_title("Antibody persistence projection (power-law; summary-level)")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
        fig.tight_layout()
        fig.savefig(outdir / "powerlaw_projection.png", bbox_inches="tight")
        plt.close(fig)
    except Exception as e:  # noqa: BLE001
        (outdir / "plot_error.txt").write_text(str(e), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

