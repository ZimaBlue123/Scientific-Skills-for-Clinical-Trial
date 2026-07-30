# 阶段三：核心配置更新计划

> **状态**：草案（**未执行任何修改**）
> **基线 commit**：`ea424f1`（阶段二）
> **范围**：`.gitignore` / `requirements.txt` / `README.md`

---

## 1. `.gitignore`（237 行）

### 1.1 已覆盖且正确（无需变更）

- ✅ Python 字节码 / 包 / venv（`__pycache__/`、`*.py[cod]`、`venv/` 等）
- ✅ 打包产物（`build/`、`dist/`、`*.whl`、`*.egg`）
- ✅ 测试缓存（`.pytest_cache/`、`.coverage`、`htmlcov/`）
- ✅ IDE（`.idea/`、`.vscode/`、`.cursor/*` 排除但保留 `skills/` 与 `rules/`）
- ✅ 操作系统（`.DS_Store`、`Thumbs.db`、`ehthumbs.db`、`$RECYCLE.BIN/`）
- ✅ Claude / Workbuddy（`.claude/`、`.mavis/`、`.workbuddy/`、`.worktrees/`）
- ✅ 敏感数据（`.env`、`.env.*`、`config.yaml`、`config_local.yaml`）
- ✅ 数据（`data/`、`raw_data/`、`output/`、`downloads/`、`review_materials/`、`secrets/`）
- ✅ 表格式数据（`*.csv`、`*.tsv`、`*.xlsx`、`*.xls`、`*.parquet`）
- ✅ 临时与日志（`*.log`、`*.bak`、`*.tmp`、`*.download`、`~$*`）
- ✅ Office / PDF / 媒体（`*.doc`、`*.docx`、`*.pdf`、`*.png`、…）
- ✅ 报告产物（`reports/**/*.{md,py,json,xlsx,doc,docx}`、`output/**/*.{md,py}`）
- ✅ 工作树与共享模板目录（`scripts/common_templates/`、`scripts/deliverables/`）
- ✅ 反例（re-include `docs/**` 与 `skills/**/assets/**`、`skills/**/references/**`）

### 1.2 提议增量（待用户批准）

#### A. 增补 IDE / OS 遗漏项（**低风险**）

| 模式 | 理由 |
|---|---|
| `.aider*` | Aider AI 编程工具 |
| `.ipynb_checkpoints/` | 已存在（确认覆盖） |
| `.mypy_cache/` | 已存在 |
| `.pytest_cache/` | 已存在 |
| `.ruff_cache/` | 已存在 |

→ **无需新增**（均已覆盖）。

#### B. 增补 IDE 配置（**中风险 - 影响开发体验**）

> `.vscode/`、`.idea/`、`.cursor/*` 已忽略。**不建议放宽**——保持现状即可。

#### C. 增补阶段三新生成文件（**低风险**）

下列由阶段一/二/三新增的文件需要确保被纳入 git：

| 文件 | 状态 |
|---|---|
| `docs/audit_phase1.md` | ✅ 已 commit（`0e5207a`） |
| `docs/cleanup_phase2_plan.md` | ✅ 已 commit（`ea424f1`） |
| `reports/phase1_*.txt` / `*.md` | ⚠️ `.gitignore` L137 `reports/**/*.md` 阻止；但被强制 `-f` add 已 commit |
| `reports/phase2_scan.json` | 同上 |
| `scripts/_tools/_audit_*.py` | ⚠️ `.gitignore` 排除；但被强制 `-f` add 已 commit |
| `scripts/_tools/_dbg_fstr.py` | ✅ 已删除（不在 commit） |

**建议**：在 `.gitignore` 中**保留现有规则**（避免污染），但**文档化**：所有"代码化石/审计工具"用 `git add -f` 显式纳入。

### 1.3 `.gitignore` 结论

**✅ 无需修改**。当前规则覆盖完整且合理。

---

## 2. `requirements.txt`（62 行）

### 2.1 已声明依赖（实际 import 命中率）

| 依赖 | 声明 | 使用文件数 | 评估 |
|---|---|---:|---|
| `python-docx` (docx) | ✅ | 26 | 健康 |
| `pandas` | ✅ | 25 | 健康 |
| `numpy` | ✅ | 33 | 健康 |
| `matplotlib` | ✅ | 19 | 健康（`matplotlib.pyplot` 子模块） |
| `python-pptx` (pptx) | ✅ | 9 | 健康 |
| `Pillow` (PIL) | ✅ | 7 | 健康（声明 `Pillow`，导入用 `PIL`） |
| `openpyxl` | ✅ | 3 | 健康 |
| `pypdf` | ✅ | 5 | 健康 |
| `markitdown` | ✅ | 4 | 健康 |
| `pymupdf` (fitz) | ✅ | **0 直接 import fitz** | ⚠️ 见下 |
| `statsmodels` | ✅ | 3 | 健康 |
| `striprtf` | ✅ | — | 无使用 |
| `pdfplumber` | ✅ | — | 无使用 |
| `olefile` | ✅ | **0** | ⚠️ 未被任何脚本 import |
| `cairosvg` | ✅ | — | ⚠️ 未被 import（脚本可能用 librsvg CLI） |
| `openai` | ✅ | — | 间接使用 |
| `pywin32` (win32com / pythoncom) | ✅ | 4 | 健康（Windows-only） |

**核心 scripts 顶层实际 import 的第三方模块**（按使用频次）：
- `numpy` 33 / `requests` 27 / `docx` 26 / `pandas` 25 / `matplotlib` 19
- `pypdf` 5 / `pptx` 9 / `PIL` 7 / `scipy` 6 / `lxml` 6

