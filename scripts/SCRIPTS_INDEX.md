# Global Scripts Capability & Reuse Index (`SCRIPTS_INDEX.md`)

> **Pre-Flight Reuse Mandate (`AGENTS.md` §4)**: Before writing any new script, search this index or run:
> ```bash
> python scripts/_tools/generate_scripts_index.py --search <keyword>
> ```
> Always import or invoke existing modules in `scripts/pipeline/` or `scripts/_tools/` instead of reinventing the wheel.

## 1. Core Modular Pipeline (`scripts/pipeline/`)

| Stage | Script Path | CLI | Public API / Exports | Capability Summary |
|-------|-------------|:---:|----------------------|--------------------|
| `pipeline/convert` | [`convert_doc_to_docx.py`](pipeline/convert/convert_doc_to_docx.py) | Yes | `convert_doc_to_docx` | Convert legacy binary .doc files to .docx using Microsoft Word COM. |
| `pipeline/convert` | [`convert_to_md.py`](pipeline/convert/convert_to_md.py) | Yes | `table_to_md`, `iter_block_items`, `docx_to_md_numbered`, `convert_file`, `convert_folder` | Unified document converter: Convert docx/pdf/rtf/doc to markdown. |
| `pipeline/core` | [`document_facade.py`](pipeline/document_facade.py) | Lib | `UnifiedDocument` | Unified Document Facade (Inspired by Univer Architecture). |
| `pipeline/export` | [`apply_audit_fonts.py`](pipeline/export/apply_audit_fonts.py) | Yes | `apply_audit_fonts` | 为审计报告 docx 全局应用宋体/Times New Roman 中英文字体。 |
| `pipeline/export` | [`docx_builder.py`](pipeline/export/docx_builder.py) | Lib | `apply_cn_en_fonts`, `create_clinical_docx` | DOCX export utilities. |
| `pipeline/export` | [`make_slide_before_after.py`](pipeline/export/make_slide_before_after.py) | Yes | `render`, `load_font` | 把两份 PPTX 的同一页渲染成上下对照图（可指定裁切区域），便于目视 diff。 |
| `pipeline/export` | [`nativize_pptx.py`](pipeline/export/nativize_pptx.py) | Yes | `nativize` | Normalize a python-pptx output by round-tripping it through PowerPoint COM. |
| `pipeline/export` | [`pptx_builder.py`](pipeline/export/pptx_builder.py) | Lib | `create_slide`, `inject_pptx_data` | PPTX export utilities. |
| `pipeline/export` | [`render_pptx_slides.py`](pipeline/export/render_pptx_slides.py) | Yes | `render` | Render selected slides of a PPTX to PNG via PowerPoint COM. |
| `pipeline/export` | [`update_docx_toc_fields.py`](pipeline/export/update_docx_toc_fields.py) | Yes | `update_docx_toc_fields` | Update Word (.docx) Table of Contents (TOC) and page number fields via Word COM. |
| `pipeline/extract` | [`extract_docx_review_comments.py`](pipeline/extract/extract_docx_review_comments.py) | Yes | `para_text`, `comment_body`, `load`, `extract_comments` | Extract Word comments (with anchoring text) and body paragraphs from a .docx. |
| `pipeline/extract` | [`extract_docx_tracked_text.py`](pipeline/extract/extract_docx_tracked_text.py) | Yes | `para_text`, `iter_block_text`, `extract_tracked_docx` | Extract text and tables from .docx using stdlib only (honoring tracked changes). |
| `pipeline/extract` | [`extract_legacy_doc_text.py`](pipeline/extract/extract_legacy_doc_text.py) | Yes | `extract_one_doc`, `extract_legacy_docs` | Extract plain text and table text from legacy binary .doc files via Word COM. |
| `pipeline/extract` | [`table_extractor.py`](pipeline/extract/table_extractor.py) | Lib | `find_tables_by_heading`, `parse_table_columns` | Table extraction utilities. |
| `pipeline/extract` | [`text_normalizer.py`](pipeline/extract/text_normalizer.py) | Lib | `detect_encoding`, `fix_mojibake`, `normalize_whitespace` | Text normalization and encoding diagnostics. |
| `pipeline/ingest` | [`docx_reader.py`](pipeline/ingest/docx_reader.py) | Lib | `extract_docx_text`, `extract_docx_tables` | DOCX extraction module. |
| `pipeline/ingest` | [`pdf_reader.py`](pipeline/ingest/pdf_reader.py) | Lib | `extract_pdf_text`, `extract_pdf_tables` | PDF extraction module. |
| `pipeline/ingest` | [`pptx_reader.py`](pipeline/ingest/pptx_reader.py) | Lib | `extract_pptx_text`, `extract_pptx_notes` | PPTX extraction module. |
| `pipeline/ingest` | [`rtf_reader.py`](pipeline/ingest/rtf_reader.py) | Yes | `decode_rtf_bytes`, `extract_rtf_text`, `extract_rtf_tables` | RTF (Rich Text Format) ingestion module for clinical TFLs and listings. |
| `pipeline/ingest` | [`xlsx_reader.py`](pipeline/ingest/xlsx_reader.py) | Lib | `extract_xlsx_data` | XLSX extraction module. |
| `pipeline/literature` | [`download_literature_batch.py`](pipeline/literature/download_literature_batch.py) | Yes | `LiteratureItem`, `try_europepmc_oa`, `try_pmc_pdf`, `try_unpaywall`, `try_openalex`, `try_doi_redirect` | Batch Literature PDF Downloader for F2F Meeting Library |
| `pipeline/literature` | [`probe_fulltext_endpoints.py`](pipeline/literature/probe_fulltext_endpoints.py) | Lib | `log`, `get` | Probe for the full-text endpoints of the two Chinese-journal references that |
| `pipeline/literature` | [`probe_journal_pdf_links.py`](pipeline/literature/probe_journal_pdf_links.py) | Lib | `log`, `fetch` | Probe Chinese journal article pages for a real PDF URL. |
| `pipeline/literature` | [`pubmed_search_tool.py`](pipeline/literature/pubmed_search_tool.py) | Yes | `esearch`, `esummary` | Unified PubMed Literature Search Tool |
| `pipeline/literature` | [`try_direct_pdf_patterns.py`](pipeline/literature/try_direct_pdf_patterns.py) | Yes | `log`, `looks_like_pdf` | Try the magtech '/cn/article/pdf/preview/<doi>.pdf' pattern for the journals |
| `pipeline/core` | [`memory_distiller.py`](pipeline/memory_distiller.py) | Yes | `distill_experiences` | Memory Distiller (Inspired by vectorize-io/hindsight). |
| `pipeline/review` | [`audit_protocol_crossrefs.py`](pipeline/review/audit_protocol_crossrefs.py) | Yes | — | Verify internal cross-references (chapter/section numbers) of a protocol .docx. |
| `pipeline/review` | [`audit_protocol_numeric_consistency.py`](pipeline/review/audit_protocol_numeric_consistency.py) | Yes | `iter_blocks` | Cross-check numeric / placeholder consistency inside a converted protocol markdown. |
| `pipeline/review` | [`compare_docx_content.py`](pipeline/review/compare_docx_content.py) | Yes | `para_sig`, `table_sig`, `body_flow`, `body_flow_nostyle`, `anchor_key`, `canonical_xml_children_sorted` | 逐部件、逐块比对两个 .docx，用于**证明「新增目录」等改动未影响正文内容**。 |
| `pipeline/review` | [`compare_pptx_package.py`](pipeline/review/compare_pptx_package.py) | Yes | `parts` | PPTX 包完整性比对：确认改写后的文件未丢失任何内部构件（媒体、图表、 |
| `pipeline/review` | [`hybrid_diff.py`](pipeline/review/hybrid_diff.py) | Yes | `generate_numbered_diff` | Hybrid Review Diffing Module (Inspired by Alibaba open-code-review). |
| `pipeline/review` | [`scan_protocol_text_quality.py`](pipeline/review/scan_protocol_text_quality.py) | Yes | `iter_blocks` | Scan a numbered protocol markdown for typos, grammar and formatting defects. |
| `pipeline/transform` | [`clinical_rag.py`](pipeline/transform/clinical_rag.py) | Lib | `ClinicalDocumentIndex` | Clinical Local RAG Utility (Retrieval-Augmented Generation). |
| `pipeline/validate` | [`ast_validator.py`](pipeline/validate/ast_validator.py) | Lib | `check_robustness_smells` | AST validation utilities for checking robustness smells. |
| `pipeline/validate` | [`docx_clean_validator.py`](pipeline/validate/docx_clean_validator.py) | Yes | `Issue`, `FileResult`, `check_docx` | Check Word (.docx) files for "clean version" compliance. |
| `pipeline/validate` | [`docx_toc_validator.py`](pipeline/validate/docx_toc_validator.py) | Yes | `verify` | 用本机 Microsoft Word (COM) 实际打开 .docx，**在临时副本上**更新域后导出 PDF / |
| `pipeline/validate` | [`encoding_validator.py`](pipeline/validate/encoding_validator.py) | Lib | `check_bom`, `diagnose_encoding` | Encoding validation utilities. |
| `pipeline/validate` | [`pptx_validator.py`](pipeline/validate/pptx_validator.py) | Lib | `check_overflow`, `find_overflow_slides` | PPTX validation utilities. |

