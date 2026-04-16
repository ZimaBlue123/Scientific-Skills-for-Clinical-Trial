## 触发示例（用户怎么问就该启用本 Skill）

**示例 1：组间 M12+ 持久性比较（监管推断）**

用户：  
“请用幂律模型比较 A2 vs C1 在 M12 以后的抗体衰减斜率，并外推到 M36/M60，给出 95% CI 和阈值 10 的持续时间。”

期望输出（要点）：  
- 明确 `t_post` 如何对齐（末免后/达峰后）  
- MixedLM：`ln_titer ~ ln_t * Group + covariates + (1|USUBJID)`  
- 重点报告交互项 `ln_t:Group` 的估计、SE、CI、P 值  
- 预测曲线与 CI 带（对数 Y 轴）  
- 反解阈值时间及区间（Delta/Bootstrap）  

**示例 2：只有汇总 GMC 表**

用户：  
“我只有 A2/C1 在 M7/M8/M12 的 GMC，能不能外推到 M36 并画图？”

期望输出（要点）：  
- 明确这是探索性（不替代个体推断）  
- OLS on log-log：对每组拟合 `ln(GMC) ~ const + ln(t_post)`  
- 输出方程 \(GMC(t)=A\cdot t^{-b}\) 的 \(A,b\) 与拟合诊断  
- 图：观测点 + 拟合线 + 95% CI 带  

**示例 3：时间标尺错位纠正**

用户：  
“A2 末免在 M1，C1 末免在 M6，直接用研究月比较可以吗？”

期望输出（要点）：  
- 明确不建议；必须构建 `t_post` 对齐  
- 给出一套可复核的映射规则与理由（避免不同衰减阶段混比）  

## 运行脚本示例

### 汇总数据（幂律外推）

输入 `summary.csv`（最少列：`Group,t_post,GMC`），运行：

```bash
python skills/antibody-kinetics/scripts/fit_powerlaw_summary.py --in summary.csv --outdir out --target-t-post 30 --threshold 10
```

### 个体水平（MixedLM 模板）

输入 `subject.csv`（最少列：`USUBJID,Group,t_post,TITER`），运行：

```bash
python skills/antibody-kinetics/scripts/fit_mixedlm_subject.py --in subject.csv --outdir out --titer-col TITER --threshold 10
```

### 个体数据（推荐：端到端管线）

输入 `subject.csv`（建议放在 `data/`，不要提交到 Git），至少包含：
- `USUBJID`：受试者ID
- `Group`：A2/C1 或其它两臂/多臂标记
- `t_post`：末免/达峰后月数（基准点 `t_post=1`）
- `TITER`：抗体滴度/浓度（如 anti-HBs GMC 或 IgG，需全为正数）

可选：
- `covars`：用于控制协变量（仅数值型），例如 `Age,BaselineIgG`

运行：

```bash
python skills/antibody-kinetics/scripts/run_antibody_kinetics_pipeline.py --infile data/subject.csv --outdir output/antibody-kinetics --threshold 10 --key-t-post 18,30
```
