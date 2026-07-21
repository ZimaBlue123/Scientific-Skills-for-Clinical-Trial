# scripts/ 审计报告

扫描目录: `E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts`
脚本总数: **35**

## 按类别汇总

| 类别 | 数量 |
|---|---:|
| docx_convert | 5 |
| docx_dsur | 2 |
| docx_extract | 7 |
| docx_generate | 10 |
| lit_search | 2 |
| maintenance | 5 |
| other | 2 |
| xlsx | 2 |

## 全部脚本详情

| # | 路径 | 大小 (字节) | 类别 | 首行 docstring |
|---|---|---:|---|---|
| 1 | `scripts\_extract_docx_text.py` | 5477 | docx_extract | Extract plain text and tables from a .docx without external deps. |
| 2 | `scripts\_selftest_cleanup.py` | 8343 | maintenance | Self-test for ``cleanup_generated_artifacts.py``. |
| 3 | `scripts\_selftest_ide_history.py` | 11983 | maintenance | Self-test for ``cleanup_generated_artifacts.py ide-history``. |
| 4 | `scripts\audit_dsur.py` | 5958 | docx_dsur | Audit DSUR document: extract full text + tables from three documents for cross-r |
| 5 | `scripts\build_tvax006_IMA_v2_docx.py` | 25350 | docx_generate | Merge TVAX-006_海外桥接法规清单_IMA_V2.md + IMA.docx URLs → TVAX-006_海外桥接法规清单_IMA_V2.doc |
| 6 | `scripts\cansino_detail4843_manual_docx.py` | 18141 | docx_generate | Download 康希诺官网 detail-4843 公示中的「说明书」两页（JPG），生成横版 Word。 |
| 7 | `scripts\cleanup_generated_artifacts.py` | 31324 | maintenance | Clean up generated/reproducible artifacts created by the project's |
| 8 | `scripts\common_scripts\build_bridge_docs_v2.py` | 15043 | other | Generate overseas bridging study Word + PPT deliverables (V2). |
| 9 | `scripts\common_scripts\docx_utils.py` | 2950 | other | Common utilities for docx generation scripts. |
| 10 | `scripts\convert_audit_report_md_to_docx.py` | 1020 | docx_convert | (无docstring) |
| 11 | `scripts\convert_doc_to_docx.py` | 1197 | docx_convert | Convert old .doc to .docx format |
| 12 | `scripts\convert_to_md.py` | 13743 | docx_convert | Unified document converter: Convert docx/pdf/rtf/doc to markdown. |
| 13 | `scripts\diagnose_docx.py` | 2680 | docx_extract | Diagnose DOCX structure to understand paragraph styles and content mapping. |
| 14 | `scripts\dsur_transfer_v7.py` | 17305 | docx_dsur | DSUR Content Transfer v7 - FINAL. |
| 15 | `scripts\extract_doc_text.py` | 5439 | docx_extract | Extract plain text from legacy Microsoft Word `.doc` files via the |
| 16 | `scripts\extract_docx_full.py` | 6080 | docx_extract | Extract text from .docx / .doc files. |
| 17 | `scripts\extract_docx_to_md.py` | 4447 | docx_extract | (无docstring) |
| 18 | `scripts\extract_ib_texts.py` | 10063 | docx_extract | Extract text from Chinese and English IB (Investigator's Brochure) docx files |
| 19 | `scripts\extract_tables_to_docx.py` | 34708 | docx_extract | 图片 / 截图 → Word：通用 OCR + 表格流水线（不绑定某一产品说明）。 |
| 20 | `scripts\extract_xlsx_full.py` | 10862 | xlsx | Extract text/content from .xlsx files (UTF-8, robust). |
| 21 | `scripts\generate_audit_report_docx.py` | 16948 | docx_generate | (无docstring) |
| 22 | `scripts\generate_clinical_doc_audit_report.py` | 8299 | docx_generate | Clinical Document Audit Report Generator |
| 23 | `scripts\generate_clinical_overview_doc_review_docx.py` | 16310 | docx_generate | Generate Word review report for CTD 2.5 clinical overview document. |
| 24 | `scripts\generate_csr_docx.py` | 32231 | docx_generate | (无docstring) |
| 25 | `scripts\generate_mmr_audit_report.py` | 21079 | docx_generate | Medical Monitoring Report (MMR) Audit Report Generator. |
| 26 | `scripts\generate_norovirus_review_docx.py` | 11937 | docx_generate | (无docstring) |
| 27 | `scripts\generate_norovirus_trial_lit_docx.py` | 17527 | docx_generate | 生成 HilleVax 诺如疫苗 HIL-214 相关 PubMed 文献检索结果 Word 文档。 |
| 28 | `scripts\generate_phase_summary_doc_review_docx.py` | 13244 | docx_generate | Generate Word review report for phase CSR interim summary document. |
| 29 | `scripts\make_safe_md_copies.py` | 5081 | docx_convert | Build sanitized copies of every ``*.md`` file under a source folder. |
| 30 | `scripts\md_to_docx.py` | 4342 | docx_convert | (无docstring) |
| 31 | `scripts\norovirus_trial_search.py` | 7177 | lit_search | HilleVax 诺如疫苗相关III期试验的PubMed文献检索。 |
| 32 | `scripts\project_self_check.py` | 10376 | maintenance | Project self-check: |
| 33 | `scripts\pubmed_lit_search.py` | 5913 | lit_search | DSUR §13 Literature search: |
| 34 | `scripts\review_clinical_xlsx.py` | 14567 | xlsx | review_clinical_xlsx.py |
| 35 | `scripts\skill_dedupe_report.py` | 6717 | maintenance | (无docstring) |