### 2.2 未声明但被使用（按使用频次）

| 模块 | 使用数 | 类别 | 建议 |
|---|---:|---|---|
| `requests` | 27 | 第三方 | **必须添加** `requests>=2.31` |
| `scipy` | 6 | 第三方 | **必须添加** `scipy>=1.10` |
| `lxml` | 6 | 第三方 | **必须添加** `lxml>=4.9`（被 python-docx 间接依赖，但显式声明更稳） |
| `defusedxml` | 6 | 第三方 | **建议添加** `defusedxml>=0.7`（安全 XML 解析） |
| `torch` | 9 | skill 专用 | **建议添加** `torch>=2.0` |
| 其他 ~65 个 | 1-6 | skills/ 专用（rdkit/pymoo/...） | **不添加**（每个 skill 自己负责依赖） |

### 2.3 提议增量（待用户批准）

```diff
--- requirements.txt
+++ requirements.txt
@@ +X,Y @@
 # --- Document parsing & generation ---
 python-docx>=1.1.0
 python-pptx>=1.0.0
 pymupdf>=1.24.0
 pypdf>=4.2.0
 pdfplumber>=0.11.0
 striprtf>=0.0.26
 markitdown>=0.1.0

+# --- HTTP client (used by 27 scripts; NCBI E-utilities etc.) ---
+requests>=2.31
+
+# --- Numeric / scientific (used by 6+ scripts) ---
+scipy>=1.10
+lxml>=4.9              # python-docx 间接依赖，显式声明更稳
+defusedxml>=0.7        # safe XML parsing
```

**`requests` 是必须的**（pubmed_lit_search、norovirus_trial_search 等 NCBI E-utilities 调用）。**`scipy`/`lxml`/`defusedxml` 是次优先级**（间接依赖）。

### 2.4 不建议操作

- ❌ **不删除** `pymupdf` / `cv2` / `olefile` / `cairosvg` 等"未直接 import"的依赖——它们可能是：
  - 间接依赖（如 `cv2` 被 `img2table` 调用）
  - 文档/注释引用
  - Windows-only 备用路径
  - 用户环境外部工具的 Python 绑定

---

## 3. `README.md`（488 行）

### 3.1 已对齐（无需变更）

- ✅ 项目定位、Python 3.10+ 要求、`librsvg` 工具说明
- ✅ 安装步骤（pip install -r requirements.txt）
- ✅ 隐私与合规建议
- ✅ 开发与质量（pytest、ruff、flake8 迁移说明）
- ✅ skills 复制/同步到 Cursor 的说明
- ✅ Windows PowerShell 示例

### 3.2 提议增量（可选，待用户批准）

#### A. 新增"项目结构"章节

```markdown
## 项目结构

\`\`\`
2-Scientific-Skills-for-Clinical_Trial/
├── scripts/                  # 本仓库核心脚本
│   ├── common_scripts/       # 公共工具（docx_utils, generator_base）
│   ├── _archive*/            # 历史归档
│   ├── _tools/               # 审计/自检脚本
│   └── *.py                  # 业务脚本（docx 抽取/生成/审计/文献检索）
├── skills/                   # AI 技能（按领域划分，~190 个 skill）
├── docs/                     # 项目文档（审计报告、清理计划、合并分析）
├── reports/                  # 阶段产物（默认被 .gitignore 忽略）
├── tests/                    # 单元测试
├── reviews/, review_materials/  # 输入数据（被 .gitignore 忽略）
└── .claude-plugin/, .cursor/, .github/  # 编辑器 / CI 配置
\`\`\`
```

#### B. 新增"工作流"章节（开发常用命令）

```markdown
## 开发工作流

\`\`\`bash
# 运行所有脚本的烟雾测试
py -3 scripts/_tools/audit_phase1_compile.py

# 代码质量自检（pyflakes）
py -3 -m pyflakes scripts/

# 阶段二：扫描冗余文件
py -3 scripts/_tools/audit_phase2_scan.py

# 阶段三：审计 import 依赖
py -3 scripts/_tools/audit_phase3_imports.py
\`\`\`
```

#### C. 修订 CHANGELOG.md

当前 `CHANGELOG.md` 内容未读取。**建议**追加 2026-07 段落说明本次重构：
- 阶段一：P0 修复（BOM + 未用 import）
- 阶段二：清理 __pycache__ 与临时日志
- 阶段三：依赖校准

---

## 4. 综合建议汇总（待您批准）

| ID | 建议 | 优先级 | 工作量 |
|---|---|---|---|
| C1 | **不修改** `.gitignore` | — | 0 |
| C2 | **添加** `requests>=2.31`（必须） | P0 | 1 行 |
| C3 | **添加** `scipy>=1.10` / `lxml>=4.9`（建议） | P1 | 2 行 |
| C4 | **不删除** 任何现有依赖（保留兼容性） | — | 0 |
| C5 | **追加** "项目结构" 章节到 README | P2 | ~15 行 |
| C6 | **追加** "开发工作流" 章节到 README | P2 | ~10 行 |
| C7 | **追加** CHANGELOG 条目 | P2 | ~10 行 |

---

## 5. 待您指令

回复：
- **A**：批准 C1–C7 全部
- **B**：仅 C2（最保守，仅加 `requests`）
- **C**：C2+C3（依赖最小集）
- **D**：C2+C3+C5（依赖 + 项目结构文档）
- **取消**：不修改任何文件