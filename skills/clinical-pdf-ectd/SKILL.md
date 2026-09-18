---
name: clinical-pdf-ectd
description: Validate, clean and rewrite PDFs for eCTD submission compliance (fonts, bookmarks, links, scripts). Use when the user asks for "eCTD 合规 / eCTD 转换 / PDF 装甲 / 申报 PDF 校验 / 字体嵌入 / 书签修复" or needs a PDF audit report for regulatory submission.
---

# PDF eCTD 合规装甲

## 适用场景
- 需要把 PDF 处理成符合 **eCTD** 申报要求的形式
- 申报前批量校验：字体是否嵌入、书签是否合规、是否含脚本或恶意链接
- 需要一份 Excel 审计报告说明每个文件做了什么

## 脚本位置
`scripts/clinical-automation/18_PDF_eCTD_Converter/pdf_ectd_converter.py`

## 用法
```bash
cd scripts/clinical-automation/18_PDF_eCTD_Converter
python pdf_ectd_converter.py --input "./input" --output "./output" --report "./ectd_report.xlsx" --overwrite
```

常用参数

| 参数 | 说明 |
|---|---|
| `--validate-only` | 只校验不改写，先看问题清单 |
| `--overwrite` | 覆盖已存在的输出 |
| `--keep-name` | 保留原文件名（默认可能改写） |
| `--no-recursive` | 不递归子目录 |
| `--no-keep-structure` | 不保留输入目录层级 |
| `--add-auto-bookmarks` / `--no-add-auto-bookmarks` | 是否自动补全书签（默认 `outline`） |

## 输入 / 输出约定
- 输入：待处理 PDF，放 `18_PDF_eCTD_Converter/input/`（该目录不入库）
- 输出：`*_ectd.pdf` 写入 `output/`，审计报告写入 `--report` 指定路径
- 覆盖条款：6.26 字体映射与嵌入、6.5/6.6/6.8 书签（无动作补全、承前缩放）

## 依赖
`pymupdf`、`pandas`、`openpyxl`、`fonttools`

```bash
pip install -r scripts/clinical-automation/requirements.txt
```

## 注意事项
- `pymupdf < 1.27` 下 `page.delete_link` 行为不一致，建议 `pymupdf >= 1.27.0`
- 与 `clinical-pdf-hygiene` 的分工：本技能面向**申报合规**，那个面向**安全与整理**
- 更详细的参数与条款说明见 `scripts/clinical-automation/18_PDF_eCTD_Converter/README.md`
