---
name: dsur-end-to-end-workflow
description: "End-to-end Development Safety Update Report (DSUR) workflow under ICH E2F and NMPA guidelines: Step 1 read-only completeness & discrepancy audit (requesting missing materials and surfacing data conflicts before any edit), Step 2 in-place Word optimization (2.5 cm margins, AutoFit Window tables, anti-orphan long-cell layout, TOC refresh, comment preservation), 5-module delivery split with bookmarked & Chinese-translated literature PDF bundle, sign-and-return cover letters, and eCTD PDF compliance validation. Use when the user asks to generate, update, audit, split, or package a DSUR."
license: MIT
metadata:
  version: "1.0.0"
  skill-author: "Scientific Skills for Clinical Trial Contributors"
---

# 研发期间安全性更新报告（DSUR）端到端标准化工作流

## 语境与核心原则

本技能严格限定于**已开展/已获批临床试验的回顾性安全性数据审核、统计学参数交叉校验与 ICH E2F / 中国《研发期间安全性更新报告管理规范（试行）》合规文档撰写**。所有步骤遵循以下硬性工作规范：

1. **前置复述与两阶段门控（Mandatory Gate）**：
   - 触发本技能后，**必须先复述用户要求并清点文件数量与前置条件**，经用户确认后再启动执行；
   - **第一步（阶段 A — 只读审核）→ 用户确认 → 第二步（阶段 B — 流程化生成与交付）**。未经用户确认，严禁修改或覆写任何文件。
2. **差异裁定原则**：与外部数据或历史口径出现冲突时，必须先输出**「差异清单 + 根因归因」**交用户裁定，严禁擅自更改核心统计口径。
3. **版本保护**：严禁覆盖母版或任何历史交付稿；每次修改前必须先创建独立备份（`_vN备份.docx` 或 `pre_*_backup/`），新版本采用递增版本号另存。
4. **就地同步原则**：基于既有 DSUR 母版做 run 级/单元格级/行级定向改写，保留原有标题层级、自动编号、段首加粗与上标 `[n]`；**禁止**整篇重造或使用 `paragraph.text=` / `cell.text=` 粗暴覆盖。

---

## 复用技能与脚本依赖（Dependencies）

执行本工作流时，优先调用以下已验证模块，不得重复造轮子：

- **相关技能**：
  - `clinical-pdf-ectd`：PDF eCTD 合规装甲转换与 `--validate-only` 审计
  - `pv-medical-auditor`：PV 医学逻辑质控与合规审核
  - `clinical-strict-extractor`：结构化、无废话、确定性数据提取
  - `pubmed-database`：报告周期内新增安全性文献检索与 PMID/DOI 实测核验
- **核心脚本与工具**：
  - `scripts/pipeline/review/audit_ledger_and_findings.py`：覆盖率台账与三态裁定（`confirmed` / `needs_validation` / `rejected`）Schema 校验及报告派生
  - `scripts/pipeline/validate/docx_clean_validator.py`：Word Clean 合规校验
  - `scripts/pipeline/export/docx_builder.py`：`enable_table_row_cant_split` 等 OOXML 排版工具
  - `scripts/pipeline/export/update_docx_toc_fields.py`：Word COM 目录域刷新
  - `scripts/_tools/preview_docx.py`：Word COM 渲染页图视觉核验
  - `scripts/clinical-automation/18_PDF_eCTD_Converter/pdf_ectd_converter.py`：eCTD PDF 转换与审计报告生成

---

## 第一步：资料审核与前置分析（阶段 A — 只读）

### 1.1 资料完整性核查（对照 `references/dsur_checklist.md`）

逐项核对用户提供的资料收集清单与文件包，若发现缺失（如缺最新版 IB 修订记录、缺 EDC 导出 Excel、缺批准通知书或文献原文 PDF），**立即列出缺漏清单向用户索要**，待补齐或用户明确豁免后再进入下一步：

1. **DSUR 基线/母版 Word**（或参考模板，如上一周期 DSUR / 预定稿参照包）
2. **最新 EDC 导出 Excel**（安全性数据**唯一权威数据源**）
3. **研究者手册（IB）最新版及版本修订记录**（核对第 4 章更新摘要、RSI 预期性、18.1.1/20 章同类产品不良反应）
4. **临床试验方案最新版及历次修订记录**（核对样本量、年龄分层、盲法/双盲表述、高血压/妊娠等排除随访阈值、附件 R4 变更记录）
5. **风险管理计划（RMP）最新版**（核对重要已确认风险与重要潜在风险，支撑第 19 章及附件 2）
6. **药物临床试验批准通知书 PDF**（核对附件 2 第一大章节前置条件及监管要求逐条一致性）
7. **研究中心进展报告 Excel（若有）**：仅用于校准试验入组/接种/随访完成度与收尾状态，**严禁**以其替代 EDC 导出 Excel 中的 AE/SAE 具体例数与转归
8. **报告周期内英文安全性文献原文 PDF**（核对检索时间窗、PMID/DOI 实测可达性及摘要翻译素材）
9. **需签章后返回模板（若有）**：递交信（主要研究者、伦理审查委员会）及执行摘要模板