## 2. Repository Governance & Automation Tools (`scripts/_tools/`)

| Script Path | CLI | Public API / Functions | Capability Summary |
|-------------|:---:|------------------------|--------------------|
| [`scripts/_tools/audit_missing_encoding.py`](_tools/audit_missing_encoding.py) | Yes | `is_builtin_open`, `is_path_open`, `mode_of`, `has_encoding`, `scan_file` | 审计仓库脚本中「读写文本但未显式指定 encoding」的 open() / Path.open() 调用。 |
| [`scripts/_tools/audit_robustness_smells.py`](_tools/audit_robustness_smells.py) | Yes | `iter_owned_python_files`, `audit_file` | Audit project-owned Python sources for robustness smells. |
| [`scripts/_tools/cleanup_generated_artifacts.py`](_tools/cleanup_generated_artifacts.py) | Yes | `CleanupResult`, `rm_tree`, `rm_pycache`, `collect_targets`, `cleanup_targets_with_age`, `discover_ide_history_dirs` | Clean up generated/reproducible artifacts created by the project's |
| [`scripts/_tools/fix_fstrings_broad.py`](_tools/fix_fstrings_broad.py) | Yes | `compile_ok`, `fix_fstring_line` | Broad f-string cleanup: remove f-prefix from all f-strings without placeholders |
| [`scripts/_tools/fix_missing_encoding.py`](_tools/fix_missing_encoding.py) | Yes | `is_target`, `has_encoding`, `mode_has_b`, `has_starstar`, `collect`, `prev_nonspace` | 给「读写文本但未指定 encoding」的 open() / Path.open() 调用自动补上 |
| [`scripts/_tools/fix_skill_broken_links.py`](_tools/fix_skill_broken_links.py) | Yes | `Redirect`, `plan_edits` | Repair dangling internal links in ``skills/*/SKILL.md`` documents. |
| [`scripts/_tools/fix_skills_frontmatter.py`](_tools/fix_skills_frontmatter.py) | Yes | `FixAction`, `FixReport` | Batch-fix SKILL.md YAML frontmatter to satisfy the structural contract. |
| [`scripts/_tools/fix_unused_imports.py`](_tools/fix_unused_imports.py) | Yes | `compile_ok`, `remove_symbol_from_import` | Remove unused standard-library imports from vendored skills. |
| [`scripts/_tools/fix_vendored_warnings.py`](_tools/fix_vendored_warnings.py) | Yes | `compile_ok`, `fix_fstring_line`, `process_file`, `fix_reimport` | Fix vendored skills cosmetic warnings: f-strings without placeholders and redundant re-imports. |
| [`scripts/_tools/generate_scripts_index.py`](_tools/generate_scripts_index.py) | Yes | `ScriptEntry`, `collect_entries`, `collect_clinical_automation_modules`, `render_markdown` | Auto-generate a categorized script capability index (scripts/SCRIPTS_INDEX.md) and provide fast keyword search. |
| [`scripts/_tools/generate_skills_index.py`](_tools/generate_skills_index.py) | Yes | `SkillInfo` | Auto-generate a categorized skills index from SKILL.md frontmatter. |
| [`scripts/_tools/inject_skill_sop.py`](_tools/inject_skill_sop.py) | Yes | `read_core_skill_names`, `needs_injection` | Inject the standard Pre-flight / Post-execution SOP into core skills. |
| [`scripts/_tools/make_safe_md_copies.py`](_tools/make_safe_md_copies.py) | Yes | `CopyRecord`, `make_safe_copies` | Build sanitized copies of every ``*.md`` file under a source folder. |
| [`scripts/_tools/pre_flight.py`](_tools/pre_flight.py) | Yes | `pre_flight_check` | Utility script |
| [`scripts/_tools/project_self_check.py`](_tools/project_self_check.py) | Yes | `CmdCheck`, `ScriptCheck`, `check_command`, `check_python_module`, `iter_python_scripts`, `check_venv_policy` | Project self-check: |
| [`scripts/_tools/repair_mojibake_from_git.py`](_tools/repair_mojibake_from_git.py) | Yes | `git_show`, `pua_seq`, `cjk_seq`, `ascii_lines`, `roundtrip`, `evaluate` | 修复 "UTF-8 中文被按中文代码页(GBK/GB18030)解码后又存成 UTF-8" 造成的乱码文件。 |
| [`scripts/_tools/repair_truncated_multibyte_sequences.py`](_tools/repair_truncated_multibyte_sequences.py) | Yes | `learn_prefix_completions`, `repair_bytes`, `iter_text_files` | Repair single-byte UTF-8 corruption where a sequence-final byte became ``?``. |
| [`scripts/_tools/skill_dedupe_report.py`](_tools/skill_dedupe_report.py) | Yes | `SkillDoc`, `build_report` | Utility script |
| [`scripts/_tools/validate_skills_registry.py`](_tools/validate_skills_registry.py) | Yes | `Issue`, `ValidationResult`, `validate_registry` | Validate the skills registry: frontmatter, internal links, ordering, and duplicates. |

## 3. Vendored Clinical Data Automation Library (`scripts/clinical-automation/` — Read-Only)

| Module Directory | Script Count | Representative Scripts |
|------------------|:------------:|------------------------|
| `scripts/clinical-automation/01_Excel_Charts` | 4 | `apply_template_charts.py`, `build_charts_openpyxl.py`, `build_charts_xlsxwriter.py`, `fill_clinical_table.py` |
| `scripts/clinical-automation/02_Excel_Chart_Colors` | 1 | `apply_clinical_colors.py` |
| `scripts/clinical-automation/03_PPT_Merge` | 4 | `csr_ppt_integrator.py`, `merge_ppt.py`, `ppt_engine.py`, `util_test_and_validate.py` |
| `scripts/clinical-automation/04_PPT_Watermark_Removal` | 1 | `pptx_corner_logo_patch.py` |
| `scripts/clinical-automation/05_PPT_to_PDF` | 1 | `ppt_to_pdf.py` |
| `scripts/clinical-automation/06_Word_to_PDF` | 1 | `word_to_pdf.py` |
| `scripts/clinical-automation/07_Word_to_Excel_to_Figure` | 4 | `__init__.py`, `table_mapping_logic.py`, `util_repair_output_by_patch.py`, `word_to_excel_to_figure.py` |
| `scripts/clinical-automation/08_Word_Tables_to_Graphpad` | 9 | `__init__.py`, `antibody_mapping.py`, `docx_parser.py`, `pzfx_parser.py` (+5 more) |
| `scripts/clinical-automation/10_Word_Style_Cleaner` | 1 | `word_style_cleaner.py` |
| `scripts/clinical-automation/11_Word_Text_Replace` | 4 | `__init__.py`, `ooxml_replace.py`, `replace_docx.py`, `util_check_docx.py` |
| `scripts/clinical-automation/12_PDF_Batch_to_Excel` | 3 | `fill_adr_from_pdf.py`, `serology_report_pdf_to_excel.py`, `util_audit_and_fix_consistency.py` |
| `scripts/clinical-automation/13_PDF_to_Excel_Rule_Extract` | 1 | `main.py` |
| `scripts/clinical-automation/14_PDF_to_PPT` | 1 | `pdf_to_ppt.py` |
| `scripts/clinical-automation/15_PDF_XSS` | 1 | `pdf_xss_clean.py` |
| `scripts/clinical-automation/16_PPTX_PDF_to_PPT` | 1 | `convert_to_native_ppt.py` |
| `scripts/clinical-automation/17_PDF_Title_Renamer` | 1 | `pdf_sanitizer.py` |
| `scripts/clinical-automation/18_PDF_eCTD_Converter` | 1 | `pdf_ectd_converter.py` |
| `scripts/clinical-automation/19_PDF_Merge` | 1 | `merge_pdf.py` |
| `scripts/clinical-automation/20_PDF_Bookmark_Inherit_Zoom` | 1 | `pdf_bookmark_inherit_zoom.py` |
| `scripts/clinical-automation/21_PDF_Watermark_Removal` | 9 | `main.py`, `__init__.py`, `step01_triage.py`, `step02_vector_detect.py` (+5 more) |
| `scripts/clinical-automation/22_PDF_Duplicate_Analyzer` | 1 | `pdf_duplicate_analyzer.py` |
| `scripts/clinical-automation/23_PDF_Threat_Analyzer` | 1 | `pdf_threat_analyzer.py` |
| `scripts/clinical-automation/24_File_Translator` | 2 | `file_translator.py`, `util_rebuild_pdf_overlay.py` |
| `scripts/clinical-automation/33_SAE_Extractor` | 6 | `cli.py`, `parsers.py`, `pipelines.py`, `sae_extractor.py` (+2 more) |
| `scripts/clinical-automation/34_Image_to_PDF` | 2 | `image_to_pdf.py`, `merge_images_to_pdf.py` |
| `scripts/clinical-automation/scripts` | 5 | `__init__.py`, `audit_deps.py`, `audit_py.py`, `check_secrets.py` (+1 more) |
| `scripts/clinical-automation/src` | 5 | `__init__.py`, `color_theme.py`, `excel_writer.py`, `pdf_reader.py` (+1 more) |
| `scripts/clinical-automation/tests` | 6 | `conftest.py`, `test_excel_writer.py`, `test_ooxml_replace.py`, `test_pdf_title_renamer.py` (+2 more) |

## 4. Curated Deliverable Reference Templates (`scripts/_archive/` — Local Reference)

| Script Name | CLI | Key Functions | Reference Scenario |
|-------------|:---:|---------------|--------------------|
| `audit_medical_coding_report_020_p2.py` | Yes | `load`, `norm`, `check_meddra`, `check_ae`, `check_whodrug`, `check_conmed_extra` | Audit medical coding report of YDSWX(TVAX-020)-002(II). |
| `crosscheck_pzfx_vs_csr.py` | Yes | `f`, `parse_pzfx` | 交叉比对：GraphPad PZFX 出图数据 vs TFL/CSR 抽取数据（I 期体液免疫 gE / VZV）。 |
| `generate_006P2_cellular_excel.py` | Yes | `title`, `subtitle`, `header`, `rows_out`, `note`, `r1` | generate_006P2_cellular_excel.py  (V2) |
| `generate_006P2_cellular_tfl_docx.py` | Yes | `load`, `set_run`, `para`, `shade`, `set_borders`, `cell_text` | 由 V3 分析工作簿生成 006 Ⅱ 期细胞免疫 TFL（Word）。 |
| `generate_medical_coding_review_checklist_020_p2.py` | Yes | `set_run`, `add_para`, `shade_cell`, `set_widths`, `fill_cell`, `build_table` | Generate TVAX-020-002(II) medical coding review checklist (.docx). |
| `update_006_ppt_phase1_immuno.py` | Yes | `esc`, `make_txbody`, `make_tcpr`, `fill_cell`, `rich_textbox`, `add_rect` | TVAX-006 EOP2 PPT —— Ⅰ期部分更新（v3） |
| `update_herpes_zoster_ctr_database.py` | Yes | `d`, `endpoints`, `arms`, `clean`, `normalize_cell`, `norm` | Sync CTR registry Word data into 国内带疱疫苗临床数据库 Excel. |
| `verify_006P2_excel_vs_raw.py` | Yes | `f2`, `fmt_ms` | 端到端校验：原始数据点（01 数据点清单）→ Excel 汇总值（05 比例 / 06 应答率） |
| `verify_006P2_tfl_docx.py` | Yes | `s`, `build_expect`, `walk`, `grid`, `norm_stat` | 独立校验：把 Word TFL 中的每一个数值，与 Excel 分析工作簿 05/06/04 子表逐值比对。 |
