## Skills 导览（面向使用者）

本仓库提供一组面向**临床研究 / 临床试验**的 skills，集中放在仓库根目录 `skills/` 下。

## 最小可用技能集（MVS）

目标：用最少技能覆盖临床数据分析、建模、生存分析、可解释性，以及试验/证据检索的常见闭环。

| # | 分组 | Skill | 用途 |
|---|---|---|---|
| 1 | 核心必备 | `exploratory-data-analysis` | 自动化 EDA 与数据质量巡检 |
| 2 | 核心必备 | `statistical-analysis` | 假设检验、统计推断与结果报告 |
| 3 | 核心必备 | `scikit-learn` | 临床表格数据建模与特征工程 |
| 4 | 核心必备 | `scikit-survival` | 生存分析（Cox/RSF、time-to-event） |
| 5 | 核心必备 | `shap` | 模型可解释性（全局/个体解释） |
| 6 | 增强能力 | `polars` | 高性能 DataFrame/ETL（中等规模数据提速） |
| 7 | 增强能力 | `dask` / `vaex` | 大数据/超内存表格数据处理（按场景择一） |
| 8 | 增强能力 | `clinicaltrials-database` | ClinicalTrials.gov 检索与导出 |
| 9 | 增强能力 | `pubmed-database` / `openalex-database` | 文献检索与证据补全（数据库/API） |
| 10 | 增强能力 | `database-lookup` / `paper-lookup` | 聚合入口：自动路由到最合适数据库/文献渠道 |
| 11 | 可选 | `clinical-reports` / `treatment-plans` | 临床报告与结构化治疗计划输出 |

## 推荐工作流（从数据到证据）

1) `exploratory-data-analysis` → 2) `statistical-analysis` → 3) `scikit-learn`（或 `scikit-survival`）→ 4) `shap`  
需要补证据/试验信息时：
- 优先 `database-lookup` / `paper-lookup` 作为统一入口
- 需要精细控制时再直接调用 `clinicaltrials-database`、`pubmed-database`、`openalex-database`

## 快速 prompt 模板

```text
请先对 <path/to/data.csv> 做 exploratory-data-analysis：识别字段、缺失、异常和质量问题；
然后用 statistical-analysis 给出适当检验与 APA 风格报告；
接着用 scikit-learn 做一个可复现的 baseline（含 CV 与指标）；
最后用 shap 输出全局与 3 个个体层面的解释，并提示可能的数据泄漏特征。
```

## Smoke Prompts（端到端自检模板）

### 1) 数据库聚合路由

```text
请用 database-lookup 检索：condition=NSCLC，intervention=PD-1/PD-L1，status=RECRUITING，region=United States。
输出：采用了哪些原子 skills、关键检索参数、Top 10 结果摘要。
```

预期：
- 主路由到 `clinicaltrials-database`
- 能返回结构化 trial 摘要

### 2) 文献聚合路由

```text
请用 paper-lookup 检索：topic=RSV vaccine efficacy，time_range=2022-2026。
输出：PubMed 核心证据 + OpenAlex 引用趋势（年份计数）。
```

预期：
- 路由到 `pubmed-database` + `openalex-database`
- 同时给出题名列表与趋势摘要

### 3) 文献+试验联合

```text
请用 paper-lookup 回答：CAR-T 在自身免疫病中的最新证据，并补充当前在研试验（RECRUITING）。
输出：证据摘要、试验摘要、下一步检索建议。
```

预期：
- 先文献路由，再追加 `clinicaltrials-database`
- 输出可复核且可复现的参数