### 1.2 数据口径与合规时限交叉核验

1. **EDC 数据解析坑点排查**：
   - 若原始 `.xlsx` 含非法 `<autoFilter ref="1:1"/>` 或 `<dimension ref="A1"/>`，先在 zip 层剥离这两类标签再以 `read_only + reset_dimensions()` 读取；
   - 统计前过滤 SDTM 变量名行（`SUBJID`、`AEYN`、`MDRAVER` 等），核验 MedDRA 字典版本列（`MDRAVER`）与语言（`MDRALANG`），切勿与数据库版本（`Database_Version = V1.0`）混淆；
   - SAE 口径取「SAE 表 ∪ AE 表中 `是否为SAE=是`」去重并集，同时记录最新 EDC 导出日期及转归分布（注明未锁库数据后续可能随随访进展更新）。
2. **修订标记预处理检查**：检查母版 Word 是否残留 `w:ins` / `w:del` 修订标记；若存在，必须在任何定向改写前先完成全部修订接受与关闭 `w:trackRevisions`。
3. **递交最晚截止日核算**：
   - **ICH E2F**：DLP（报告周期结束日）起 **60 个自然日**内；
   - **中国 CDE《研发期间安全性更新报告管理规范（试行）》**：报告周期结束后 **2 个自然月**内；
   - 取二者较早日期作为从严合规最晚递交日提示用户。
4. **输出阶段 A 报告（覆盖率台账 + 三态裁定门控）**：
   - 使用 `scripts/pipeline/review/audit_ledger_and_findings.py` 维护各章/附录/EDC/IB 核对台账（`coverage-ledger.json`）与问题裁定（`findings.json`）：
     - `confirmed`：已取得源文件直接证据的确定性问题（标注 `P0–P3`）；
     - `needs_validation`：信息缺失或待申办方/CRO 确认的事项（仅列明待确认事实，严禁虚标严重度）；
     - `rejected`：经交叉核对已证伪的误报候选（仅留审计轨迹，不写入客户待办）。
   - 以结构化 Markdown 输出「缺漏资料清单（若有）」「差距清单与优化计划」「待裁定差异清单（含根因归因）」，**等待用户确认后再进入第二步**。

---

## 第二步：流程化生成与合规交付（阶段 B — 经确认后执行）

### 2.1 完整版 DSUR 终稿生成（先备份、递增版本号）

1. 先备份基线 `.docx`（`_vN备份.docx`），再生成递增版本号终稿（`_v{N+1}.docx`）。
2. 定向更新已裁定内容（安全数据口径、最新 EDC 转归、IB/方案修订同步、试验最新进展、附件 2 监管要求逐条回应、文献检索与核验表）。
3. **批注与高亮处理**：按用户裁定保留指定审阅批注（如统一批注人姓名）或清理无关批注/残留高亮；未指定保留批注的交付件须通过 `docx_clean_validator.py`（`✅ CLEAN`）。

### 2.2 Word 全篇格式与排版规范（联动 `AGENTS.md` §10）

对所有生成与拆分后的 `.docx` 统一执行：

1. **统一 2.5 cm 页边距**：所有分节（纵向与横向）`w:pgMar` 的 `top`/`bottom`/`left`/`right` 统一设为 **`1417 twips`（2.5 cm）**。
2. **页眉页脚规范**：
   - 完整版与预定稿分册：清除 CRO（如斯丹姆）模板信息与 logo，页眉保留「方案编号（左）」+「DSUR 版本日期（右）」+ 单线底边框，右对齐制表位精准匹配 2.5 cm 版心（A4 纵向 `9072 twips`，横向 `14004 twips`）；页脚仅保留居中 `PAGE \* MERGEFORMAT` 页码域；
   - 需签章后返回文件：递交信彻底移除页眉与页脚；执行摘要保持与完整版 DSUR 一致的统一页眉、无页脚。
3. **表格窗口自适应与防孤标题/空表头/截断**：
   - 默认按 Word「根据窗口自动调整表格」设置：`w:tblW="5000" w:type="pct"`，清除 `w:tblInd`，`tblGrid` 匹配所在节版心（`9072` / `14004`），`tcW` 按 `pct` 分配（合计 `5000`）；含超长不可折行 URL 的链接表采用 `w:tblLayout="fixed"` 锁定列宽；
   - 全部表格启用 `w:tblHeader`（含双行复合表头）与 `w:cantSplit`；
   - **长文本表格处理**：评估长行高度，优先优化列宽比例（摘要/正文列 ≥50% 宽）并收紧表内排版（表头 9.5 pt 加粗、正文 9 pt、1.15 倍行距、段前段后 0 pt、单元格上下边距 40 dxa），表题设 `w:keepNext` 绑定表头；若个别超长行优化后仍必然超出一页，仅为该行移除 `w:cantSplit`，杜绝孤标题页、空表头页与文字截断。
