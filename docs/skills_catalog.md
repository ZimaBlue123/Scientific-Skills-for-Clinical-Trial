## Skills 清单与常用 prompt 模板

本文件提供"做什么用"的速览与可复制的常用 prompt 模板；更细的参数/脚本入口请以各 skill 目录下的 `SKILL.md` 为准。

## Skills 清单（项目内置 - 28 个）

### 核心数据分析

| Skill | 主要用途 | 许可证 | 关键脚本入口 |
|-------|----------|--------|--------------|
| `exploratory-data-analysis` | 科研数据 EDA（200+ 格式，自动生成 markdown 报告） | MIT | `scripts/eda_analyzer.py` |
| `statistical-analysis` | 检验选择/假设检查/效应量与功效/APA 报告 | MIT | `scripts/assumption_checks.py` |
| `scikit-learn` | 经典 ML：分类/回归/聚类/管线/评估 | BSD-3-Clause | `scripts/classification_pipeline.py`, `scripts/clustering_analysis.py` |
| `scikit-survival` | 生存分析：Cox/RSF/GBS/SVM、C-index/Brier 等 | GPL-3.0 | 见 SKILL.md |
| `shap` | 可解释性：SHAP values 与常见图 | MIT | 见 SKILL.md |

### 高性能数据处理

| Skill | 主要用途 | 许可证 | 关键脚本入口 |
|-------|----------|--------|--------------|
| `polars` | 高性能 DataFrame/ETL | MIT | 见 references/ |
| `dask` | 大数据/超内存表格数据处理 | BSD-3-Clause | 见 references/ |
| `vaex` | 十亿行级数据处理（内存映射） | MIT | 见 references/ |

### 医学数据库检索

| Skill | 主要用途 | 许可证 | 关键脚本入口 |
|-------|----------|--------|--------------|
| `clinicaltrials-database` | ClinicalTrials.gov API v2：按条件/药物/地区/状态检索与导出 | Public | `scripts/query_clinicaltrials.py` |
| `pubmed-database` | PubMed（E-utilities）：高级检索、批量抓取、系统综述检索策略 | Public | 见 references/ |
| `openalex-database` | OpenAlex：文献检索/引用分析/趋势与计量学 | CC0 | `scripts/openalex_client.py`, `scripts/query_helpers.py` |
| `database-lookup` | 数据库聚合入口：自动路由到 ClinicalTrials/PubMed/OpenAlex/FDA/ClinVar/ClinPGx/COSMIC | MIT | 见 `skills/database-lookup/SKILL.md` |
| `paper-lookup` | 文献聚合入口：自动路由到 PubMed/OpenAlex，按需补充试验信息 | MIT | 见 `skills/paper-lookup/SKILL.md` |
| `fda-database` | openFDA：药品/器械/召回/不良事件等 | Public | `scripts/fda_query.py`, `scripts/fda_examples.py` |
| `clinvar-database` | ClinVar：变异致病性/星级/批量下载与注释 | Public | 见 references/ |
| `clinpgx-database` | ClinPGx：基因-药物相互作用、CPIC 指南等 | Public | `scripts/query_clinpgx.py` |
| `cosmic-database` | COSMIC：癌症体细胞突变/基因普查/融合/签名（需账号） | 需注册 | `scripts/download_cosmic.py` |

### 临床文档与报告

| Skill | 主要用途 | 许可证 | 关键脚本入口 |
|-------|----------|--------|--------------|
| `clinical-reports` | 病例报告/诊断报告/SAE/CSR（合规校验与模板） | MIT | `scripts/validate_case_report.py`, `scripts/validate_trial_report.py`, `scripts/check_deidentification.py` |
| `clinical-decision-support` | 队列分层/疗效结局比较/循证治疗推荐（LaTeX/PDF） | MIT | `scripts/create_cohort_tables.py`, `scripts/generate_survival_analysis.py` |
| `treatment-plans` | 个体化治疗计划（强调简洁可执行，LaTeX/PDF） | MIT | `scripts/generate_template.py`, `scripts/check_completeness.py` |

### 工具类

| Skill | 主要用途 | 许可证 | 关键脚本入口 |
|-------|----------|--------|--------------|
| `markitdown` | 文件转 Markdown（PDF/DOCX/PPTX/XLSX/图片/音频等） | MIT | `scripts/batch_convert.py`, `scripts/convert_literature.py` |
| `perplexity-search` | AI 实时网络搜索（需 OpenRouter API Key） | MIT | `scripts/perplexity_search.py`, `scripts/setup_env.py` |
| `github-proxy-push` | GitHub 代理推送 | MIT | 见 SKILL.md |
| `pyhealth` | 医疗 AI：EHR 任务/数据集/模型 | MIT | 见 references/ |
| `csr-stage-docx-workflow` | CSR 阶段性小结 Word 生成（Shell结构+PDF自动填数） | MIT | `scripts/generate_csr_docx.py` |
| `word-audit-report-format` | Word 审核报告字体规范（中文宋体/英文TNR） | MIT | `scripts/generate_audit_report_docx.py` |

### 图表扩展（项目内置）

| Skill | 主要用途 | 来源 | 安装位置 |
|-------|----------|------|----------|
| `fireworks-tech-graph` | 自然语言生成技术图（架构图/流程图/序列图/UML），导出 SVG+PNG | [yizhiyanhua-ai/fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) | `skills/fireworks-tech-graph` |

更新（Windows/PowerShell）：

```powershell
git -c http.proxy= -c https.proxy= -C ".\skills\fireworks-tech-graph" pull
```

---

## 常用 prompt 模板（可直接复制）

> 约定：把 `<>` 替换成你的真实信息；如涉及患者/受试者数据，请先去标识化并遵循合规要求。

### 数据分析类

