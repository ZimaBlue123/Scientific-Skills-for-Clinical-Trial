# Global Scripts Capability & Reuse Index (`SCRIPTS_INDEX.md`)

> **Pre-Flight Reuse Mandate (`AGENTS.md` §4)**: Before writing any new script, search this index
> and [`SKILLS_INDEX.md`](../SKILLS_INDEX.md), or run:
> ```bash
> python scripts/_tools/generate_scripts_index.py --search <keyword>   # also searches clinical-automation + skill scripts
> ```
> Always import or invoke existing modules in `scripts/pipeline/` or `scripts/_tools/` instead of reinventing the wheel.
> This file is auto-generated — edit module docstrings, then re-run `python scripts/_tools/generate_scripts_index.py`.

Legend: **CLI** = `Yes` (runnable, `__main__` guard) / `Lib` (import only); **CLI Args** = argparse inputs/outputs.

## 1. Core Modular Pipeline (`scripts/pipeline/`)

| Stage | Script | CLI | CLI Args | Public API | Capability Summary |
|-------|--------|:---:|----------|------------|--------------------|
| `pipeline/convert` | [`convert_doc_to_docx.py`](pipeline/convert/convert_doc_to_docx.py) | Yes | `src`, `--output` | `convert_doc_to_docx` | Convert legacy binary .doc files to .docx using Microsoft Word COM. |
| `pipeline/convert` | [`convert_to_md.py`](pipeline/convert/convert_to_md.py) | Yes | `input`, `--folder`, `--output`, `--extensions`, `--mode`, `--max-cols` | `table_to_md`, `iter_block_items`, `docx_to_md_numbered`, `convert_file`, `convert_folder` | Unified document converter: Convert docx/pdf/rtf/doc to markdown. |
| `pipeline/core` | [`document_facade.py`](pipeline/document_facade.py) | Lib | — | `UnifiedDocument` | Unified Document Facade (Inspired by Univer Architecture). |
| `pipeline/export` | [`apply_audit_fonts.py`](pipeline/export/apply_audit_fonts.py) | Yes | — | `apply_audit_fonts` | 为审计报告 docx 全局应用宋体/Times New Roman 中英文字体。 |
| `pipeline/export` | [`docx_builder.py`](pipeline/export/docx_builder.py) | Lib | — | `create_clinical_docx`, `apply_cn_en_fonts` | DOCX export utilities. |
| `pipeline/export` | [`make_slide_before_after.py`](pipeline/export/make_slide_before_after.py) | Yes | `old_pptx`, `new_pptx`, `page`, `out_png`, `--crop`, `--title-old` | `render`, `load_font` | 把两份 PPTX 的同一页渲染成上下对照图（可指定裁切区域），便于目视 diff。 |
| `pipeline/export` | [`nativize_pptx.py`](pipeline/export/nativize_pptx.py) | Yes | `stage`, `final` | `nativize` | Normalize a python-pptx output by round-tripping it through PowerPoint COM. |
| `pipeline/export` | [`pptx_builder.py`](pipeline/export/pptx_builder.py) | Lib | — | `inject_pptx_data`, `create_slide` | PPTX export utilities. |
| `pipeline/export` | [`render_pptx_slides.py`](pipeline/export/render_pptx_slides.py) | Yes | `pptx`, `slides`, `--outdir`, `--width` | `render` | Render selected slides of a PPTX to PNG via PowerPoint COM. |
| `pipeline/export` | [`update_docx_toc_fields.py`](pipeline/export/update_docx_toc_fields.py) | Yes | `docx_path` | `update_docx_toc_fields` | Update Word (.docx) Table of Contents (TOC) and page number fields via Word COM. |
| `pipeline/extract` | [`extract_docx_review_comments.py`](pipeline/extract/extract_docx_review_comments.py) | Yes | — | `para_text`, `comment_body`, `load`, `extract_comments` | Extract Word comments (with anchoring text) and body paragraphs from a .docx. |
| `pipeline/extract` | [`extract_docx_tracked_text.py`](pipeline/extract/extract_docx_tracked_text.py) | Yes | `docx_path`, `--output`, `--mode` | `extract_tracked_docx`, `para_text` | Extract text and tables from .docx using stdlib only (honoring tracked changes). |
| `pipeline/extract` | [`extract_legacy_doc_text.py`](pipeline/extract/extract_legacy_doc_text.py) | Yes | `src`, `out_dir` | `extract_one_doc`, `extract_legacy_docs` | Extract plain text and table text from legacy binary .doc files via Word COM. |
| `pipeline/extract` | [`stream_docx_tables.py`](pipeline/extract/stream_docx_tables.py) | Yes | `src`, `out_dir`, `--no-paragraphs` | `stream_extract_docx_tables` | Stream-extract every table (and non-table paragraphs) from a very large .docx into TSV files. |
| `pipeline/extract` | [`table_extractor.py`](pipeline/extract/table_extractor.py) | Lib | — | `find_tables_by_heading`, `parse_table_columns` | Table extraction utilities. |
| `pipeline/extract` | [`text_normalizer.py`](pipeline/extract/text_normalizer.py) | Lib | — | `detect_encoding`, `fix_mojibake`, `normalize_whitespace` | Text normalization and encoding diagnostics. |
| `pipeline/ingest` | [`docx_reader.py`](pipeline/ingest/docx_reader.py) | Lib | — | `extract_docx_text`, `extract_docx_tables` | DOCX extraction module. |
| `pipeline/ingest` | [`pdf_reader.py`](pipeline/ingest/pdf_reader.py) | Lib | — | `extract_pdf_text`, `extract_pdf_tables` | PDF extraction module. |
| `pipeline/ingest` | [`pptx_reader.py`](pipeline/ingest/pptx_reader.py) | Lib | — | `extract_pptx_text`, `extract_pptx_notes` | PPTX extraction module. |
| `pipeline/ingest` | [`rtf_reader.py`](pipeline/ingest/rtf_reader.py) | Yes | `rtf_path`, `--tables`, `--grep`, `--output` | `decode_rtf_bytes`, `extract_rtf_text`, `extract_rtf_tables` | RTF (Rich Text Format) ingestion module for clinical TFLs and listings. |
| `pipeline/ingest` | [`xlsx_reader.py`](pipeline/ingest/xlsx_reader.py) | Lib | — | `extract_xlsx_data` | XLSX extraction module. |
| `pipeline/literature` | [`download_literature_batch.py`](pipeline/literature/download_literature_batch.py) | Yes | `--dry-run`, `--report` | `LiteratureItem`, `try_europepmc_oa`, `try_pmc_pdf`, `try_unpaywall`, `try_openalex`, `try_doi_redirect` | Batch Literature PDF Downloader for F2F Meeting Library |
| `pipeline/literature` | [`probe_fulltext_endpoints.py`](pipeline/literature/probe_fulltext_endpoints.py) | Lib | — | `log`, `get` | Probe for the full-text endpoints of the two Chinese-journal references that |
| `pipeline/literature` | [`probe_journal_pdf_links.py`](pipeline/literature/probe_journal_pdf_links.py) | Lib | — | `log`, `fetch` | Probe Chinese journal article pages for a real PDF URL. |
| `pipeline/literature` | [`pubmed_search_tool.py`](pipeline/literature/pubmed_search_tool.py) | Yes | `--query`, `--mindate`, `--maxdate`, `--out`, `--retmax` | `esearch`, `esummary` | Unified PubMed Literature Search Tool |
| `pipeline/literature` | [`try_direct_pdf_patterns.py`](pipeline/literature/try_direct_pdf_patterns.py) | Yes | — | `log`, `looks_like_pdf` | Try the magtech '/cn/article/pdf/preview/<doi>.pdf' pattern for the journals |
| `pipeline/core` | [`memory_distiller.py`](pipeline/memory_distiller.py) | Yes | — | `distill_experiences` | Memory Distiller (Inspired by vectorize-io/hindsight). |
| `pipeline/review` | [`audit_protocol_crossrefs.py`](pipeline/review/audit_protocol_crossrefs.py) | Yes | — | — | Verify internal cross-references (chapter/section numbers) of a protocol .docx. |
| `pipeline/review` | [`audit_protocol_numeric_consistency.py`](pipeline/review/audit_protocol_numeric_consistency.py) | Yes | `markdown`, `--keys` | `iter_blocks` | Cross-check numeric / placeholder consistency inside a converted protocol markdown. |
| `pipeline/review` | [`compare_docx_content.py`](pipeline/review/compare_docx_content.py) | Yes | `old`, `new`, `--out`, `--align-body`, `--capture-styles` | `para_sig`, `table_sig`, `body_flow`, `body_flow_nostyle`, `anchor_key`, `canonical_xml_children_sorted` | 逐部件、逐块比对两个 .docx，用于**证明「新增目录」等改动未影响正文内容**。 |
| `pipeline/review` | [`compare_pptx_package.py`](pipeline/review/compare_pptx_package.py) | Yes | — | `parts` | PPTX 包完整性比对：确认改写后的文件未丢失任何内部构件（媒体、图表、 |
| `pipeline/review` | [`hybrid_diff.py`](pipeline/review/hybrid_diff.py) | Yes | — | `generate_numbered_diff` | Hybrid Review Diffing Module (Inspired by Alibaba open-code-review). |
| `pipeline/review` | [`scan_protocol_text_quality.py`](pipeline/review/scan_protocol_text_quality.py) | Yes | `markdown`, `--show` | `iter_blocks` | Scan a numbered protocol markdown for typos, grammar and formatting defects. |
| `pipeline/transform` | [`clinical_rag.py`](pipeline/transform/clinical_rag.py) | Lib | — | `ClinicalDocumentIndex` | Clinical Local RAG Utility (Retrieval-Augmented Generation). |
| `pipeline/transform` | [`quantile_definitions.py`](pipeline/transform/quantile_definitions.py) | Yes | `values`, `--target-q1`, `--target-q3`, `--tol` | `QUANTILE_DEFINITIONS`, `median`, `quantile`, `quartiles`, `scan_definitions` | Sample quantile definitions for reconciling Q1/Median/Q3 against SAS TFL output. |
| `pipeline/transform` | [`rate_ci_methods.py`](pipeline/transform/rate_ci_methods.py) | Yes | `x1`, `n1`, `x2`, `n2`, `--alpha`, `--target` | `z_value`, `wald_ci`, `wilson_ci`, `wilson_cc_ci`, `clopper_pearson_ci`, `wald_diff_ci` | Binomial proportion and rate-difference confidence intervals for TFL cross-verification. |
| `pipeline/validate` | [`ast_validator.py`](pipeline/validate/ast_validator.py) | Lib | — | `check_robustness_smells` | AST validation utilities for checking robustness smells. |
| `pipeline/validate` | [`docx_clean_validator.py`](pipeline/validate/docx_clean_validator.py) | Yes | `target`, `--json` | `Issue`, `FileResult`, `check_docx` | Check Word (.docx) files for "clean version" compliance. |
| `pipeline/validate` | [`docx_toc_validator.py`](pipeline/validate/docx_toc_validator.py) | Yes | `docx`, `--out-dir`, `--pages` | `verify` | 用本机 Microsoft Word (COM) 实际打开 .docx，**在临时副本上**更新域后导出 PDF / |
| `pipeline/validate` | [`encoding_validator.py`](pipeline/validate/encoding_validator.py) | Lib | — | `check_bom`, `diagnose_encoding` | Encoding validation utilities. |
| `pipeline/validate` | [`pptx_validator.py`](pipeline/validate/pptx_validator.py) | Lib | — | `check_overflow`, `find_overflow_slides` | PPTX validation utilities. |

