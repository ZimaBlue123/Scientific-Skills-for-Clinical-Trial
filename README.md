# Scientific-Skills-for-Clinical_Trial

中文 | [English](README.en.md)

临床试验 / 临床研究 AI 辅助系统（仓库核心内容：`skills/`）。

## 项目定位

本仓库维护一组面向临床研究与临床试验的 AI skills/技能，覆盖临床试验检索、循证/决策支持、临床报告与合规文档、统计与建模、生存分析、可解释性，以及常用医学/科研数据库访问等工作流。

## 快速开始

### 环境要求

- **Python**：3.10+（CI 当前使用 3.10）
- **AI 客户端**：Cursor / Claude Code / Codex（需要支持 skills 机制）
- **图表渲染（`fireworks-tech-graph`）**：`librsvg`（提供 `rsvg-convert` 命令）

`rsvg-convert` 安装示例：

```bash
# macOS
brew install librsvg

# Ubuntu / Debian
sudo apt install librsvg2-bin
```

### 安装（Python 依赖）

```bash
python -m pip install -r requirements.txt
```

### 隐私与合规（强烈建议）

- 不要把原始个体数据（含受试者层面字段、明细导出）提交到 Git。请把输入 CSV 放在 `data/`（已在 `.gitignore` 中忽略），并把输出放到 `output/`（同样会被忽略）。
- 抗体动力学分析脚本会输出“已汇总/已建模”的结果（参数、预测均值/CI、阈值时间），但仍建议不要把输出产物上传到不可信环境。

### 开发与质量（可选）

安装开发依赖（测试/Lint）：

```bash
python -m pip install -r requirements-dev.txt
```

运行测试：

```bash
pytest
```

运行代码风格检查：

```bash
flake8
```

清理本地缓存/忽略文件（谨慎使用，会删除所有被 `.gitignore` 忽略的内容）：

```bash
git clean -fdX
```

### 安装（skills 到客户端）

如果你的客户端支持"直接引用项目目录"，推荐直接指向本仓库的 `skills/`；否则可复制到客户端的全局 skills 目录。

Windows（PowerShell）示例：

```powershell
$dst = Join-Path $env:USERPROFILE ".cursor\skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force ".\skills\*" $dst
```

macOS/Linux（bash）示例：

```bash
mkdir -p ~/.cursor/skills
cp -r ./skills/* ~/.cursor/skills/
```

## 仓库结构

```
Scientific-Skills-for-Clinical_Trial/
├── skills/                # 每个 skill 一个目录（核心内容，28 个）
├── docs/                  # 长文档（索引见下方"文档索引"）
├── scripts/               # 仓库级可执行脚本入口（含 CSR/审核报告生成）
├── tests/                 # 测试
├── requirements.txt
├── requirements-dev.txt
└── CONTRIBUTING.md
```

维护约定与更详细解释见 `docs/repo_layout.md`。

---

## Skills 清单与使用方法

本仓库包含 **28 个 skills**，分为以下几类：

### 核心数据分析 Skills

| Skill | 用途 | 快速使用 |
|-------|------|----------|
| `exploratory-data-analysis` | 200+ 格式科研数据 EDA | `python skills/exploratory-data-analysis/scripts/eda_analyzer.py <file>` |
| `statistical-analysis` | 假设检验、效应量、APA 报告 | `from scripts.assumption_checks import comprehensive_assumption_check` |
| `antibody-kinetics` | 抗体动力学/免疫持久性：幂律模型 + MixedLM，支持 M12+ 外推与阈值时间 | `python skills/antibody-kinetics/scripts/run_antibody_kinetics_pipeline.py --infile data/subject.csv --outdir output/antibody-kinetics --threshold 10` |
| `scikit-learn` | 经典 ML 建模与管线 | `python skills/scikit-learn/scripts/classification_pipeline.py` |
| `scikit-survival` | 生存分析（Cox/RSF/GBS） | 见 SKILL.md 中的代码示例 |
| `shap` | 模型可解释性（SHAP values） | `shap.TreeExplainer(model)(X_test)` |

### 高性能数据处理 Skills

| Skill | 用途 | 快速使用 |
|-------|------|----------|
| `polars` | 高性能 DataFrame/ETL | 见 `references/core_concepts.md` |
| `dask` | 大数据/超内存处理 | 见 `references/dataframes.md` |
| `vaex` | 十亿行级数据处理 | 见 `references/core_dataframes.md` |

### 医学数据库检索 Skills

