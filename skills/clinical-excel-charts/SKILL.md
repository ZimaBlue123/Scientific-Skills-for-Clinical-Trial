---
name: clinical-excel-charts
description: Generate clinical Excel charts and fill immunogenicity tables (GMC, GMI, seroconversion rate), or recolor existing TFL charts with journal-ready clinical palettes. Use when the user asks for "Excel 图表 生成 / 临床配色 / TFL 配色 / 期刊配色 / GMC GMI 填表 / 阳转率 汇总 / ADR 组合图".
---

# 临床 Excel 图表与配色

## 一、临床表格数据填充（统一入口：GMC / GMI / 阳转率）

脚本：`scripts/clinical-automation/01_Excel_Charts/fill_clinical_table.py`

```bash
cd scripts/clinical-automation/01_Excel_Charts
python fill_clinical_table.py input/TVAX-006.xlsx                 # 自动检测全部支持子表
python fill_clinical_table.py input/TVAX-006.xlsx --type gmc      # 仅 GMC
python fill_clinical_table.py input/TVAX-006.xlsx --type gmi      # 仅 GMI
python fill_clinical_table.py input/TVAX-006.xlsx --sheets "总体GMC,40-59岁GMC"
```

- GMC / GMI 从详细统计表（`LS GMC/GMI 95%CI` 格式，如 `768.17(507.87, 1161.89)`）自动解析并填入
- 阳转率自动扫描定位「阳转例数（阳转率）」和「95%CI」行
- GMI 自动适配不同行号结构

参数：`--type`、`--sheets`、`--output-dir`、`--verbose`

## 二、图表生成

```bash
cd scripts/clinical-automation/01_Excel_Charts
python build_charts_xlsxwriter.py     # 推荐：支持持续时间 + 临床配色
python build_charts_openpyxl.py       # 备用引擎
```

> 生成 ADR 组合图（柱 + 线）。**优先用 XlsxWriter 引擎**，可避免 openpyxl 的 XML 结构问题。
> Excel 图表生成会自动备份旧文件（`.bak.xlsx`）。

## 三、期刊 / 临床配色重绘

脚本：`scripts/clinical-automation/02_Excel_Chart_Colors/apply_clinical_colors.py`

不改原始 TFL 的前提下，对现有图表应用配色预设（NPG、Lancet、NEJM 等）。

```bash
cd scripts/clinical-automation/02_Excel_Chart_Colors
python apply_clinical_colors.py --palette Lancet --n-colors 3
python apply_clinical_colors.py --batch --input "input" --output "output"
```

配色主题统一在 `scripts/clinical-automation/src/color_theme.py`
（`get_series_color` 等），改配色改这里。

## 输入 / 输出约定
- 输入：各模块 `input/`（不入库）
- 输出：xlsx 写入各模块 `output/`

## 依赖
`openpyxl`、`XlsxWriter`、`pandas`

## 注意事项
- **涨用红、跌用绿**（中国区惯例），配色预设已按此约定，不要反向套用欧美配色
- `--palette` 支持多期刊预设，投稿前确认目标期刊的具体要求
