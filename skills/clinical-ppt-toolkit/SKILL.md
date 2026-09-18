---
name: clinical-ppt-toolkit
description: Merge and deduplicate multiple PowerPoint decks into a CSR-structured narrative, and remove corner logo watermarks from image-only slides. Use when the user asks for "PPT 合并 / 去重 / 叙事 重组 / CSR 结构 PPT / 边角 logo 去除 / 水印 去除 PPT".
---

# 临床 PPT 整合

## 一、多 PPT 去重合并与叙事重组

脚本目录：`scripts/clinical-automation/03_PPT_Merge/`

```bash
cd scripts/clinical-automation/03_PPT_Merge
python merge_ppt.py      # 物理合并，TF-IDF 去重
python ppt_engine.py     # 叙事编排，按 CSR 结构重组
```

**推荐顺序**：先 `merge_ppt.py` 做基础合并去重，再 `ppt_engine.py` 做叙事重组。
另有 `csr_ppt_integrator.py`（叙事 + 去重 + 视觉统一三合一）与
`util_test_and_validate.py`（依赖与流程自检）。

输出：`merge_report.xlsx`、`narrative_report.xlsx`，写入 `output/`。

## 二、边角水印 / 重复 logo 去除

脚本：`scripts/clinical-automation/04_PPT_Watermark_Removal/pptx_corner_logo_patch.py`

仅处理**图片型页面**右下角的重复 logo；可编辑页面会自动跳过。

```bash
cd scripts/clinical-automation/04_PPT_Watermark_Removal
python pptx_corner_logo_patch.py
python pptx_corner_logo_patch.py "input/your.pptx" -o "output/your_clean.pptx"
```

## 输入 / 输出约定
- 输入：各模块 `input/`（不入库）
- 输出：合并后 PPTX 与报告写入 `output/`

## 依赖
`python-pptx`、`scikit-learn`（`merge_ppt.py` 的 TF-IDF 去重）

## 注意事项
- 合并结果**必须人工逐页复核**，TF-IDF 去重是相似度判定，可能误判内容相近但需保留的页
- 叙事编排依赖 `SLIDE_BLUEPRINT` 配置，换项目时需要按新 CSR 结构调整
- 若需要处理 PPT 里的图表配色或导出 PDF，见 `document-format-convert`