| Skill | 用途 | 快速使用 |
|-------|------|----------|
| `clinicaltrials-database` | ClinicalTrials.gov API v2 | `python skills/clinicaltrials-database/scripts/query_clinicaltrials.py` |
| `pubmed-database` | PubMed E-utilities 检索 | 见 `references/api_reference.md` |
| `openalex-database` | OpenAlex 文献检索 | `python skills/openalex-database/scripts/openalex_client.py` |
| `database-lookup` | 聚合数据库入口（自动路由到 ClinicalTrials/PubMed/OpenAlex/FDA/ClinVar/ClinPGx/COSMIC） | 见 `skills/database-lookup/SKILL.md` |
| `paper-lookup` | 聚合文献入口（自动路由到 PubMed/OpenAlex，按需补充试验检索） | 见 `skills/paper-lookup/SKILL.md` |
| `fda-database` | openFDA 药品/器械/召回 | `python skills/fda-database/scripts/fda_query.py` |
| `clinvar-database` | ClinVar 变异致病性 | 见 `references/api_reference.md` |
| `clinpgx-database` | ClinPGx 基因-药物相互作用 | `python skills/clinpgx-database/scripts/query_clinpgx.py` |
| `cosmic-database` | COSMIC 癌症体细胞突变 | `python skills/cosmic-database/scripts/download_cosmic.py` |

### 临床文档与报告 Skills

| Skill | 用途 | 快速使用 |
|-------|------|----------|
| `clinical-reports` | 病例报告/CSR/SAE（CARE/ICH-E3） | `python skills/clinical-reports/scripts/validate_case_report.py` |
| `clinical-decision-support` | 队列分层/循证推荐（LaTeX/PDF） | `python skills/clinical-decision-support/scripts/create_cohort_tables.py` |
| `treatment-plans` | 个体化治疗计划（LaTeX/PDF） | `python skills/treatment-plans/scripts/generate_template.py` |

### 工具类 Skills

| Skill | 用途 | 快速使用 |
|-------|------|----------|
| `markitdown` | 文件转 Markdown（PDF/DOCX/PPTX等） | `markitdown document.pdf -o output.md` |
| `perplexity-search` | AI 实时网络搜索 | `python skills/perplexity-search/scripts/perplexity_search.py "query"` |
| `github-proxy-push` | GitHub 代理推送 | 见 SKILL.md |
| `pyhealth` | 医疗 AI（EHR 任务/模型） | 见 `references/datasets.md` |
| `csr-stage-docx-workflow` | CSR 阶段性小结 Word 生成 | `python scripts/generate_csr_docx.py` |
| `word-audit-report-format` | Word 审核报告字体规范 | `python scripts/generate_audit_report_docx.py` |

### 图表 Skill（项目内置）

| Skill | 用途 | 安装位置 | 快速使用 |
|-------|------|----------|----------|
| `fireworks-tech-graph` | 通过自然语言生成技术图（架构图/流程图/序列图/UML），导出 SVG+PNG | `skills/fireworks-tech-graph` | Prompt 示例：`画一个 RAG 架构图，style 2，输出到 ./output/` |

