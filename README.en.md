# Scientific-Skills-for-Clinical_Trial

[中文](README.md) | English

AI-assisted toolkit for clinical trials and clinical research (core content: `skills/`).

## Project Scope

This repository maintains AI skills focused on clinical research and clinical trial workflows, including trial retrieval, evidence-based clinical decision support, clinical reporting and compliance documentation, statistics and modeling, survival analysis, explainability, and biomedical/scientific database access.

## Quick Start

### Requirements

- **Python**: 3.10+ (CI currently uses 3.10)
- **AI clients**: Cursor / Claude Code / Codex (with skill support)
- **Diagram rendering (`fireworks-tech-graph`)**: `librsvg` (provides `rsvg-convert`)

Install `rsvg-convert`:

```bash
# macOS
brew install librsvg

# Ubuntu / Debian
sudo apt install librsvg2-bin
```

### Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

### Privacy and Compliance (Strongly Recommended)

- Do not commit raw subject-level data (including patient-level exports) to Git. Put input CSV files in `data/` (ignored by `.gitignore`) and outputs in `output/` (also ignored).
- Antibody kinetics scripts produce aggregated/model-derived outputs (parameters, predicted means/CIs, threshold times), but you should still avoid uploading these artifacts to untrusted environments.

### Development and Quality (Optional)

Install dev dependencies (tests/lint):