## 2. Repository Governance & Automation Tools (`scripts/_tools/`)

| Script | CLI | CLI Args | Capability Summary |
|--------|:---:|----------|--------------------|
| [`audit_missing_encoding.py`](_tools/audit_missing_encoding.py) | Yes | — | 审计仓库脚本中「读写文本但未显式指定 encoding」的 open() / Path.open() 调用。 |
| [`audit_robustness_smells.py`](_tools/audit_robustness_smells.py) | Yes | `--json` | Audit project-owned Python sources for robustness smells. |
| [`cleanup_generated_artifacts.py`](_tools/cleanup_generated_artifacts.py) | Yes | `--apply`, `--dry-run`, `--log-level`, `--root`, `--max-age-days`, `--keep-manifest` | Clean up generated/reproducible artifacts created by the project's |
| [`fix_fstrings_broad.py`](_tools/fix_fstrings_broad.py) | Yes | `--apply` | Broad f-string cleanup: remove f-prefix from all f-strings without placeholders |
| [`fix_missing_encoding.py`](_tools/fix_missing_encoding.py) | Yes | — | 给「读写文本但未指定 encoding」的 open() / Path.open() 调用自动补上 |
| [`fix_skill_broken_links.py`](_tools/fix_skill_broken_links.py) | Yes | `--write` | Repair dangling internal links in ``skills/*/SKILL.md`` documents. |
| [`fix_skills_frontmatter.py`](_tools/fix_skills_frontmatter.py) | Yes | `--dry-run`, `--apply`, `--skills-dir` | Batch-fix SKILL.md YAML frontmatter to satisfy the structural contract. |
| [`fix_unused_imports.py`](_tools/fix_unused_imports.py) | Yes | `--apply` | Remove unused standard-library imports from vendored skills. |
| [`fix_vendored_warnings.py`](_tools/fix_vendored_warnings.py) | Yes | `--apply` | Fix vendored skills cosmetic warnings: f-strings without placeholders and redundant re-imports. |
| [`generate_scripts_index.py`](_tools/generate_scripts_index.py) | Yes | `--search`, `--check` | Auto-generate a categorized script capability index (scripts/SCRIPTS_INDEX.md) and provide fast keyword search. |
| [`generate_skills_index.py`](_tools/generate_skills_index.py) | Yes | `--out`, `--skills-dir` | Auto-generate a categorized skills index from SKILL.md frontmatter. |
| [`inject_skill_sop.py`](_tools/inject_skill_sop.py) | Yes | `--write` | Inject the standard Pre-flight / Post-execution SOP into core skills. |
| [`make_safe_md_copies.py`](_tools/make_safe_md_copies.py) | Yes | `--src`, `--out`, `--manifest`, `--log-level` | Build sanitized copies of every ``*.md`` file under a source folder. |
| [`pre_flight.py`](_tools/pre_flight.py) | Yes | — | Utility script |
| [`project_self_check.py`](_tools/project_self_check.py) | Yes | — | Project self-check: |
| [`repair_mojibake_from_git.py`](_tools/repair_mojibake_from_git.py) | Yes | — | 修复 "UTF-8 中文被按中文代码页(GBK/GB18030)解码后又存成 UTF-8" 造成的乱码文件。 |
| [`repair_truncated_multibyte_sequences.py`](_tools/repair_truncated_multibyte_sequences.py) | Yes | `--write` | Repair single-byte UTF-8 corruption where a sequence-final byte became ``?``. |
| [`skill_dedupe_report.py`](_tools/skill_dedupe_report.py) | Yes | `--threshold`, `--top`, `--skills-subdir`, `--out` | Utility script |
| [`validate_skills_registry.py`](_tools/validate_skills_registry.py) | Yes | `--format`, `--out`, `--no-links`, `--no-dedupe`, `--dedupe-threshold`, `--skills-dir` | Validate the skills registry: frontmatter, internal links, ordering, and duplicates. |

## 3. Vendored Clinical Data Automation Library (`scripts/clinical-automation/` — Read-Only)

> Invoke via the `skills/clinical-*` SKILL.md entry points; never edit these scripts directly (`AGENTS.md` §3.1).

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

## 4. Skill-Bundled Scripts (`skills/*/scripts/`)

> Use through the owning skill's `SKILL.md`. Searchable with `--search`.

| Skill | Script Count |
|-------|:------------:|
| [`analytical-method-validation`](../skills/analytical-method-validation/SKILL.md) | 8 |
| [`antibody-kinetics`](../skills/antibody-kinetics/SKILL.md) | 3 |
| [`arboreto`](../skills/arboreto/SKILL.md) | 1 |
| [`biorxiv-database`](../skills/biorxiv-database/SKILL.md) | 1 |
| [`bioservices`](../skills/bioservices/SKILL.md) | 4 |
| [`brenda-database`](../skills/brenda-database/SKILL.md) | 3 |
| [`chembl-database`](../skills/chembl-database/SKILL.md) | 1 |
| [`citation-management`](../skills/citation-management/SKILL.md) | 6 |
| [`clinical-decision-support`](../skills/clinical-decision-support/SKILL.md) | 5 |
| [`clinical-immunogenicity-noninferiority`](../skills/clinical-immunogenicity-noninferiority/SKILL.md) | 4 |
| [`clinical-reports`](../skills/clinical-reports/SKILL.md) | 8 |
| [`clinicaltrials-database`](../skills/clinicaltrials-database/SKILL.md) | 1 |
| [`clinpgx-database`](../skills/clinpgx-database/SKILL.md) | 1 |
| [`cosmic-database`](../skills/cosmic-database/SKILL.md) | 1 |
| [`ctr-registry-to-excel`](../skills/ctr-registry-to-excel/SKILL.md) | 3 |
| [`deepchem`](../skills/deepchem/SKILL.md) | 3 |
| [`deeptools`](../skills/deeptools/SKILL.md) | 2 |
| [`diffdock`](../skills/diffdock/SKILL.md) | 3 |
| [`document-skills-docx`](../skills/document-skills-docx/SKILL.md) | 3 |
| [`document-skills-pdf`](../skills/document-skills-pdf/SKILL.md) | 8 |
| [`document-skills-pptx`](../skills/document-skills-pptx/SKILL.md) | 4 |
| [`drugbank-database`](../skills/drugbank-database/SKILL.md) | 1 |
| [`ensembl-database`](../skills/ensembl-database/SKILL.md) | 1 |
| [`etetoolkit`](../skills/etetoolkit/SKILL.md) | 2 |
| [`experimental-design`](../skills/experimental-design/SKILL.md) | 2 |
| [`exploratory-data-analysis`](../skills/exploratory-data-analysis/SKILL.md) | 1 |
| [`fda-database`](../skills/fda-database/SKILL.md) | 2 |
| [`fireworks-tech-graph`](../skills/fireworks-tech-graph/SKILL.md) | 2 |
| [`fred-economic-data`](../skills/fred-economic-data/SKILL.md) | 2 |
| [`gene-database`](../skills/gene-database/SKILL.md) | 3 |
| [`generate-image`](../skills/generate-image/SKILL.md) | 1 |
| [`get-available-resources`](../skills/get-available-resources/SKILL.md) | 1 |
| [`gget`](../skills/gget/SKILL.md) | 3 |
| [`infographics`](../skills/infographics/SKILL.md) | 2 |
| [`iso-standards-readiness`](../skills/iso-standards-readiness/SKILL.md) | 10 |
| [`kegg-database`](../skills/kegg-database/SKILL.md) | 1 |
| [`labarchive-integration`](../skills/labarchive-integration/SKILL.md) | 3 |
| [`literature-review`](../skills/literature-review/SKILL.md) | 3 |
| [`market-research-reports`](../skills/market-research-reports/SKILL.md) | 1 |
| [`markitdown`](../skills/markitdown/SKILL.md) | 3 |
| [`matplotlib`](../skills/matplotlib/SKILL.md) | 2 |
| [`medchem`](../skills/medchem/SKILL.md) | 1 |
| [`neuropixels-analysis`](../skills/neuropixels-analysis/SKILL.md) | 6 |
| [`ontology-term-resolution`](../skills/ontology-term-resolution/SKILL.md) | 3 |
| [`open-notebook`](../skills/open-notebook/SKILL.md) | 3 |
| [`openalex-database`](../skills/openalex-database/SKILL.md) | 2 |
| [`opentargets-database`](../skills/opentargets-database/SKILL.md) | 1 |
| [`opentrons-integration`](../skills/opentrons-integration/SKILL.md) | 3 |
| [`pathogen-variant-surveillance`](../skills/pathogen-variant-surveillance/SKILL.md) | 5 |
| [`perplexity-search`](../skills/perplexity-search/SKILL.md) | 2 |
| [`pkpd-modeling`](../skills/pkpd-modeling/SKILL.md) | 11 |
| [`pptx-gmc-sync-from-word`](../skills/pptx-gmc-sync-from-word/SKILL.md) | 2 |
| [`pubchem-database`](../skills/pubchem-database/SKILL.md) | 2 |
| [`pufferlib`](../skills/pufferlib/SKILL.md) | 2 |
| [`pydeseq2`](../skills/pydeseq2/SKILL.md) | 1 |
| [`pydicom`](../skills/pydicom/SKILL.md) | 3 |
| [`pymatgen`](../skills/pymatgen/SKILL.md) | 3 |
| [`pymc`](../skills/pymc/SKILL.md) | 2 |
| [`pymoo`](../skills/pymoo/SKILL.md) | 5 |
| [`pytdc`](../skills/pytdc/SKILL.md) | 3 |
| [`pytorch-lightning`](../skills/pytorch-lightning/SKILL.md) | 3 |
| [`rdkit`](../skills/rdkit/SKILL.md) | 3 |
| [`reactome-database`](../skills/reactome-database/SKILL.md) | 1 |
| [`scanpy`](../skills/scanpy/SKILL.md) | 1 |
| [`scientific-schematics`](../skills/scientific-schematics/SKILL.md) | 2 |
| [`scientific-slides`](../skills/scientific-slides/SKILL.md) | 7 |
| [`scientific-visualization`](../skills/scientific-visualization/SKILL.md) | 7 |
| [`scikit-learn`](../skills/scikit-learn/SKILL.md) | 2 |
| [`simpy`](../skills/simpy/SKILL.md) | 2 |
| [`stable-baselines3`](../skills/stable-baselines3/SKILL.md) | 3 |
| [`statistical-analysis`](../skills/statistical-analysis/SKILL.md) | 1 |
| [`statistical-power`](../skills/statistical-power/SKILL.md) | 2 |
| [`string-database`](../skills/string-database/SKILL.md) | 1 |
| [`timesfm-forecasting`](../skills/timesfm-forecasting/SKILL.md) | 2 |
| [`torch-geometric`](../skills/torch-geometric/SKILL.md) | 3 |
| [`treatment-plans`](../skills/treatment-plans/SKILL.md) | 4 |
| [`uniprot-database`](../skills/uniprot-database/SKILL.md) | 1 |
| [`uspto-database`](../skills/uspto-database/SKILL.md) | 3 |
