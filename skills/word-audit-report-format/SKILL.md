---
name: word-audit-report-format
description: Generate or update Word (.docx) audit/review reports with enforced fonts. Use when the user asks for “审核报告/审计式审核/生成Word/导出docx” and requires Chinese font SimSun (宋体) and English font Times New Roman, including headings and tables.
metadata:
  version: "1.0.0"
---
# Word 审核报告字体规范

## 适用场景
- 用户要求输出 **Word（.docx）** 审核/评审/审计报告
- 明确提出 **中文宋体、英文 Times New Roman**
- 需要覆盖 **标题、正文、表格**

## 生成/修改规则（python-docx）
- **必须在创建 `Document()` 后立即设置全局样式字体**
  - 英文字体（ASCII/HAnsi/CS）：`Times New Roman`
  - 中文字体（East Asia）：`宋体`
- 至少覆盖这些样式（如存在则设置）：
  - `Normal`, `Title`, `Heading 1`, `Heading 2`, `Heading 3`, `Table Grid`
- 设置 East Asia 字体需要通过 `w:eastAsia`（`qn("w:eastAsia")`）写入 `rFonts`。

## 项目内默认实现
- 使用脚本：`scripts/pipeline/export/docx_builder.py`
- 关键函数：`apply_cn_en_fonts(doc)`

## 结构化审计数据源与三态分离规范（Schema Gate）
当基于结构化审核发现生成 Word 审核报告或 DCF 意见表时，**必须先通过 `scripts/pipeline/review/audit_ledger_and_findings.py` 的 Schema 校验**：
1. **`confirmed`（已确认问题）**：按 `P0 → P3` 严重度排序写入正式审核意见表，每条必须含 `source_ref` 原文溯源与客观证据。
2. **`needs_validation`（待确认/澄清事项）**：独立成节渲染为「待申办方/研究者澄清清单」，**禁止**为其分配严重度标签。
3. **`rejected`（已证伪候选项）**：仅在 `findings.json` 留存证伪理由，**严禁**输出到交付客户/研究者的 Word 质疑表中。

## Pre-flight Check

Before executing, the agent MUST:
1. Verify input file exists at the expected path
2. Clear any cached results from previous runs
3. Confirm required environment variables are set

## Post-execution Validation

After execution, the agent MUST:
1. Verify output file was created successfully
2. Run applicable validator (if available)
3. Report results in standardized Markdown table format
