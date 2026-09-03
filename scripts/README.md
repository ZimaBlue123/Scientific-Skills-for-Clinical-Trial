# scripts/

仓库级可执行脚本入口。

## 目录组织

```
scripts/
├── common_scripts/         # 共享库（docx 工具）
├── common_templates/       # 共享模板
├── *.py                    # 独立脚本（见下表）
└── sync_skills_to_global.ps1  # Windows skills 同步
```

## 脚本清单

| 脚本 | 功能 | 主要依赖 |
|------|------|---------|
| `extract_office_utils.py` | 统一 Office 文档提取（DOCX/DOC/PPTX/XLSX，含容错 XML 提取） | python-docx, python-pptx, openpyxl |
| `review_clinical_xlsx.py` | 临床试验 Excel 数据质量审核（遍历、矛盾扫描、错别字检测、报告输出） | openpyxl |
| `project_self_check.py`   | 项目自检：外部命令可用性 + Python 脚本冒烟测试 | stdlib |
| `convert_to_md.py`        | docx/pdf/rtf/doc 统一转 Markdown | 多种 |
| `extract_tables_to_docx.py` | OCR + 表格流水线（图片 → Word） | pytesseract, opencv, img2table |
| `make_safe_md_copies.py`  | 生成 .md 文件的安全副本（去敏感信息） | stdlib |
| `generate_audit_report_docx.py` | 生成审核报告 Word | python-docx |
| `generate_clinical_doc_audit_report.py` | 临床文档审核报告通用模板 | python-docx |
| `generate_mmr_audit_report.py` | 医学监查报告（MMR）审核：Word+EDC 交叉核对 → Word 报告 | python-docx |
| `generate_clinical_overview_doc_review_docx.py` | CTD 2.5 临床总览审阅报告 | python-docx |
| `generate_phase_summary_doc_review_docx.py` | 期中 CSR 摘要审阅报告 | python-docx |
| `generate_norovirus_review_docx.py` | 诺如病毒流行病学综述生成 | python-docx |
| `generate_csr_docx.py`    | 生成 II 期临床总结报告 CSR | python-docx, pymupdf |
| `cansino_detail4843_manual_docx.py` | 康希诺说明书下载 + 横版排版 | pillow, img2table |
| `cleanup_generated_artifacts.py` | 清理 generated/ 与历史状态等可重建产物 | stdlib |
| `skill_dedupe_report.py`  | skills 去重报告 | stdlib |
| `compute_diabetes_immuno.py` | TVAX-009 糖尿病亚组免疫原性聚合与计算 (FAS/PPS) | python-docx, stdlib |
| `generate_diabetes_immuno_word.py` | TVAX-009 糖尿病亚组 Word 表格生成器（支持 --pps-only） | python-docx |
| `generate_diabetes_6slides_standalone.py` | TVAX-009 糖尿病亚组 6 页独立 PPT 生成器 | python-pptx, lxml |
| `generate_diabetes_4slides_pps_16x9.py` | TVAX-009 糖尿病亚组 4 页宽屏 PPT 生成器 (PPS) | python-pptx, lxml |
| `verify_diabetes_slides.py` | 糖尿病亚组幻灯片与 JSON 数据对齐校验 | python-pptx |
| `update_data_final.py`    | CpG 疫苗安全性汇总基础数据字典 (V29 数据集) | stdlib |
| `generate_updated_files_final.py` | CpG 疫苗安全性汇总 PPTX/DOCX 产出与超链接渲染 | python-docx, python-pptx |
| `duplicate_pptx_win32_final.py` | CpG 疫苗安全性汇总 PPTX 结构骨架复制 | win32com |
| `verify_output_final.py`  | CpG 疫苗安全性交付物结构与链接完整性自检 | python-docx, python-pptx |

## 用法

```bash
# 提取 .xlsx（含容错）
python scripts/extract_xlsx_full.py review_materials/ -o dump.txt

# 生成 MMR 审核报告（自动选定目录内的 Word + Excel）
python scripts/generate_mmr_audit_report.py --folder review_materials/ \
    --project "TVAX-020 II期"

# 审核临床 Excel
python scripts/review_clinical_xlsx.py <excel_path>

# 项目自检
python scripts/project_self_check.py

# 提取 Word 文本
python scripts/extract_docx_full.py <docx_path>
```

## 约定

- 脚本头部使用 `# -*- coding: utf-8 -*-` 声明编码
- Python ≥ 3.10，使用 `from __future__ import annotations`
- 第三方依赖必须显式声明 import 错误提示
- 不在仓库级产生可重建 artifacts（已通过 `.gitignore` 过滤）

## 关键脚本说明

### extract_xlsx_full.py

与 `extract_docx_full.py` 风格对齐，使用 zipfile + xml.etree 解析 .xlsx 文件，
**绕开 openpyxl 的严格 autoFilter ref 校验**。部分国内 EDC 系统（如太美、太保、同心
等）导出的 .xlsx 含历史遗留的非规范 XML，会导致 openpyxl 直接抛
`ValueError: Value does not match pattern ^[$]?([A-Za-z]{1,3})...$`。

输出格式：每个 sheet 以 78 个 `#` 分隔，行以 `R{nnnn}: cell1 | cell2 | ...` 表示。

### generate_mmr_audit_report.py

医学监查报告（MMR）端到端审核流水线：

1. 调用 `extract_xlsx_full.py` 提取 EDC Excel
2. 调用 `extract_docx_full.py` 等价逻辑提取 MMR Word
3. 运行错别字/术语统一性扫描 + 数据交叉核对
4. 复用 `common_scripts.docx_utils.apply_cn_en_fonts` 字体规范输出 Word 报告

支持以下发现类别：

- 错别字（P0）："足三里交" → "足三里穴"；"肌内滴注" → "肌内注射"
- 术语：试验疫苗 vs 试验用疫苗；受试者 vs 试验参与者；医学监查 vs 医学核查
- 格式：罗马数字 II/Ⅱ 不统一；连续句号
- 数据矛盾：筛选失败数、方案偏离数与 EDC 实际行数差异
- 数据完整性：AE 表 155 行关键字段为空、EX 表 EXSTDTC 大量为空
- 分析补充：年龄层 AE 发生率递减趋势
