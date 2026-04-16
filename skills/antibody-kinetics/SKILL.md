---
name: antibody-kinetics
description: Analyze antibody kinetics and immune persistence (e.g., anti-HBs, neutralizing Ab) for CSR/regulatory submissions using power-law (log-log) decay models and subject-level linear mixed models (LMM/MixedLM). Use when the user mentions antibody kinetics, waning, persistence, GMC/GMT over time, M12+ extrapolation, power law model, decay slope comparison between arms (e.g., A2 vs C1), seroprotection threshold time, or CDE/FDA submission-ready inference and plots.
---

# Antibody Kinetics（抗体动力学）分析

## 适用范围与交付物

- **适用数据**：
  - **个体水平**：ADaM/分析数据（推荐）。至少包含 `USUBJID`、`Group`（或可映射到组别/程序）、时间点（建议派生为末免后/达峰后月数 `t_post`）、抗体滴度/浓度（如 IgG、anti-HBs）。
  - **汇总水平**：仅有 `GMC/GMT` 随时间点的表（可做探索性外推，不替代个体推断）。
- **核心监管问题**：
  - **组间衰减斜率差异**（交互项 `Group * ln(t_post)` 的推断）
  - **M12 以后免疫持久性预测**（外推至 M36/M60，提供 95% CI）
  - **保护阈值持续时间**（给定阈值反解达到时间及不确定性）
- **典型输出（CSR友好）**：
  - 模型设定与时间标尺对齐说明（`t_post` 定义、峰值/末免对齐）
  - 参数估计：截距（\(\ln A\)）与衰减斜率（\(b\)）及其 CI
  - 组间比较：交互项估计、P 值、效应量解释
  - 图：观测点 + 拟合曲线 + 置信区间带；建议 Y 轴对数刻度

## 默认方法（推荐顺序）

### 1) 时间变量对齐（强制优先）

- **原则**：组间比较必须在同一生理衰减阶段上进行。
- **做法**：
  - 构建 `t_post`：定义为“末次免疫后（或达峰后）月数”
  - 为避免 \(\ln(0)\)，将对齐基准点设为 `t_post = 1`（例如全免后 1 个月的访视）
- **常见情形**：
  - A2（0,1）与 C1（0,1,6）若直接用研究访视月会错位；应转为各自末免/达峰后的 `t_post`。

### 2) 幂律模型（Power Law）作为衰减形状的默认基线

- **模型**：\( GMC(t) = A \cdot t^{-b} \)
- **线性化**：\(\ln(GMC(t)) = \ln(A) - b \cdot \ln(t)\)
- **解释**：
  - \(\ln(A)\)：对数尺度截距（对齐基准点的水平）
  - \(b\)：衰减速率（越大越快）

### 3) 个体水平推断：线性混合效应模型（LMM / MixedLM）

- **因变量**：`ln_titer`（\(\ln\) 或 \(\log_{10}\) 一致即可）
- **固定效应**：`ln_t`、`Group`、`ln_t:Group`，可加协变量（年龄、性别、基线、中心等）
- **随机效应**：至少随机截距 `1|USUBJID`；收敛允许时考虑随机斜率 `ln_t|USUBJID`
- **主检验**：交互项 `ln_t:Group` 的估计与 P 值（组间衰减斜率差异）

### 4) 预测与阈值时间

- **预测**：外推到目标 `t_post`（如 30 对应约 M36）得到边际均值与 95% CI，再反变换回 GMC
- **阈值时间**：给定阈值 `T`，解 \(T = A \cdot t^{-b}\Rightarrow t = (A/T)^{1/b}\)。不确定性优先使用参数协方差的 Delta method 或自助法（bootstrapping）。

## 操作清单（闭环、可审计）

1. **数据准备**：定义并记录 `t_post` 规则；对数转换；处理 BLQ/缺失（在分析计划中写清）
2. **探索性检查**：对数尺度散点图；异常值与访视窗口核对
3. **主模型拟合**：MixedLM（个体数据）；必要时对比随机结构与残差诊断
4. **推断与报告**：交互项、斜率、预测点与 CI；阈值时间与敏感性分析
5. **可复现交付**：输出模型汇总、参数表、图（高分辨率）、运行日志与版本信息

## 快速启动（附带脚本）

- **汇总GMC幂律拟合与外推**：运行 `scripts/fit_powerlaw_summary.py`
- **个体水平 MixedLM 模板**：运行 `scripts/fit_mixedlm_subject.py`
- **个体数据端到端 CSR 工作流（推荐）**：运行 `scripts/run_antibody_kinetics_pipeline.py`

个体数据管线会自动完成：`ln` 变换、MixedLM 拟合、M12+ 外推预测（固定效应边际均值 + CI）、阈值持续时间（Delta method CI）、以及审计输出（`run_metadata.json`）。

更多细节见：
- [reference.md](reference.md)
- [examples.md](examples.md)
