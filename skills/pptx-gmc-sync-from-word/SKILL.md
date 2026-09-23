---
name: pptx-gmc-sync-from-word
description: >-
  Sync PowerPoint immunogenicity tables from a source Word CSR/report using raw GMC
  (not adjusted/corrected GMC), sample sizes, and P-values. Cross-check PPS vs FAS
  sources, update specified slides, and export landscape Word tables for copy-paste.
  Use when updating PPT tables from Word, replacing 校正GMC with GMC, fixing PPS/FAS
  mix-ups, or exporting slide tables to Word.
metadata:
  version: "1.0.0"
---

# PPTX GMC 同步（Word → PPT）

## 目标

根据源 Word（CSR/阶段性报告）中的 **GMC（非校正 GMC）**、**例数（n）**、**P 值**，更新目标 PPT 指定页表格，并可导出横版 Word 便于复制回 PPT。

## 何时使用

- PPT 表格写的是「校正 GMC」，需改为 Word 中的 **GMC**
- 需要同步 **例数（n）**、**组间比较 P 值**
- 用户指定修改 PPT **第 1、2、4 页**
- 必须避免 **PPS 与 FAS 串用**（例如：第 1 页 M4 / 全免后 2 个月把 PPS 误写成 FAS）

## 脚本入口（可手动调用）

```bash
python ...\\pptx-gmc-sync-from-word\\scripts\\sync_pptx_from_word.py --word <docx> --ppt <pptx>
python ...\\pptx-gmc-sync-from-word\\scripts\\export_ppt_tables_to_word.py --ppt <pptx> --out <docx> --slides 1,2,4
```

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