```bash
python -m pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run lint:

```bash
flake8
```

Clean local ignored files (use with caution):

```bash
git clean -fdX
```

### Install Skills to Client

If your client supports directly referencing a project path, point it to this repository's `skills/` folder. Otherwise, copy skills into the global skill directory.

Windows (PowerShell):

```powershell
$dst = Join-Path $env:USERPROFILE ".cursor\skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force ".\skills\*" $dst
```

macOS/Linux (bash):

```bash
mkdir -p ~/.cursor/skills
cp -r ./skills/* ~/.cursor/skills/
```

## Repository Layout

```text
Scientific-Skills-for-Clinical_Trial/
├── skills/                # One directory per skill (core content, 28 total)
├── docs/                  # Long-form docs (see index below)
├── scripts/               # Repository-level executable scripts
├── tests/                 # Tests
├── requirements.txt
├── requirements-dev.txt
└── CONTRIBUTING.md
```

For maintenance conventions and details, see `docs/repo_layout.md`.

---

## Skills List and Usage

This repository currently includes **28 skills**, grouped as follows.

### Core Data Analysis Skills

| Skill | Purpose | Quick Usage |
|-------|---------|-------------|
| `exploratory-data-analysis` | EDA for 200+ scientific formats | `python skills/exploratory-data-analysis/scripts/eda_analyzer.py <file>` |
| `statistical-analysis` | hypothesis tests, effect sizes, APA reporting | `from scripts.assumption_checks import comprehensive_assumption_check` |
| `antibody-kinetics` | antibody kinetics and durability modeling (power-law + MixedLM) | `python skills/antibody-kinetics/scripts/run_antibody_kinetics_pipeline.py --infile data/subject.csv --outdir output/antibody-kinetics --threshold 10` |
| `scikit-learn` | classic ML pipelines | `python skills/scikit-learn/scripts/classification_pipeline.py` |
| `scikit-survival` | survival modeling (Cox/RSF/GBS) | see examples in `SKILL.md` |
| `shap` | model explainability | `shap.TreeExplainer(model)(X_test)` |

### High-Performance Data Processing Skills

| Skill | Purpose | Quick Usage |
|-------|---------|-------------|
| `polars` | high-performance DataFrame/ETL | see `references/core_concepts.md` |
| `dask` | large/out-of-memory processing | see `references/dataframes.md` |
| `vaex` | billion-row tabular processing | see `references/core_dataframes.md` |

### Biomedical Database Skills

| Skill | Purpose | Quick Usage |
|-------|---------|-------------|
| `clinicaltrials-database` | ClinicalTrials.gov API v2 | `python skills/clinicaltrials-database/scripts/query_clinicaltrials.py` |
| `pubmed-database` | PubMed E-utilities queries | see `references/api_reference.md` |
| `openalex-database` | OpenAlex literature search | `python skills/openalex-database/scripts/openalex_client.py` |
| `database-lookup` | Aggregated database entrypoint (routes to ClinicalTrials/PubMed/OpenAlex/FDA/ClinVar/ClinPGx/COSMIC) | see `skills/database-lookup/SKILL.md` |
| `paper-lookup` | Aggregated literature entrypoint (routes to PubMed/OpenAlex; trial lookup on demand) | see `skills/paper-lookup/SKILL.md` |
| `fda-database` | openFDA drugs/devices/recalls | `python skills/fda-database/scripts/fda_query.py` |
| `clinvar-database` | ClinVar pathogenicity interpretation | see `references/api_reference.md` |
| `clinpgx-database` | ClinPGx gene-drug interactions | `python skills/clinpgx-database/scripts/query_clinpgx.py` |
| `cosmic-database` | COSMIC somatic mutations | `python skills/cosmic-database/scripts/download_cosmic.py` |

### Clinical Documentation and Reporting Skills

| Skill | Purpose | Quick Usage |
|-------|---------|-------------|
| `clinical-reports` | case reports/CSR/SAE (CARE/ICH-E3) | `python skills/clinical-reports/scripts/validate_case_report.py` |
| `clinical-decision-support` | biomarker-stratified evidence recommendations | `python skills/clinical-decision-support/scripts/create_cohort_tables.py` |
| `treatment-plans` | individualized treatment plan generation | `python skills/treatment-plans/scripts/generate_template.py` |

### Utility Skills

| Skill | Purpose | Quick Usage |
|-------|---------|-------------|
| `markitdown` | convert files to Markdown | `markitdown document.pdf -o output.md` |
| `perplexity-search` | AI-powered real-time web search | `python skills/perplexity-search/scripts/perplexity_search.py "query"` |
| `github-proxy-push` | GitHub proxy diagnosis/push | see `SKILL.md` |
| `pyhealth` | healthcare AI modeling toolkit | see `references/datasets.md` |
| `csr-stage-docx-workflow` | CSR stage summary generation (Word) | `python scripts/generate_csr_docx.py` |
| `word-audit-report-format` | Word audit report formatting | `python scripts/generate_audit_report_docx.py` |

### Diagram Skill (Project-Integrated)

| Skill | Purpose | Location | Quick Usage |
|-------|---------|----------|-------------|
| `fireworks-tech-graph` | generate architecture/flow/UML diagrams from natural language; export SVG+PNG | `skills/fireworks-tech-graph` | Example prompt: `Draw a RAG architecture diagram in style 2 and output to ./output/` |

Notes:
- Source: [yizhiyanhua-ai/fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph)
- This skill is now managed in-repo under `skills/`.
- Update command (Windows/PowerShell):

```powershell
git -c http.proxy= -c https.proxy= -C ".\skills\fireworks-tech-graph" pull
```

---

## Skill Usage Examples

### 1) `exploratory-data-analysis`

```bash
python skills/exploratory-data-analysis/scripts/eda_analyzer.py data.csv output_report.md
```

Prompt template:

```text
Run EDA on <path/to/data>: identify format, columns/dimensions, missingness/outliers, quality risks, and output a markdown report with next-step recommendations.
```

### 2) `statistical-analysis`

```python
from scripts.assumption_checks import comprehensive_assumption_check

results = comprehensive_assumption_check(
    data=df,
    value_col="score",
    group_col="group",
    alpha=0.05
)
```

Prompt template:

```text
Given dataset <path/to.csv> with outcome=<Y> and group=<group>, choose the appropriate test, run assumption checks, and provide APA-style results with effect sizes.
```

### 3) `scikit-survival`

```python
from sksurv.util import Surv
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_ipcw
```

Prompt template:

```text
Perform survival analysis on <path/to.csv> with time=<time_col> and event=<event_col>; compare Cox/RSF/GBS and report Uno C-index, IBS, and risk stratification.
```

### 4) `clinicaltrials-database`

```python
import requests
url = "https://clinicaltrials.gov/api/v2/studies"
```

Prompt template:

```text
Search ClinicalTrials.gov with condition=<disease>, intervention=<drug/therapy>, status=RECRUITING, region=<country/state>; output top 20 in a comparison table and summarize inclusion/exclusion criteria.
```

### 5) `shap`

```python
import shap
explainer = shap.TreeExplainer(model)
```

Prompt template:

```text
Generate SHAP explanations for my trained model (beeswarm + bar + 3 individual waterfall plots) and flag potential leakage features.
```

### 6) `perplexity-search`

```bash
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
python skills/perplexity-search/scripts/perplexity_search.py "What are the latest CAR-T therapy clinical trials in 2024?"
```

### 7) `markitdown`

```bash
markitdown document.pdf -o output.md
```

---

## Recommended Workflow

```text
1) exploratory-data-analysis -> data quality screening
2) statistical-analysis -> inferential tests + APA report
3) scikit-learn or scikit-survival -> baseline modeling
4) shap -> model interpretation
```

To supplement evidence/trial intelligence, run `clinicaltrials-database` with `pubmed-database` and/or `openalex-database`.

---

## Common Entrypoints

- Skills guide (recommended workflow): `docs/skills_guide.md`
- Skills catalog and prompt templates: `docs/skills_catalog.md`
- Contributing guide: `CONTRIBUTING.md`

## Documentation Index (`docs/`)

- `docs/skills_guide.md`: workflow guidance for users
- `docs/skills_catalog.md`: skill index and prompt templates
- `docs/repo_layout.md`: repository layout and maintenance conventions

## Skill-Level Entry Points

- Usage instructions: check each skill's `SKILL.md`
- References: `references/INDEX.md` where available
- Supplemental docs: some skills provide additional README files (quick links below)
- Project memory rule: `.cursor/rules/skills-location-policy.mdc` enforces in-repo `skills/` placement for new skills

### Supplemental Skill README Links

- `skills/fireworks-tech-graph/README.zh.md` (Chinese)
- `skills/fireworks-tech-graph/README.md` (English)
- `skills/fireworks-tech-graph/scripts/README.md` (script details)

---

## Common Scripts

### Review Pipeline (materials -> Markdown -> Word)

1) Convert DOCX/XLSX/PDF to Markdown:

```bash
python scripts/convert_review_materials.py --root "."
```

Output: `review_materials/_converted_md/`

2) Convert Markdown audit report to Word:

```bash
python scripts/md_to_docx.py "review_materials/<your-report>.md" -o "review_materials/<your-report>.docx"
```

3) Generate CSR stage summary (Word):

```bash
python scripts/generate_csr_docx.py --root "project-root"
```

Note: `review_materials/` is ignored by `.gitignore` and not uploaded to GitHub.

---

## Source and Attribution (Compliance)

- **Upstream**: This repository is derived from [`K-Dense-AI/claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills.git), scoped for clinical trial/clinical research usage.
- **Additional source**: `skills/fireworks-tech-graph` comes from [`yizhiyanhua-ai/fireworks-tech-graph`](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) (MIT License).
- **License**: Both upstream and this repository are MIT-licensed; redistribution retains upstream and third-party notices.
- **Change scope**: non-clinical skills/docs removed; clinically relevant skills reorganized; repository conventions, dependencies, and CI supplemented.
- **No endorsement**: this is a community-maintained curated/trimmed distribution and does not imply official endorsement by upstream authors/organizations.

## License

This project is licensed under MIT. See `LICENSE.md`.

Note: some skills may include separate licenses or additional restrictions tied to external data sources/SDKs. Review each skill's `SKILL.md` before use.
