---
name: clinical-pdf-hygiene
description: Clean and organize PDF libraries - strip JavaScript and malicious links, rename papers by extracted title and year, detect duplicate PDFs across folders, and scan for PDF threats. Use when the user asks for "PDF 重命名 / 文献 按标题 命名 / PDF 去重 / 重复 PDF / PDF XSS / PDF 安全 扫描 / 恶意链接 清理".
---

# PDF 整理与安全

四个独立工具，按需求单独调用，彼此无依赖。

## 一、标题驱动重命名

脚本：`scripts/clinical-automation/17_PDF_Title_Renamer/pdf_sanitizer.py`

从 PDF 首页提取**正文标题**与**年份**，生成 `标题-年份.pdf`。

```bash
cd scripts/clinical-automation/17_PDF_Title_Renamer
python pdf_sanitizer.py
```

参数：`--input`、`--output`、`--no-recursive`、`--no-keep-structure`、`--overwrite`

提取链路：视觉字号层级 → 学术首屏多行合并 → 元数据/首行 → OCR 后备。
噪声过滤已覆盖期刊页眉（PLOS / Elsevier）、`RESEARCH ARTICLE`、`ARTICLE IN PRESS`、
`Please cite this article…`、卷期页眉、纯作者姓行等。

> ⚠️ **执行后 `input/` 中的 PDF 会被剪切到 `output/`，请先备份。**

## 二、跨文件夹重复检测

脚本：`scripts/clinical-automation/22_PDF_Duplicate_Analyzer/pdf_duplicate_analyzer.py`

按**文件名**或**首页文本**检测重复 PDF（无 `input/`，源文件在外部路径）。

```bash
cd scripts/clinical-automation/22_PDF_Duplicate_Analyzer
python pdf_duplicate_analyzer.py --root "D:\References" --folders "FolderA,FolderB" --label "批次1"
python pdf_duplicate_analyzer.py --config jobs.json
```

## 三、XSS / 脚本清理

脚本：`scripts/clinical-automation/15_PDF_XSS/pdf_xss_clean.py`

清理 PDF 中的脚本、恶意协议链接、注释与嵌入文件。

```bash
cd scripts/clinical-automation/15_PDF_XSS
python pdf_xss_clean.py
```

## 四、威胁分析与剥离

脚本：`scripts/clinical-automation/23_PDF_Threat_Analyzer/pdf_threat_analyzer.py`

静态扫描 + 风险评分 + 可选 sanitize，输出 `threat_report_*.json` 与 `*_sanitized.pdf`。
对 ≥ 1MB 文件自动启用 mmap 加速。

```bash
cd scripts/clinical-automation/23_PDF_Threat_Analyzer
python pdf_threat_analyzer.py
```

> 加密 PDF 处理依赖 `pypdf >= 6.0`。

## 输入 / 输出约定
- 除模块 22（用 `--root` 指向外部路径）外，其余均为 `input/` → `output/`
- 模块 22 输出：`duplicate_report_*.txt`

## 依赖
`pymupdf`（>= 1.27.0 推荐）、`pypdf`（>= 6.0）、`pytesseract`（模块 17 的 OCR 后备，可选）

## 注意事项
- 模块 17 是**剪切**而非复制，务必先备份
- 与 `clinical-pdf-ectd` 的区别：本技能面向**日常整理与安全**，那个面向**申报合规**
- 与 `clinical-pdf-extraction` 的区别：本技能不取数据
