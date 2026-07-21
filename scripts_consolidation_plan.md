# scripts/ 整合精简方案（待批准）

## 一、当前盘点（35 个 .py 脚本，_archive/ 不计）

| 类别 | 数量 | 总代码量 |
|---|---:|---:|
| **docx_extract**（docx 文本提取） | 7 | 61 KB |
| **docx_generate**（docx 生成） | 10 | 195 KB |
| **docx_convert**（格式互转） | 5 | 25 KB |
| **docx_dsur**（DSUR 专项） | 2 | 23 KB |
| **xlsx** | 2 | 25 KB |
| **lit_search**（文献检索） | 2 | 13 KB |
| **maintenance**（维护工具） | 5 | 70 KB |
| **other**（共享 utility 等） | 2 | 18 KB |

## 二、可整合点（按优先级）

### 🔴 优先级 1：docx_extract 严重重复（**-4 个脚本**）

| 当前脚本 | 大小 | 状态 | 处置 |
|---|---:|---|---|
| `_extract_docx_text.py` | 5477 B | 下划线开头（私有），但被多处使用 | **删除并合并到 `extract_docx_full.py`** |
| `extract_docx_full.py` | 6080 B | 已支持 docx/doc/folder 多种模式 + 公共 API | **升级为统一入口** |
| `extract_docx_to_md.py` | 4447 B | docx→md 子功能 | **改造为 `extract_docx_full.py` 的 `--format md` 子模式** |
| `extract_ib_texts.py` | 10063 B | IB 专用，封装 `Document()` + 自定义 `IBExtractResult` class | **保留**（业务语义独立），但调用 `_extract_docx_text` 的代码改为 import `extract_docx_full` |

**预期效果**：7 → 3 个脚本（保留 extract_doc_text.py for legacy .doc、extract_docx_full.py for 现代、extract_ib_texts.py for 业务）

### 🔴 优先级 2：docx_convert 整合（**-3 个脚本**）

| 当前脚本 | 大小 | 状态 | 处置 |
|---|---:|---|---|
| `convert_doc_to_docx.py` | 1197 B | 仅调用 win32com Word.Application | **删除**（功能已被 `convert_to_md.py` 的 `convert_doc` 路径覆盖） |
| `md_to_docx.py` | 4342 B | md→docx 转换 | **保留** |
| `convert_audit_report_md_to_docx.py` | 1020 B | 与 md_to_docx 高度重复 | **删除并入 md_to_docx.py**（通过 `--style` 参数切换） |
| `convert_to_md.py` | 13743 B | docx/pdf/rtf/doc → md 统一入口 | **保留**（已有 unify 作用） |
| `make_safe_md_copies.py` | 5081 B | 制作脱敏副本 | **保留**（独立业务） |

**预期效果**：5 → 2 个脚本（convert_to_md.py + md_to_docx.py）

### 🟡 优先级 3：docx_generate 抽象（**保留数量，提升可维护性**）

`docx_generate` 类别 10 个脚本总计 195 KB，但**每个脚本对应一个独立的 CSR/审核报告/桥接文档模板**，业务领域不同，不应强行合并；建议：

- **新建** `scripts/common_scripts/generator_base.py`：抽取共用模式（日志、模板加载、字体设置、标题样式）
- 让 10 个 generate_* 脚本改为薄壳（30-50 行），调用 base 模块
- **预期效果**：现有代码量 -30%（约 60 KB 抽取到 base）

### 🟢 优先级 4：lit_search 整合（**-1 个脚本**）

| 当前脚本 | 大小 | 状态 | 处置 |
|---|---:|---|---|
| `pubmed_lit_search.py` | 5913 B | DSUR §13 文献检索 | **保留** |
| `norovirus_trial_search.py` | 7177 B | HilleVax 诺如疫苗专用 | **保留**（业务领域不同） |

**结论**：仅 1 个整合候选（pubmed_lit_search 和 norovirus_trial_search 几乎都用 PubMed E-utilities，但因业务领域和入参不同，合并的边际收益不显著，**建议保留**）。

### 🟢 优先级 5：maintenance 与 other（**保留**）

- `cleanup_generated_artifacts.py`（31 KB）、`project_self_check.py`（10 KB）、`skill_dedupe_report.py`、`_selftest_*`：业务功能独立，无明显重复
- `common_scripts/docx_utils.py`（3 KB）：唯一共享模块，已被 21 个 docx 脚本使用，**保留并扩展**

## 三、整合后总览

| 类别 | 当前 | 整合后 | Δ |
|---|---:|---:|---:|
| docx_extract | 7 | **3** | **-4** |
| docx_convert | 5 | **2** | **-3** |
| docx_generate | 10 | 10（薄壳化） | 0 |
| docx_dsur | 2 | 2 | 0 |
| xlsx | 2 | 2 | 0 |
| lit_search | 2 | 2 | 0 |
| maintenance | 5 | 5 | 0 |
| other | 2 | 3 (+generator_base.py) | +1 |
| **总计** | **35** | **29** | **-6** |

代码量减少估算：
- 删除 7 个重复脚本：约 -27 KB（_extract_docx_text + convert_doc_to_docx + convert_audit_report_md_to_docx + 部分 extract_docx_to_md）
- 抽取 generator_base：约 -60 KB 重复代码
- **净减少约 87 KB**（约 27%）

## 四、建议执行顺序

1. **先备份**：`scripts/_archive/` 已是软隔离；新增 `scripts/_archive_2026_consolidation/` 暂存待删脚本
2. **优先级 1**：合并 docx_extract（修改 extract_docx_full.py + 删除 _extract_docx_text.py 与 extract_docx_to_md.py 独立入口）
3. **优先级 2**：合并 docx_convert（删除 convert_doc_to_docx.py + convert_audit_report_md_to_docx.py）
4. **优先级 3**：抽取 generator_base.py（不删脚本，只重构）
5. **回归测试**：每个 generate_* 脚本跑一次生成验证
6. **本地 commit**：`refactor(scripts): consolidate 7 extract/convert scripts into unified entry points`

## 五、风险评估

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 调用方脚本未同步更新 | 中 | 中 | 全仓搜索旧 import 路径，保留兼容层（deprecated） |
| extract_docx_full.py 升级引入回归 | 低 | 高 | 现有测试 + 灰度替换：先并存，再切流量 |
| docx 格式差异（doc/docx）丢失支持 | 低 | 中 | 在 extract_docx_full.py 中保留 `extract_doc_legacy` 函数 |
| 用户已有调用旧脚本的 CI / cron | 低 | 低 | 在旧入口加 deprecation warning，1 版本后删除 |

## 六、需要您的明确批准

请回答以下 3 项后我才开始执行：
1. **是否同意整合方案？**（同意/部分同意/拒绝）
2. **优先级 1-5 是否按顺序全部执行？**（或仅执行前 N 项）
3. **是否先归档到 `scripts/_archive_2026_consolidation/`？**（是/否）

---

**报告日期**: 2026-07-21
**审计依据**: `_audit_scripts.py` 产出 [`scripts/_audit_report.md`](scripts/_audit_report.md:1)