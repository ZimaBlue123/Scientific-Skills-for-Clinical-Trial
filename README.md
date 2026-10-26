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

运行代码风格检查（推荐使用 ruff）：

```bash
ruff check scripts/ tests/
ruff format --check scripts/ tests/
```

> 项目已从 flake8 迁移至 ruff（配置见 `pyproject.toml`）。`requirements-dev.txt` 仍保留 flake8 以兼容旧 CI。

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

# 仅同步单个 skill（示例）
powershell -File .\scripts\_tools\sync_skills_to_global.ps1 -Skill pptx-gmc-sync-from-word
```

macOS/Linux（bash）示例：

```bash
mkdir -p ~/.cursor/skills
cp -r ./skills/* ~/.cursor/skills/
```

## 仓库结构

```
Scientific-Skills-for-Clinical_Trial/
├── skills/                # 每个 skill 一个目录（核心内容，178 个）
├── docs/                  # 长文档（索引见下方"文档索引"）
├── scripts/               # 仓库级可执行脚本入口
│   ├── SCRIPTS_INDEX.md   # 全局脚本能力与快速复用索引（自动生成）
│   ├── pipeline/          # 模块化数据处理管线（ingest/extract/transform/convert/export/validate/review/literature）
│   ├── _tools/            # 内部审计/索引/自检/维护脚本
│   ├── clinical-automation/ # 外部子项目（只读）
│   └── _archive/          # 精选高价值交付物参考模板（本地参考，不追踪）
├── tests/                 # 测试
├── pyproject.toml         # 项目元数据 + ruff/mypy/pytest 配置
├── requirements.txt
├── requirements-dev.txt
├── SKILLS_INDEX.md        # 全局技能索引（自动生成）
└── CONTRIBUTING.md
```

维护约定与更详细解释见 `docs/repo_layout.md` 及 `scripts/README.md`。

---

## 开发工作流

本仓库在每次重大重构时会跑一组**自检与索引脚本**（位于 `scripts/_tools/`）。这些脚本可独立于 IDE / CI 运行，方便人工排查与快速复用。

```bash
# 快速检索可复用脚本能力（编写新脚本前必跑）
python scripts/_tools/generate_scripts_index.py --search docx
python scripts/_tools/generate_scripts_index.py

# 项目自检（语法 + 代码质量 + 鲁棒性审计）
python scripts/_tools/project_self_check.py
python scripts/_tools/audit_robustness_smells.py

# Skills 注册表校验
python scripts/_tools/validate_skills_registry.py

# Skills 去重报告
python scripts/_tools/skill_dedupe_report.py

# 重新生成 SKILLS_INDEX.md
python scripts/_tools/generate_skills_index.py

# 为核心 Skills 注入 SOP
python scripts/_tools/inject_skill_sop.py --write

# 未使用 Import 扫描
python scripts/_tools/fix_unused_imports.py
```



---

## Skills 清单与使用方法

本仓库包含 **178 个 skills**（已合并上游 scientific-skills 的非重复条目），分为以下几类：

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
| `clinical-immunogenicity-noninferiority` | 疫苗免疫原性非劣效分析（GMC 比值/率差 + 95%CI → 多子表 Excel） | `python skills/clinical-immunogenicity-noninferiority/scripts/compute_noninferiority.py --self-check` |

### 工具类 Skills

| Skill | 用途 | 快速使用 |
|-------|------|----------|
| `markitdown` | 文件转 Markdown（PDF/DOCX/PPTX等） | `markitdown document.pdf -o output.md` |
| `perplexity-search` | AI 实时网络搜索 | `python skills/perplexity-search/scripts/perplexity_search.py "query"` |
| `github-proxy-push` | GitHub 代理推送 | 见 SKILL.md |
| `pyhealth` | 医疗 AI（EHR 任务/模型） | 见 `references/datasets.md` |
| `csr-stage-docx-workflow` | CSR 阶段性小结 Word 生成 | `python scripts/generate_csr_docx.py` |
| `word-audit-report-format` | Word 审核报告字体规范 | `python scripts/generate_audit_report_docx.py` |
| `pptx-gmc-sync-from-word` | Word GMC/例数/P 值同步到 PPT 指定页表格 | `python skills/pptx-gmc-sync-from-word/scripts/sync_pptx_from_word.py --word <docx> --ppt <pptx>` |
| `docx-to-markdown` | DOCX 文本/表格抽取为 Markdown | `python skills/docx-to-markdown/scripts/extract_docx_text.py` |

### 临床数据自动化 Skills（vendored 能力层）

这一组 SKILL.md 是**薄能力层**，脚本本体位于 `scripts/clinical-automation/`
—— 该目录是从 [`ZimaBlue123/Clinical-Data-Automation`](https://github.com/ZimaBlue123/Clinical-Data-Automation)
整体迁入的外部子项目，保留了完整提交历史与原有 `01_` … `34_` 编号结构。

依赖需在该目录内**单独安装**，不要并入仓库根：

```bash
pip install -r scripts/clinical-automation/requirements.txt
```

| Skill | 用途 | 覆盖模块 |
|-------|------|----------|
| `clinical-pdf-ectd` | PDF eCTD 申报合规装甲与审计报告 | 18 |
| `clinical-sae-extraction` | SAE 严重不良事件结构化抽取 | 33 |
| `clinical-word-tables` | Word 表格导出 Excel / pzfx 抗体数据替换 / 图表复刻 | 07、08、09 |
| `clinical-pdf-extraction` | 血清报告、ADR、规则驱动提取与干扰区定位 | 12、13、21 |
| `clinical-docx-editing` | Word 样式清理与 OOXML 批量替换 | 10、11 |
| `clinical-excel-charts` | 临床图表生成与 GMC/GMI/阳转率填表、期刊配色 | 01、02 |
| `clinical-pdf-hygiene` | 标题重命名、去重、XSS 清理、威胁分析 | 15、17、22、23 |
| `clinical-ppt-toolkit` | PPT 合并去重与边角水印去除 | 03、04 |
| `document-format-convert` | PPT/Word/PDF/图片 互转与 PDF 合并 | 05、06、14、16、19、34 |
| `clinical-document-translation` | Excel/CSV/Word/PDF 中英双向翻译 | 24 |

> 编号 25–32 在原仓库中为非临床工具（Py 转 EXE、C 盘清理、WiFi 密码、文件计数、
> 文献下载、代理导出、DNS 泄漏、网速测试），本次迁入时已剔除，故编号不连续。
> 详见 `scripts/clinical-automation/README.md` 文首说明。

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
results = comprehensive_assumption_check(data=df, value_col="score", group_col="group", alpha=0.05)
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
y = Surv.from_dataframe("event", "time", df)

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
params = {"query.cond": "breast cancer", "filter.overallStatus": "RECRUITING", "pageSize": 10}
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

## 常用脚本与快速复用机制

### 脚本能力索引 (`scripts/SCRIPTS_INDEX.md`)

> 完整脚本清单见 [`scripts/SCRIPTS_INDEX.md`](scripts/SCRIPTS_INDEX.md)，支持通过 `python scripts/_tools/generate_scripts_index.py --search <keyword>` 秒级检索：

| 脚本 | 用途 | 状态 |
|------|------|------|
| `scripts/pipeline/convert/convert_to_md.py` | 文档转 Markdown（支持 `--mode numbered` 锚点编号） | ✅ 推荐 |
| `scripts/pipeline/ingest/rtf_reader.py` | SAS / 临床 TFL RTF 文本与二维表格提取 | ✅ 推荐 |
| `scripts/pipeline/extract/extract_docx_tracked_text.py` | 零依赖提取含修订痕迹 (`w:ins`/`w:del`) 的 `.docx` 文本与表格 | ✅ 推荐 |
| `scripts/pipeline/export/docx_builder.py` | DOCX 导出与中英文字体规范（Word/审核报告生成基础模块） | ✅ 推荐 |
| `scripts/pipeline/export/update_docx_toc_fields.py` | 通过 Word COM 自动更新 `.docx` 目录域与页码 | ✅ 推荐 |
| `scripts/pipeline/review/audit_protocol_crossrefs.py` | 核查临床方案 `.docx` 内部章节号与图表交叉引用 | ✅ 推荐 |
| `scripts/pipeline/review/compare_docx_content.py` | 逐包、逐块、逐样式比对两份 `.docx` 文档 | ✅ 推荐 |
| `scripts/pipeline/validate/docx_clean_validator.py` | 校验 `.docx` 清洁版合规性（红蓝字、高亮、批注） | ✅ 推荐 |
| `scripts/pipeline/literature/pubmed_search_tool.py` | PubMed 文献检索 CLI | ✅ 推荐 |
| `scripts/_tools/generate_scripts_index.py` | 生成脚本复用索引与 `--search` 关键词检索 | ✅ 推荐 |
| `scripts/_tools/project_self_check.py` | 项目自检 | ✅ 推荐 |
| `scripts/_tools/cleanup_generated_artifacts.py` | 清理缓存与 IDE 历史记录 | ✅ 推荐 |

> `scripts/` 现行分层：`pipeline/`（核心业务流）· `_tools/`（内部运维/审计/索引工具）·
> `_archive/`（精选交付物参考模板，本地参考不追踪）·
> `clinical-automation/`（外部迁入的只读能力库）。

### 如何选择

```
需要从 docx/pdf/rtf 提取纯文本或带编号 Markdown（##P1, ##T1 标记）？
  → python scripts/pipeline/convert/convert_to_md.py input.docx -o output.md --mode numbered

需要从含修订痕迹（Track Changes）的 docx 提取定稿/原稿文本？
  → python scripts/pipeline/extract/extract_docx_tracked_text.py input.docx -o output.txt --mode final

需要从 SAS 导出的临床 TFL (.rtf) 提取结构化二维表格？
  → python scripts/pipeline/ingest/rtf_reader.py input.rtf --tables -o tables.json

需要核查 Word 清洁版是否残留红蓝字、高亮或批注？
  → python scripts/pipeline/validate/docx_clean_validator.py target.docx
```

### 文档审核工作流（素材 → Markdown → Word）

#### 1) 将 DOCX/XLSX/PDF 转成 Markdown

```bash
# 单文件
python scripts/pipeline/convert/convert_to_md.py input.docx -o output.md

# 批量文件夹（输出到 review_materials/converted/）
python scripts/pipeline/convert/convert_to_md.py --folder review_materials -o review_materials/converted
```

#### 2) 方案交叉引用与数值/文本质量核查

```bash
python scripts/pipeline/review/audit_protocol_crossrefs.py review_materials/protocol.docx
python scripts/pipeline/review/audit_protocol_numeric_consistency.py review_materials/converted/protocol.md
python scripts/pipeline/review/scan_protocol_text_quality.py review_materials/converted/protocol.md
```

提示：`review_materials/` 已在 `.gitignore` 中忽略，不会被上传到 GitHub。

### Word 文档处理技巧

**文件名含中文时**：直接在命令行传递路径可能因编码问题失败，建议先用 PowerShell 复制为简单文件名：

```powershell
# 复制为纯英文文件名
Copy-Item "review_materials\1-3-1说明-20260529-新.docx" target.docx

# 然后用脚本处理
python scripts/pipeline/convert/convert_to_md.py target.docx -o output.md
```

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