说明：
- 该 skill 来源：[`yizhiyanhua-ai/fireworks-tech-graph`](https://github.com/yizhiyanhua-ai/fireworks-tech-graph)。
- `fireworks-tech-graph` 已并入本项目 `skills/` 目录统一管理。
- 更新该 skill（Windows/PowerShell）：

```powershell
git -c http.proxy= -c https.proxy= -C ".\skills\fireworks-tech-graph" pull
```

---

## Skill 详细使用示例

### 1. exploratory-data-analysis（EDA）

**场景**：对科研数据文件进行自动化探索分析

```bash
# 命令行使用
python skills/exploratory-data-analysis/scripts/eda_analyzer.py data.csv output_report.md

# 支持 200+ 格式：CSV, FASTQ, PDB, HDF5, TIFF, mzML 等
```

**Prompt 模板**：
```
请对文件 <path/to/data> 做 EDA：识别格式、字段/维度、缺失/异常、质量问题，并输出 markdown 报告与下一步建议。
```

### 2. statistical-analysis（统计分析）

**场景**：假设检验、效应量计算、APA 格式报告

```python
from scripts.assumption_checks import comprehensive_assumption_check

# 综合假设检验（含可视化）
results = comprehensive_assumption_check(
    data=df,
    value_col='score',
    group_col='group',
    alpha=0.05
)
```

**Prompt 模板**：
```
我有数据集 <path/to.csv>，主要结局=<Y>，分组=<group>；请帮我选择合适检验、做假设检查，并按 APA 风格输出结果与效应量。
```

### 3. scikit-survival（生存分析）

**场景**：临床试验 time-to-event 分析

```python
from sksurv.util import Surv
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_ipcw

# 创建生存结局
y = Surv.from_dataframe('event', 'time', df)

# 训练模型
rsf = RandomSurvivalForest(n_estimators=100, random_state=42)
rsf.fit(X_train, y_train)

# 评估（Uno's C-index，推荐用于高删失数据）
c_uno = concordance_index_ipcw(y_train, y_test, rsf.predict(X_test))[0]
```

**Prompt 模板**：
```
对 <path/to.csv> 做生存分析：time=<time_col>, event=<event_col>；比较 Cox/RSF/GBS，报告 Uno C-index、IBS，并给出风险分层。
```

### 4. clinicaltrials-database（临床试验检索）

**场景**：检索 ClinicalTrials.gov 招募中的试验

```python
import requests

url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "breast cancer",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 10
}
response = requests.get(url, params=params)
data = response.json()
print(f"Found {data['totalCount']} trials")
```

**Prompt 模板**：
```
在 ClinicalTrials.gov 检索：condition=<疾病>，intervention=<药物/疗法>，status=RECRUITING，地区=<国家/州>；输出前 20 条对比表并总结入排标准。
```

### 5. shap（模型可解释性）

**场景**：解释机器学习模型预测

```python
import shap

# 创建解释器（树模型用 TreeExplainer）
explainer = shap.TreeExplainer(model)
shap_values = explainer(X_test)

# 全局重要性
shap.plots.beeswarm(shap_values)

# 单个预测解释
shap.plots.waterfall(shap_values[0])
```

**Prompt 模板**：
```
请对我训练好的模型做 SHAP 解释：beeswarm+bar+3 个个体 waterfall，并指出可能的数据泄漏特征。
```

### 6. perplexity-search（AI 网络搜索）

**场景**：获取最新科研信息（超出模型知识截止日期）

```bash
# 设置 API Key
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'

# 搜索
python skills/perplexity-search/scripts/perplexity_search.py "What are the latest CAR-T therapy clinical trials in 2024?"

# 使用高级模型
python skills/perplexity-search/scripts/perplexity_search.py "query" --model sonar-pro-search
```

### 7. markitdown（文件转换）

**场景**：将 PDF/DOCX/PPTX 等转为 Markdown

```bash
# 命令行
markitdown document.pdf -o output.md

# Python API
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

---

## 推荐工作流

### 从数据到证据的完整流程

```
1) exploratory-data-analysis → 数据质量巡检
2) statistical-analysis → 假设检验与 APA 报告
3) scikit-learn 或 scikit-survival → 建模
4) shap → 模型解释
```

需要补充证据/试验信息时：并行使用 `clinicaltrials-database` + `pubmed-database`/`openalex-database`。

### 快速 Prompt 模板

```text
请先对 <path/to/data.csv> 做 exploratory-data-analysis：识别字段、缺失、异常和质量问题；
然后用 statistical-analysis 给出适当检验与 APA 风格报告；
接着用 scikit-learn 做一个可复现的 baseline（含 CV 与指标）；
最后用 shap 输出全局与 3 个个体层面的解释，并提示可能的数据泄漏特征。
```

---

## 常用入口

- **Skills 导览（推荐工作流）**：`docs/skills_guide.md`
- **Skills 清单与 prompt 模板**：`docs/skills_catalog.md`
- **贡献指南**：`CONTRIBUTING.md`

## 文档索引（docs/）

- `docs/skills_guide.md`：Skills 导览与推荐工作流（给使用者）
- `docs/skills_catalog.md`：Skills 清单与常用 prompt 模板（给使用者）
- `docs/repo_layout.md`：仓库目录规范与维护约定（给维护者）

## 每个 skill 的说明入口

- **使用说明**：优先看对应目录的 `SKILL.md`
- **参考资料**：统一放在 `references/INDEX.md`（如存在）
- **补充文档（README）**：部分 skill 目录提供额外 README（见下方直达链接）
- **项目规则记忆**：已在 `.cursor/rules/skills-location-policy.mdc` 固化“skill 仅放项目 `skills/` 目录”

### Skills 补充 README 直达链接

- `skills/fireworks-tech-graph/README.zh.md`（中文说明）
- `skills/fireworks-tech-graph/README.md`（英文说明）
- `skills/fireworks-tech-graph/scripts/README.md`（脚本说明）

---

## 常用脚本

### 审核工作流（素材→Markdown→Word）

#### 1) 将 DOCX/XLSX/PDF 转成 Markdown

```bash
python scripts/convert_review_materials.py --root "."
```

输出到：`review_materials/_converted_md/`

#### 2) 将 Markdown 审核报告转成 Word

```bash
python scripts/md_to_docx.py "review_materials/<你的审核报告>.md" -o "review_materials/<你的审核报告>.docx"
```

#### 3) 生成 CSR 阶段性小结（Word）

```bash
python scripts/generate_csr_docx.py --root "项目根目录"
```

提示：`review_materials/` 已在 `.gitignore` 中忽略，不会被上传到 GitHub。

---

## 来源与归属（合规声明）

- **上游项目**：本仓库从 [`K-Dense-AI/claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills.git) 提取并裁剪出更聚焦"临床研究/临床试验"场景的一部分 skills。
- **附加来源**：`skills/fireworks-tech-graph` 来自 [`yizhiyanhua-ai/fireworks-tech-graph`](https://github.com/yizhiyanhua-ai/fireworks-tech-graph)（MIT License）。
- **许可证**：上游与本仓库均为 MIT License；本仓库在再分发时保留上游版权与许可声明（含新增第三方 skill 版权声明）。
- **改动范围（摘要）**：删除与临床研究无关的 skills/文档，仅保留并重组与临床研究相关的 skills；补充本仓库的目录规范、依赖与 CI。
- **非背书声明**：本仓库为社区维护的裁剪/整理版本，不代表上游作者或组织的官方立场、认证或背书。

## 许可证

本项目采用 MIT 许可证，详见 `LICENSE.md`。

注意：各 skill 可能有独立许可证或对外部数据源/SDK 有额外限制，使用前请查看对应 skill 的 `SKILL.md`。