- **exploratory-data-analysis**
  ```
  请对文件 <path/to/data> 做 EDA：识别格式、字段/维度、缺失/异常、质量问题，并输出 markdown 报告与下一步建议。
  ```

- **statistical-analysis**
  ```
  我有数据集 <path/to.csv>，主要结局=<Y>，分组=<group>；请帮我选择合适检验、做假设检查，并按 APA 风格输出结果与效应量。
  ```

- **scikit-learn**
  ```
  用 <path/to.csv> 做 <二分类/回归>：建立可复现 pipeline（预处理+模型+CV），输出指标、混淆矩阵/ROC，并导出可复用训练代码。
  ```

- **scikit-survival**
  ```
  对 <path/to.csv> 做生存分析：time=<time_col>, event=<event_col>；比较 Cox/RSF/GBS，报告 Uno C-index、IBS，并给出风险分层。
  ```

- **shap**
  ```
  请对我训练好的模型（特征表 <X>，模型输出=<概率/风险分数>）做 SHAP 解释：beeswarm+bar+3 个个体 waterfall，并指出可能的数据泄漏特征。
  ```

### 数据库检索类

- **clinicaltrials-database**
  ```
  在 ClinicalTrials.gov 检索：condition=<疾病>，intervention=<药物/疗法>，status=RECRUITING，地区=<国家/州>；输出前 20 条对比表并总结入排标准。
  ```

- **database-lookup**
  ```
  我不确定该查哪个数据库：请以 <疾病/药物/基因/监管问题> 为目标，自动选择最合适的数据库并给出可复核结果摘要。
  ```

- **pubmed-database**
  ```
  请为 <PICO 问题> 构建 PubMed 检索式（含 MeSH/同义词/限制条件），并给出可直接用于 E-utilities 的查询字符串。
  ```

- **paper-lookup**
  ```
  请围绕主题 <topic> 做文献聚合检索（近 <N> 年）：先给 PubMed 核心证据，再用 OpenAlex 补充引用趋势与关键作者/机构。
  ```

- **openalex-database**
  ```
  用 OpenAlex 检索主题 <topic>（>=2021），按 cited_by_count 排序，输出 Top 20 论文清单、研究趋势（年份计数）与关键机构/作者。
  ```

- **fda-database**
  ```
  用 openFDA 分析 <drug/device>：近 5 年不良事件 Top 10 反应、严重事件比例、相关召回，并输出可复现的查询参数与注意事项。
  ```

- **clinvar-database**
  ```
  对变异 <chr:pos ref> 或 <rsID/转录本变异> 查询 ClinVar：返回 CLNSIG、review status（星级）、冲突解释，并给出临床解读注意点。
  ```

- **clinpgx-database**
  ```
  患者基因型：<gene>=<diplotype>，用 ClinPGx/CPIC 给出对药物 <drug> 的用药建议、证据等级与替代方案，并提示 DDI/phenoconversion。
  ```

- **cosmic-database**
  ```
  用 COSMIC 获取基因 <gene> 在 <cancer type> 的常见体细胞突变与频率，并说明是否为 CGC 基因；若需下载请给出脚本与认证步骤。
  ```

### 临床文档类

- **clinical-reports**
  ```
  基于以下资料生成 <CARE 病例报告/SAE/CSR>：<粘贴要点或表格>；请先做 HIPAA 去标识化检查，并用脚本校验完整性。
  ```

- **clinical-decision-support**
  ```
  对队列 <n> 例按生物标志物 <biomarker> 分层，比较 OS/PFS/ORR（含 HR、95%CI、KM 曲线/森林图），生成 LaTeX/PDF 的 CDS 报告与执行摘要。
  ```

- **treatment-plans**
  ```
  为患者（去标识化）<基本信息+诊断+合并症> 生成 1 页或 3-4 页治疗计划：SMART 目标+干预+监测+时间线，并输出 LaTeX/PDF。
  ```

### 工具类

- **markitdown**
  ```
  将 <path/to/document.pdf> 转换为 Markdown 格式，保留表格结构和格式。
  ```

- **perplexity-search**
  ```
  搜索 <topic> 的最新研究进展（2024年以来），要求有来源引用，输出结构化摘要。
  ```

---

## Smoke Prompts（端到端自检模板）

### 1) 数据库聚合路由

```text
请用 database-lookup 检索：condition=NSCLC，intervention=PD-1/PD-L1，status=RECRUITING，region=United States。
输出：采用了哪些原子 skills、关键检索参数、Top 10 结果摘要。
```

预期：
- 主路由到 `clinicaltrials-database`
- 返回结构化 trial 摘要

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

---

## 完整工作流示例

### 临床数据分析流程

```text
1. 请先对 <path/to/data.csv> 做 exploratory-data-analysis：识别字段、缺失、异常和质量问题；
2. 然后用 statistical-analysis 给出适当检验与 APA 风格报告；
3. 接着用 scikit-learn 做一个可复现的 baseline（含 CV 与指标）；
4. 最后用 shap 输出全局与 3 个个体层面的解释，并提示可能的数据泄漏特征。
```

### 生存分析流程

```text
1. 用 exploratory-data-analysis 检查生存数据质量（time/event 列、删失比例）；
2. 用 scikit-survival 比较 Cox/RSF/GBS 模型，报告 Uno C-index 和 IBS；
3. 用 shap 解释生存模型的特征重要性；
4. 用 clinical-decision-support 生成风险分层报告。
```

### 文献检索流程

```text
1. 用 pubmed-database 构建系统综述检索策略；
2. 用 openalex-database 补充引用分析和研究趋势；
3. 用 clinicaltrials-database 查找相关临床试验；
4. 用 perplexity-search 获取最新进展（超出数据库更新范围）。
```
