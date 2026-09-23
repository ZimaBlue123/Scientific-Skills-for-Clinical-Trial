---
name: clinical-pdf-extraction
description: Extract structured data from clinical PDFs into Excel - serology reports, ADR grading tables, and rule-driven keyword extraction, plus locating and masking page header/watermark interference regions. Use when the user asks for "PDF 提取 Excel / 血清报告 汇总 / ADR 分级 回填 / 按规则提取 PDF / 页眉水印 干扰区 / 排除框".
license: MIT
compatibility: Requires Python 3.10+ with pymupdf, pandas, openpyxl and pdfplumber; OCR additionally needs a local Tesseract installation.
allowed-tools: Read Write Edit Bash
metadata:
  version: "1.0"
  skill-author: Scientific Skills for Clinical Trial Contributors
  last-reviewed: "2026-09-18"
---

# 临床 PDF 数据提取

三个模块按场景选用，可串联使用。

## 一、血清报告 / ADR 分级表专用提取

脚本：`scripts/clinical-automation/12_PDF_Batch_to_Excel/`

```bash
cd scripts/clinical-automation/12_PDF_Batch_to_Excel
python serology_report_pdf_to_excel.py --input "input" --output "output/serology_report_merged.xlsx" --ocr --ocr-dpi 110
python fill_adr_from_pdf.py                    # ADR 分级表专用提取
python util_audit_and_fix_consistency.py       # ADR 表与 PDF 一致性检查与修正
```

血清报告场景**建议开 `--ocr`**（需本机 Tesseract + `chi_sim+eng` 语言包）。

## 二、规则驱动提取（config.yaml）

脚本：`scripts/clinical-automation/13_PDF_to_Excel_Rule_Extract/main.py`

```bash
cd scripts/clinical-automation/13_PDF_to_Excel_Rule_Extract
python main.py
python main.py --config config.yaml --exclusion-json "../21_PDF_Watermark_Removal/output/<文件>_boxes.json"
```

规则写在 `scripts/clinical-automation/config.example.yaml`（复制为 `config.yaml`，该文件不入库）：

```yaml
pdf_path: "13_PDF_to_Excel_Rule_Extract/input/不同剂量组ADR分析 (TFL).pdf"
excel_path: "13_PDF_to_Excel_Rule_Extract/output/不同剂量组ADR分析 (TFL).xlsx"
rules:
  - name: "提取规则1"
    search: { keyword: "关键词", page: 1 }
    excel:  { sheet: "Sheet1", cell: "B3" }
```

## 三、干扰区定位（页眉 / 水印排除框）

脚本：`scripts/clinical-automation/21_PDF_Watermark_Removal/main.py`

```bash
cd scripts/clinical-automation/21_PDF_Watermark_Removal
python main.py --input "input" --output "output"
```

产出 `boxes.json`（排除框）、`audit_masked.pdf`（叠加审计图）、清洗后文本。
管线子步骤在 `steps/`（triage → vector → ocr → merge → audit → extract）。

**串联用法**：先用模块 21 生成 `boxes.json`，再把它作为模块 13 的
`--exclusion-json`，可让提取时自动跳过页眉水印区域。

## 输入 / 输出约定
- 输入：各模块 `input/`（不入库）
- 输出：xlsx / json / 审计 PDF 写入各模块 `output/`

## 依赖
`pymupdf`、`pandas`、`openpyxl`、`pdfplumber`；OCR 另需本机 Tesseract

## 注意事项
- 提取结果**必须人工核对**，尤其是数值型字段（GMC、CI、分级）
- 规则驱动提取对 PDF 版式敏感，换来源文档就要重新调规则
- 与 `clinical-pdf-hygiene` 的区别：本技能是**取数据**，那个是**整理与安全**

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
