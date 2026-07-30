# 阶段一审计报告：代码健壮性与语法 (Code Quality & Robustness Audit)

> **范围**：项目 `E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\` 下 `scripts/`、`scripts/common_scripts/`、`skills/*/scripts/`、`tests/`，**不含 `_archive/`**
> **时间**：2026-07-30
> **审计者**：Roo（Architect→Code 阶段切换后执行）
> **当前状态**：已完成静态扫描，**未做任何代码修改**（等用户指令）
> **生成的所有中间文件**：
> - `reports/phase1_file_list.txt` — 240 个 .py 文件清单
> - `reports/phase1_compile_ok.txt` / `phase1_compile_fail.txt`
> - `reports/phase1_pyflakes_raw.txt` — pyflakes 原始输出
> - `reports/phase1_pyflakes_categories.md` — pyflakes 类别分布
> - `reports/phase1_pyflakes_top_files.md` — Top 20 问题文件
> - `reports/phase1_ast_audit.md` — AST 深度审查指标

---

## 1. 审计范围盘点

| 分组 | 文件数 | 字节数 |
|---|---:|---:|
| `scripts/` 顶层 | 29 | — |
| `scripts/common_scripts/` | 3 | — |
| `scripts/_tools/` | 6 | — |
| `scripts/_archive_2026_consolidation/` | 16 | — |
| `scripts/_selftest_*` | 2 | — |
| `skills/*/scripts/` | 183 | — |
| `tests/` | 1 | — |
| **合计** | **240** | **2,483,661 (~2.4 MB)** |

> 4 个 `_audit_*.py` 与 `extract_review_doc_stdlib.py`、`verify_data.py` 等根目录长期工具已在阶段零归位至 `scripts/_tools/` 与 `scripts/`。

---

## 2. 语法编译（py_compile + AST）

| 检查项 | 结果 |
|---|---|
| `py_compile` 全量编译 | **240 / 240 通过** |
| `ast.parse` 严格解析 | **239 / 240 通过**；**1 个失败** |

### 2.1 唯一 AST 失败

| 文件 | 行 | 问题 | 风险 |
|---|---:|---|---|
| `scripts/verify_data.py` | L1 | 含 UTF-8 BOM `U+FEFF` | pyflakes 已能容忍，但部分工具链（ast、mypy、ruff 旧版）会失败；文件顶部多 3 个字节；Shebang 不在 L1 |

> **优先级 P0**：1 行修复（删除 BOM）。

---

## 3. pyflakes 静态分析

| 指标 | 数值 |
|---|---:|
| 扫描文件数 | 240 |
| 有问题的文件数 | **105（43.7%）** |
| 总问题数 | **310** |

### 3.1 类别分布（Top 10）

| 数量 | 消息 | 含义 |
|---:|---|---|
| **178** | `f-string is missing placeholders` | `f"..."` 内无 `{...}` 占位符，纯静态字符串误加 `f` 前缀 |
| 32 | `local variable 'X' is assigned to but never used` | 局部变量赋值未使用 |
| 8 | `'pathlib.Path' imported but unused` | 未使用导入 |
| 7 | `'typing.Optional' imported but unused` | 同上 |
| 6 | `'typing.Tuple' imported but unused` | 同上 |
| 6 | `'json' imported but unused` | 同上 |
| 5 | `'pandas as pd' imported but unused` | 同上 |
| 5 | `'os' imported but unused` | 同上 |
| 4 | `'numpy as np' imported but unused` | 同上 |
| 3 | `'re' imported but unused` | 同上 |

> **结论**：57.4% 的问题是 **`f-string missing placeholders`**（轻量、低风险、可批量修复）；其余约 132 个是**未使用导入/变量**（低风险）。

### 3.2 Top 10 问题文件

| 问题数 | 文件 |
|---:|---|
| 15 | `skills/infographics/scripts/generate_infographic_ai.py` |
| 12 | `skills/pymc/scripts/model_comparison.py` |
| 11 | `skills/brenda-database/scripts/brenda_visualization.py` |
| 11 | `skills/diffdock/scripts/setup_check.py` |
| 10 | `skills/bioservices/scripts/protein_analysis_workflow.py` |
| 9 | `skills/brenda-database/scripts/brenda_queries.py` |
| 8 | `skills/brenda-database/scripts/enzyme_pathway_builder.py` |
| 8 | `skills/pymc/scripts/model_diagnostics.py` |
| 8 | `skills/scientific-schematics/scripts/generate_schematic_ai.py` |
| 7 | `skills/bioservices/scripts/{batch_id_converter, compound_cross_reference, pathway_analysis}.py` |
| 7 | `skills/fda-database/scripts/fda_examples.py` |

> **结论**：问题**集中在 `skills/`**；核心 `scripts/` 顶层（29 个）**几乎全部干净**——仅 4 个文件上榜，且每个仅 1 个问题：
> - `scripts/verify_data.py`（1：未使用 `Callable`）
> - `scripts/_archive_2026_consolidation/_verify_data.py`（1：未使用 `re`）
> - `scripts/_tools/_audit_scripts.py`（1：未使用 `re`）
> - `scripts/_tools/scan_cleanup.py`（1：f-string 缺占位符）

---

## 4. AST 深度审查

| 指标 | 数值 | 评估 |
|---|---:|---|
| 函数总数 | 1,714 | — |
| 有返回类型注解的函数 | **860（50%）** | ✅ **健康** |
| 调用 `logger.*` 的函数 | **83（4%）** | ⚠️ **极低** — 主流是 print |
| 含 `try` 块的函数 | 393 | ✅ 健康 |
| `except` handler 总数 | 1,161 | — |
| **`bare except`**（`except:`） | **22** | ✅ 极少 |
| 含 bare except 的文件 | 10 | ✅ |
| 含 broad `Exception/BaseException` 的文件 | — | 散见 |
| 模块级 logger 缺失（函数 >3） | **140 / 239** | ⚠️ **广泛缺失** |
| 使用 `print()` 的文件 | **214 / 239（89.5%）** | ⚠️ **极高** |
| `print()` 总调用次数 | **3,903** | ⚠️ |

### 4.1 bare except Top 5

| 数量 | 文件 |
|---:|---|
| 4 | `skills/clinical-decision-support/scripts/generate_survival_analysis.py` |
| 2 | `skills/bioservices/scripts/pathway_analysis.py` |
| 2 | `skills/bioservices/scripts/protein_analysis_workflow.py` |
| 2 | `skills/chembl-database/scripts/example_queries.py` |
| 2 | `skills/get-available-resources/scripts/detect_resources.py` |

> **22 处 bare except** 全部位于 `skills/`，**核心 `scripts/` 0 处**。

### 4.2 print 调用 Top 5

| 次数 | 文件 |
|---:|---|
| 95 | `skills/bioservices/scripts/protein_analysis_workflow.py` |
| 93 | `skills/pytdc/scripts/molecular_generation.py` |
| 87 | `skills/fred-economic-data/scripts/fred_examples.py` |
| 74 | `skills/bioservices/scripts/compound_cross_reference.py` |
| 73 | `skills/pymc/scripts/model_comparison.py` |

---

## 5. 工程化改进建议（按优先级）

### P0 — 必修（5 分钟级，影响 CI/下游工具链）

| # | 修复 | 范围 | 风险 |
|---|---|---|---|
| P0-1 | 删除 `scripts/verify_data.py` L1 的 UTF-8 BOM | 1 文件 / 1 行 | 极低 |
| P0-2 | （可选）移除 `verify_data.py` 中未使用的 `Callable` 导入（L30） | 1 文件 / 1 行 | 极低 |

### P1 — 强烈建议（覆盖大部分问题，可自动化修复）

| # | 修复 | 范围 | 风险 |
|---|---|---|---|
| P1-1 | 把所有无占位符的 `f""` 改成 `""`（178 处） | 多文件 | **极低**（机械替换） |
| P1-2 | 删除全部未使用导入（~50 处；pathlib.Path / typing.Optional / json / os / pandas / numpy / re / Any 等） | 多文件 | 低（需逐文件确认不影响外部 API） |
| P1-3 | 删除未使用的局部变量（32 处） | 多文件 | 低 |

### P2 — 建议（提升日志规范）

| # | 修复 | 范围 | 风险 |
|---|---|---|---|
| P2-1 | 在 `scripts/` 顶层 29 个核心脚本中，将 `print()` 替换为 `logger.info(...)` | 29 文件 | 中（需引入 `logger = logging.getLogger(__name__)`，可能改变 stdout 行为） |
| P2-2 | 在 `skills/*/scripts/` 高 print 文件中替换 print → logger | ~50 文件 | 中-高（每个 skill 输出格式可能不同） |

> **建议**：P2 仅对 `scripts/` 顶层与 `scripts/common_scripts/` 做；**不动 `skills/`**（它们是教学示例，print 更直观）。

### P3 — 不在本次范围（深度重构）

| # | 修复 | 说明 |
|---|---|---|
| P3-1 | 给 854 个无注解函数补 `-> ReturnType` | 工作量大，需逐函数审查；建议作为下一轮（阶段一 v2） |
| P3-2 | 把 22 处 bare except 改成具体异常 | 单独 patch 即可；建议作为下一轮 |
| P3-3 | 引入 `generator_base.py` 统一所有 `generate_*` 脚本 | 已在 `scripts_consolidation_analysis.md` §4.2 标记为 M8 |

---

## 6. 安全基线（基线状态说明）

### 6.1 当前 Worktree 状态

| 项 | 状态 |
|---|---|
| HEAD | `02ceb75 refactor(scripts): consolidate 19 root-level .py files into scripts/` |
| ahead of origin/main | 1 commit |
| 工作区 untracked | 14 个（.txt/.log/.err 等非代码产物，不影响基线） |

### 6.2 基线脚本

5 个阶段一审计脚本已落到 `scripts/_tools/`：
- `_audit_phase1.py` — 范围盘点
- `_audit_phase1_compile.py` — py_compile + AST 解析
- `_audit_phase1_pyflakes.py` — pyflakes 第一版（含 Bug）
- `_audit_phase1_pyflakes2.py` — 第二版（修正未生效）
- `_audit_phase1_pyflakes3.py` — 第三版（基于 raw 文件解析，成功）
- `_audit_phase1_ast.py` — AST 深度审查

> 这 6 个脚本本身**未提交**（仍在工作区 untracked）。在阶段一提交基线前，建议先 `git add scripts/_tools/_audit_*.py` 让它们纳入版本控制，作为审计的"代码化石"。

---

## 7. 待用户决策（阶段一进入"实际修改"前必须明确）

### Q1. 修复范围

| 选项 | 描述 |
|---|---|
| **A** | 仅 P0（删除 BOM 1 行） |
| **B** | P0 + P1（最稳妥，覆盖 ~95% pyflakes 问题） |
| **C** | P0 + P1 + P2（覆盖 scripts/ 顶层的 print→logger，工作量较大） |
| **D** | 仅审计不修复（保留基线，等待后续独立修复轮） |

### Q2. P2 范围限定

| 选项 | 描述 |
|---|---|
| **A** | 仅 `scripts/` 顶层 + `scripts/common_scripts/`（推荐） |
| **B** | 也覆盖 `scripts/_tools/` 与 `scripts/_archive_2026_consolidation/` |
| **C** | 不动 scripts/，只把审计报告作为下一轮输入 |

### Q3. 基线提交粒度

| 选项 | 描述 |
|---|---|
| **A** | 把 6 个 `_audit_*.py` 与 `docs/audit_phase1.md` 合并到一次 commit |
| **B** | 分两次：① 提交审计脚本（仅新增） ② 提交审计报告（仅新增） |
| **C** | 不提交审计脚本（避免污染 scripts/_tools/） |

---

## 8. 报告版本

- v1.0（2026-07-30）：阶段一完整审计报告。  
- **下一步**：等待用户指令确定 Q1–Q3 后，进入 1-8 实际修复 + 本地 commit。

---

## 附录：报告与中间产物

```
reports/
  phase1_file_list.txt              # 240 个文件清单（每行一个相对路径）
  phase1_compile_ok.txt             # 240 通过 py_compile
  phase1_compile_fail.txt           # 0 失败（仅 1 个 AST 错误在 phase1_step2.txt）
  phase1_pyflakes_raw.txt           # 521 行原始 pyflakes 输出
  phase1_pyflakes_categories.md     # 类别分布
  phase1_pyflakes_top_files.md      # Top 20 问题文件
  phase1_ast_audit.md               # AST 深度审查指标

scripts/_tools/
  _audit_phase1.py
  _audit_phase1_compile.py
  _audit_phase1_pyflakes.py         # 早期版本（正则有 Bug，仅供审计）
  _audit_phase1_pyflakes2.py        # 第二版（已弃用）
  _audit_phase1_pyflakes3.py        # 推荐版本（解析 raw 文件，不重跑 pyflakes）
  _audit_phase1_ast.py