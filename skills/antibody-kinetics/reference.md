## 统计方法细则（监管递交友好）

### 时间标尺（t_post）定义建议

- **推荐主方案**：以“末次免疫后 1 个月”为 `t_post = 1`。
  - 示例：若某组末免在研究月 M6，则研究月 M7 设为 `t_post=1`。
- **替代方案（需论证）**：以“达峰访视后 1 个月”为 `t_post=1`，适用于峰值并非固定在末免后 1 个月的抗体。
- **记录要求**：在方法章节明确 `t_post` 与研究访视月的映射规则（可写成一张映射表），确保组间可比性。

### 对数尺度与单位

- **对数底数**：\(\ln\) 与 \(\log_{10}\) 均可，但必须全流程一致（模型、预测、图、表）。
- **单位一致性**：确保同一分析集中各访视使用同一单位（mIU/mL、IU/mL 等），避免混用导致截距不可解释。

### BLQ/缺失值（常见审评关注点）

优先在 SAP/CSR 明确一种主策略并给出敏感性分析：

- **主策略（常用）**：
  - BLQ 按 LLOQ/2 或 LLOQ/\(\sqrt{2}\) 代入（对数变换前）
  - 缺失按 MAR 假设在 MixedLM 中自然处理（但要描述缺失机制评估）
- **敏感性分析**：
  - BLQ 作为删失数据建模（如 Tobit/加权似然）或多重插补
  - 用不同 BLQ 代入规则复跑关键推断（交互项、阈值时间）

### MixedLM 模型诊断与稳健性

- **收敛与随机结构**：
  - 默认：随机截距 `1|USUBJID`
  - 若随机斜率不收敛：保留随机截距，并在 CSR 说明原因与替代检验
- **残差检查**：对数尺度残差的 QQ plot/异方差性；必要时考虑：
  - 访视水平残差方差结构（statsmodels MixedLM 支持有限；可用稳健 SE 作为替代说明）
  - 或采用 GEE/分层自助法作为敏感性分析

### 预测与置信区间（建议在 CSR 写清）

- **个体水平模型（推荐）**：
  - 生成目标 `t_post` 序列的边际均值预测（固定效应层面）并给出 95% CI
  - 回变换：\( \widehat{GMC} = \exp(\widehat{\ln GMC}) \)
  - 如需校正对数正态偏差，可报告 smearing estimate（可选，需一致性说明）
- **仅汇总数据（探索性）**：
  - OLS 在 \(\ln(GMC)\) vs \(\ln(t)\) 上拟合
  - CI 仅反映汇总点拟合不确定性，不等价于个体推断，CSR 中需降级表述

### 保护阈值时间（Threshold time）

若 \( GMC(t)=A\cdot t^{-b} \)，阈值 \(T\) 对应时间：
\[
t_T = \left(\frac{A}{T}\right)^{1/b}
\]

- **推荐不确定性**：
  - 使用参数协方差的 Delta method（快速、可审计）
  - 或参数自助法（从 \((\ln A, b)\) 的近似正态抽样）给出区间

## 与脚本的字段约定

### 汇总数据脚本（`fit_powerlaw_summary.py`）

输入 CSV 至少包含：

- `Group`：如 A2/C1
- `t_post`：正数，且基准点为 1
- `GMC`：正数
- 可选 `StudyMonth`：用于图轴展示（否则自动 `t_post + offset`）

### 个体水平 MixedLM 脚本（`fit_mixedlm_subject.py`）

输入 CSV 至少包含：

- `USUBJID`
- `Group`
- `t_post`
- `TITER`（或通过参数指定字段名）

脚本会派生：

- `ln_t = log(t_post)`
- `ln_titer = log(TITER)`

### 个体数据端到端管线（`run_antibody_kinetics_pipeline.py`）

该管线在个体数据上执行：

1. 派生 `ln_t`、`ln_titer`（支持对数底数 `e` 或 `10`）
2. 拟合模型：`ln_titer ~ ln_t * C(Group) + covars`（默认仅含组别交互）
3. 输出固定效应边际均值预测与置信区间（外推到指定 `--target-t-post`）
4. 保护阈值持续时间反解：给定 `threshold`，用参数协方差进行 Delta method 置信区间

输入 CSV 最少包含：

- `USUBJID`
- `Group`
- `t_post`（要求正数；基准点建议 `t_post=1`）
- `TITER`（要求正数；用于对数变换）

可选：

- `covars`：以 `--covars Age,BaselineIgG` 指定数值列名；预测时协变量取样使用均值（当前默认 `--covar-strategy mean`）。

关键时间点输出：

- 默认会输出 `key_timepoint_predictions.csv`，包含每组在 `--key-t-post`（默认 `18,30`；对应 M24/M36 的对齐时间尺度）的预测均值与 95% CI。
