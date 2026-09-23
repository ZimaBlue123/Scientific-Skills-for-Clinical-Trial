---
name: clinical-word-tables
description: Export Word document tables to Excel, replicate Word tables into Excel chart ranges, and substitute antibody immunogenicity data into GraphPad Prism (.pzfx) templates. Use when the user asks for "Word 表格导出 / 表格转 Excel / 临床小结 表格提取 / Graphpad pzfx / 抗体数据替换 / GMC GMI 阳转率 填入".
license: MIT
compatibility: Requires Python 3.10+ with python-docx, openpyxl and pandas. Module 07 additionally needs pywin32 and a local Microsoft Word installation (Windows only).
allowed-tools: Read Write Edit Bash
metadata:
  version: "1.0"
  skill-author: Scientific Skills for Clinical Trial Contributors
  last-reviewed: "2026-09-18"
---

# Word 表格 → Excel / GraphPad

本技能聚合三个相邻模块，按任务选择对应脚本。

## 一、Word 表格导出到 Excel（最常用）

脚本：`scripts/clinical-automation/09_Word_Tables_to_Excel/`

```bash
cd scripts/clinical-automation/09_Word_Tables_to_Excel
python word_all_tables_to_excel.py                                  # 批量导出全部顶层表格
python word_tables_to_excel.py --input X.docx --table-indices 1,3   # 只导出指定表
```

定位参数：`--table-title`、`--table-index` / `--table-indices`、`--header-keywords`、
`--merge-tables-from` / `--merge-tables-to`
辅助参数：`--list-word-tables`（先列出有哪些表）、`--header-rows`、`--dry-run`、`--skip-existing`

## 二、抗体数据替换进 GraphPad pzfx 模板

脚本：`scripts/clinical-automation/08_Word_Tables_to_Graphpad/`

用途：把 docx 中「源抗体」的免疫原性数据（GMC / GMI / 阳转率 × 4 年龄段 × 3 时间点 × 2 组别）
替换到 pzfx 模板，生成目标抗体的新 pzfx。典型场景：gE 抗体 → VZV 抗体。

```bash
cd scripts/clinical-automation/08_Word_Tables_to_Graphpad
python util_probe.py --docx input/source.docx --pzfx input/template.pzfx --out output/_probe_report.md
python poc_replicate.py --docx input/source.docx --pzfx input/template.pzfx --source-antibody gE --target-antibody VZV --out output/result.pzfx -v
```

> 先跑 `util_probe.py` 生成探查报告，确认表名与列名对得上，再跑替换。
> 替换只改 `<d>` 数值，表名 / 列名 / Subcolumn 顺序不变。

## 三、Word → Excel 图表区间高保真复刻

脚本：`scripts/clinical-automation/07_Word_to_Excel_to_Figure/`

需要 **Windows + Microsoft Word + pywin32**。

```bash
cd scripts/clinical-automation/07_Word_to_Excel_to_Figure
python word_to_excel_to_figure.py --input-dir "input" --plan-only
python word_to_excel_to_figure.py --input-dir "input" --table-map-json "output/table_mapping_plan_<模板名>.json"
```

两步走：先 `--plan-only` 生成映射计划，人工确认后再带 `--table-map-json` 执行。
子表映射唯一实现在 `lib/table_mapping_logic.py`。

## 输入 / 输出约定
- 输入：各模块自己的 `input/`（不入库）
- 输出：xlsx / pzfx 写入各自 `output/`

## 依赖
`python-docx`、`openpyxl`、`pandas`；模块 07 另需 `pywin32` 与本机 Word

## 注意事项
- 表格定位依赖**表题 / 表头关键词**，不同文档的写法差异会直接影响命中率，
  建议先用 `--list-word-tables` 或 `--dry-run` 核对
- 模块 08 的 `.pzfx` 是 GraphPad Prism 的 XML 格式，替换后请用 Prism 打开验证一次

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