4. **目录刷新**：对含目录域的文档运行 `scripts/pipeline/export/update_docx_toc_fields.py`。

### 2.3 五大模块拆分交付包（`<项目编号> 预定稿文件\`）

从终稿完整版 `.docx` 按 OOXML 节点边界切片生成（过滤每个切片的 `comments.xml`/`commentsExtended.xml`/`commentsIds.xml`，确保每个子文档完整保留属于该章节的原有批注与高亮）：

1. **根目录（Word）**：
   - `<申办者>_<疫苗名>_DSUR#<N>（<周期>）_预定稿_全文含附件（保留批注）.docx`
   - `<申办者>_<疫苗名>_DSUR#<N>（<周期>）_预定稿_正文不含附件（保留批注）.docx`（刷新 1–20 章目录）
   - `<申办者>_<疫苗名>_DSUR#<N>（<周期>）_预定稿_执行摘要.docx`
2. **附录（`附录\`，Word + 对应 eCTD PDF）**：
   - `附录1 研究者手册.docx` + `附录1 研究者手册[请申办方老师合并签章版IB].pdf`
   - `附录2`–`附录6` 各自独立 `.docx` + `.pdf`
   - `附录7 文献[目录].docx` + `.pdf`
   - `附录7 文献[<K>篇安全性文献合辑].pdf`（原文 PDF 合并 + 一级文献书签）
   - `附录7 文献[<K>篇安全性文献合辑][添加书签&摘要翻译版].pdf`（每篇英文原文前插入 1 页 Word 渲染的中文标题+出处+完整中文摘要翻译页，配一级文献目录书签 + 二级「中文摘要翻译 / 英文原文」书签）
3. **区域附录（`区域附录\`，Word + 对应 eCTD PDF）**：
   - `附录R1`–`附录R3` 各自独立 `.docx` + `.pdf`
   - `附录R4`、`附录R5` 各自独立 `.docx`（保留批注）+ `.pdf`

### 2.4 需签章后返回包（`<项目编号> 需签章后返回\`）

1. `递交信（主要研究者）.docx`（1 页完整含签字栏与回执，无页眉页脚，无 CRO 信息，申办者主体名称严格与 DSUR 原文一致）
2. `递交信（伦理审查委员会）.docx`（同上）
3. `执行摘要.docx`（同步自终稿执行摘要，带统一 DSUR 页眉，无页脚，2.5 cm 页边距）

### 2.5 PDF eCTD 合规转换

1. 所有附录与区域附录 `.docx` 经 Word COM 以 `CreateBookmarks=1`（按标题层级生成章节书签）导出 PDF。
2. 对全部交付 PDF 运行：
   ```bash
   python scripts/clinical-automation/18_PDF_eCTD_Converter/pdf_ectd_converter.py \
     --input "<预定稿目录>" --output "<暂存目录>" \
     --report "<预定稿目录>/eCTD合规审计报告.xlsx" \
     --keep-name --overwrite --no-delete-input --subset-fonts --linearize
   ```
3. 将转换后 PDF 回写覆盖至预定稿对应子目录（原导出 PDF 保留在 `_extract/` 备份中），再执行 `--validate-only` 全量复检，确认 `structure_warnings=0` 且每份 PDF 书签完整。

---

## Pre-flight Check

1. 核实用户输入的全部文件路径存在且可读，无独占锁（`open(p, 'r+b')` 通过）。
2. 核实项目 `.venv/Scripts/python.exe`、`python-docx`、`openpyxl`、`pymupdf`、`fontTools` 及本机 Word COM 可用。
3. 创建历史版本备份后再执行任何写入操作；所有临时脚本仅存放于 `scripts/` 并在验证后清理。

## Post-execution Validation

1. **Word 校验**：检查全部 `.docx` 页边距均为 `2.5 cm`（`1417 twips`）、无残留修订标记、无旧项目/CRO 残留词、批注数量与归属切片完全一致；`需签章后返回\` 3 份文件通过 `docx_clean_validator.py`（`✅ CLEAN`）。
2. **PDF eCTD 校验**：`pdf_ectd_converter.py --validate-only` 全部通过（`structure_warnings=0`），`pymupdf` 核验每份 PDF 均含有效章节/文献书签，交付 `eCTD合规审计报告.xlsx`。
3. **视觉抽检（Visual QA）**：调用 `scripts/_tools/preview_docx.py` 抽检封面、目录、表 2 跨页表头、附录 2、附录 7 汇总表、文献中文翻译页及递交信渲染图，确认无孤标题页、无空表头页、无溢出或乱码后清理临时预览目录与脚本。
