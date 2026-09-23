# scripts/

仓库级可执行脚本入口。

## 目录组织

```
scripts/
├── common_scripts/         # 共享库（docx_utils 等）
├── _tools/                 # 内部审计/自检辅助脚本
├── _archive/               # 已归档的历史单次任务脚本（不提交）
├── _archive_2026_consolidation/ # 2026 年大整合归档（不提交）
├── *.py                    # 活跃核心脚本（见下表）
├── *.cmd / *.ps1           # Windows 辅助脚本
└── README.md               # 本文件
```

## 活跃脚本清单

| 脚本 | 功能 | 主要依赖 |
|------|------|----------|
| `extract_office_utils.py` | 统一 Office 文档提取（DOCX/DOC/PPTX/XLSX，含容错 XML 提取） | python-docx, python-pptx, openpyxl |
| `edit_office_utils.py` | Office 文档编辑工具（段落遍历、Run 创建、单元格操作） | python-docx |
| `extract_ib_texts.py` | IB（研究者手册）结构化文本提取 | python-docx |
| `extract_tables_to_docx.py` | OCR + 表格流水线（图片 → Word） | pytesseract, img2table, Pillow |
| `convert_to_md.py` | docx/pdf/rtf/doc 统一转 Markdown | python-docx, pypdf, pdfplumber, striprtf, markitdown |
| `make_safe_md_copies.py` | 生成 .md 文件的安全副本（去敏感信息） | stdlib |
| `project_self_check.py` | 项目自检：外部命令可用性 + Python 脚本冒烟测试 | stdlib |
| `cleanup_generated_artifacts.py` | 清理 generated/ 与历史状态等可重建产物 | stdlib |
| `skill_dedupe_report.py` | skills 去重报告 | stdlib |
| `pubmed_search_tool.py` | PubMed 文献检索（NCBI E-utilities） | stdlib (urllib) |

## 辅助脚本

| 脚本 | 功能 |
|------|------|
| `on_open_cleanup.cmd` | 开机/打开项目时自动清理 |
| `register_cleanup_logon_task.ps1` | 注册 Windows 开机自启清理任务 |
| `sync_skills_to_global.ps1` | Windows skills 同步至全局目录 |

## 用法

```bash
# 提取 .xlsx（含容错）
python scripts/extract_office_utils.py review_materials/ -o dump.txt

# 转换 Word 为 Markdown
python scripts/pipeline/convert/convert_to_md.py input.docx -o output.md

# OCR 图片表格 → Word
python scripts/extract_tables_to_docx.py input.png -o output.docx

# 项目自检
python scripts/_tools/project_self_check.py

# PubMed 检索
python scripts/pubmed_search_tool.py --query '"hepatitis B vaccine"[tiab]' --out result.json
```

## 约定

- Python ≥ 3.10，使用 `from __future__ import annotations`
- 第三方依赖必须显式声明 import 错误提示
- 不在仓库级产生可重建 artifacts（已通过 `.gitignore` 过滤）
- 已归档的历史脚本保存在 `_archive/` 下，仅作参考，不纳入版本追踪

## 关键脚本说明

### extract_office_utils.py

统一入口：DOCX 纯文本 / Markdown 提取、PPTX 全量提取（含表格/组合形状/备注）、
XLSX zip+xml 解析（绕开 openpyxl 的严格 autoFilter ref 校验）。

部分国内 EDC 系统（如太美、太保、同心等）导出的 .xlsx 含历史遗留的非规范 XML，
会导致 openpyxl 直接抛 `ValueError`。本脚本使用 zipfile + xml.etree 直接解析，
稳健地提取所有文本内容。
