---
name: document-format-convert
description: Convert documents between formats - PPT/PPTX to PDF, Word to PDF, PDF to PPT, PDF/PPTX back to editable native PPT, merge PDFs, and merge images into PDF. Use when the user asks for "PPT 转 PDF / Word 转 PDF / PDF 转 PPT / 图片 转 PDF / PDF 合并 / 格式转换 / 批量导出 PDF".
---

# 文档格式互转

各模块彼此独立，按需调用。

| 转换 | 脚本 | 运行方式 |
|---|---|---|
| PPT → PDF | `scripts/clinical-automation/05_PPT_to_PDF/ppt_to_pdf.py` | 需 Windows + PowerPoint |
| Word → PDF | `scripts/clinical-automation/06_Word_to_PDF/word_to_pdf.py` | 需 Windows + Word + pywin32 |
| PDF → PPT | `scripts/clinical-automation/14_PDF_to_PPT/pdf_to_ppt.py` | 每页 PDF 转一张幻灯片 |
| PDF/PPTX → 可编辑 PPT | `scripts/clinical-automation/16_PPTX_PDF_to_PPT/convert_to_native_ppt.py` | 表格识别重建，需 PaddleOCR |
| PDF 合并 | `scripts/clinical-automation/19_PDF_Merge/merge_pdf.py` | 自然排序，支持子目录 |
| 图片 → PDF | `scripts/clinical-automation/34_Image_to_PDF/image_to_pdf.py` | 支持 jpg/png/bmp/webp/tiff |

## 常用示例

```bash
# PPT 批量转 PDF（Windows + PowerPoint）
cd scripts/clinical-automation/05_PPT_to_PDF
python ppt_to_pdf.py --input "input" --output "output" --overwrite

# Word 批量转 PDF（Windows + Word）
cd scripts/clinical-automation/06_Word_to_PDF
python word_to_pdf.py --recursive --overwrite

# 合并 PDF（自然排序）
cd scripts/clinical-automation/19_PDF_Merge
python merge_pdf.py --output-name "merged.pdf" --overwrite

# 图片转 PDF：--merge 合并为一个多页 PDF，不加则每张图一个 PDF
cd scripts/clinical-automation/34_Image_to_PDF
python image_to_pdf.py --merge

# PDF/PPTX 还原为可编辑 PPT（表格重建）
cd scripts/clinical-automation/16_PPTX_PDF_to_PPT
python convert_to_native_ppt.py --dpi 300 --lang ch
```

## 输入 / 输出约定
- 输入：各模块 `input/`（不入库）
- 输出：各模块 `output/`

## 依赖
- 通用：`pymupdf`、`python-pptx`、`Pillow`
- Office 自动化（05/06）：`pywin32` + **本机安装 Microsoft Office**，仅 Windows
- 模块 16：`paddleocr` + `paddlepaddle`（体积大，macOS 无官方 wheel，可按需注释掉）

## 注意事项
- 依赖 Office COM 的两个模块（05、06）**只能在本机有 Office 的 Windows 上跑**，
  且运行时不要手动操作 Word / PowerPoint 窗口
- 模块 16 是 OCR 重建，属于**尽力而为**的转换，表格复杂时务必人工核对
- 若目标是 eCTD 申报合规，转换后请用 `clinical-pdf-ectd` 再处理一遍
