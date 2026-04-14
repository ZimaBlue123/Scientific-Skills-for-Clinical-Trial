---
name: word-audit-report-format
description: Generate or update Word (.docx) audit/review reports with enforced fonts. Use when the user asks for “审核报告/审计式审核/生成Word/导出docx” and requires Chinese font SimSun (宋体) and English font Times New Roman, including headings and tables.
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
- 使用脚本：`scripts/generate_audit_report_docx.py`
- 关键函数：`_apply_cn_en_fonts(doc)`

