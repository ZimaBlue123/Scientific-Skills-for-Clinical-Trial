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
| `extract_xlsx_full.py` | 通用 .xlsx 容错文本提取（zipfile+xml，兼容 openpyxl 无法读取的工作簿） | stdlib |
| `review_clinical_xlsx.py` | 临床试验 Excel 数据质量审核（遍历、矛盾扫描、错别字检测、报告输出） | openpyxl |
| `project_self_check.py`   | 项目自检：外部命令可用性 + Python 脚本冒烟测试 | stdlib |
| `extract_docx_full.py`    | 通用 .docx/.doc 文本提取 | python-docx |
| `extract_docx_to_md.py`   | .docx → Markdown（含表格） | python-docx |
| `extract_doc_text.py`     | 旧版 .doc (二进制) 文本提取 | olefile |
| `extract_ib_texts.py`     | 中英文 IB（研究者手册）提取 | python-docx |
| `extract_tables_to_docx.py` | OCR + 表格流水线（图片 → Word） | pytesseract, opencv |
| `convert_to_md.py`        | docx/pdf/rtf/doc 统一转 Markdown | 多种 |
| `convert_doc_to_docx.py`  | 旧版 .doc → .docx | subprocess(libreoffice) |
| `md_to_docx.py`           | Markdown → .docx | python-docx |
| `convert_audit_report_md_to_docx.py` | 审核报告 MD → DOCX | python-docx |
| `make_safe_md_copies.py`  | 生成 .md 文件的安全副本（去敏感信息） | stdlib |
| `generate_audit_report_docx.py` | 生成审核报告 Word | python-docx |
| `generate_clinical_doc_audit_report.py` | 临床文档审核报告 | python-docx |
| `generate_mmr_audit_report.py` | 医学监查报告（MMR）审核：Word+EDC 交叉核对 → Word 报告 | python-docx |
| `generate_clinical_overview_doc_review_docx.py` | CTD 2.5 临床总览审阅 | python-docx |
| `generate_phase_summary_doc_review_docx.py` | 期中 CSR 摘要审阅 | python-docx |
| `generate_norovirus_review_docx.py` | 诺如病毒专项审阅 | python-docx |
| `generate_csr_docx.py`    | 生成 CSR 文档 | python-docx |
| `build_tvax006_IMA_v2_docx.py` | TVAX-006 IMA v2 桥接文档 | python-docx |
| `cansino_detail4843_manual_docx.py` | 康希诺说明书下载 + 横版排版 | pillow, requests |
| `cleanup_generated_artifacts.py` | 清理 generated/ 等可重建产物 | stdlib |
| `skill_dedupe_report.py`  | skills 去重报告 | stdlib |

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
