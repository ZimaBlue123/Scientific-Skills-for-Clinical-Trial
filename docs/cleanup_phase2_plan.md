# 阶段二清理计划 (Phase 2 Cleanup Plan)

> **本文件为扫描结果草案，未执行任何删除。**
> 执行需用户明确批准。基线 commit: `0e5207a`（可回滚）。

## 扫描摘要

- **HIGH 置信度（AUTO_CLEAR）**: 326 项（系统缓存 / 临时副本）
- **MEDIUM 置信度（LIKELY_TMP）**: 25 项（*.log / *.tmp 等）
- **LOW 置信度（UNTRACKED）**: 10 项（git 未追踪，需人工判断）

**总计**: 361 项 / 4,235,641 bytes

## 🟢 高置信度（AUTO_CLEAR）

系统产物：可安全删除

| # | 路径 | 大小 (B) | 模式 | 理由 |
|---:|---|---:|---|---|
| 1 | `__pycache__` | 35,956 | `__pycache__` | Python bytecode cache |
| 2 | `__pycache__/append_supplement.cpython-314.pyc` | 4,887 | `*.pyc` | Python compiled bytecode |
| 3 | `__pycache__/extract_review_doc.cpython-314.pyc` | 1,447 | `*.pyc` | Python compiled bytecode |
| 4 | `__pycache__/extract_review_doc_stdlib.cpython-314.pyc` | 10,853 | `*.pyc` | Python compiled bytecode |
| 5 | `__pycache__/scan_cleanup.cpython-314.pyc` | 6,929 | `*.pyc` | Python compiled bytecode |
| 6 | `__pycache__/verify_data.cpython-314.pyc` | 11,840 | `*.pyc` | Python compiled bytecode |
| 7 | `scripts/__pycache__` | 366,547 | `__pycache__` | Python bytecode cache |
| 8 | `scripts/__pycache__/_selftest_cleanup.cpython-310.pyc` | 6,661 | `*.pyc` | Python compiled bytecode |
| 9 | `scripts/__pycache__/_selftest_ide_history.cpython-310.pyc` | 10,046 | `*.pyc` | Python compiled bytecode |
| 10 | `scripts/__pycache__/audit_dsur.cpython-310.pyc` | 5,671 | `*.pyc` | Python compiled bytecode |
| 11 | `scripts/__pycache__/build_tvax006_IMA_v2_docx.cpython-310.pyc` | 21,970 | `*.pyc` | Python compiled bytecode |
| 12 | `scripts/__pycache__/cansino_detail4843_manual_docx.cpython-310.pyc` | 15,686 | `*.pyc` | Python compiled bytecode |
| 13 | `scripts/__pycache__/cleanup_generated_artifacts.cpython-310.pyc` | 21,731 | `*.pyc` | Python compiled bytecode |
| 14 | `scripts/__pycache__/convert_to_md.cpython-310.pyc` | 11,660 | `*.pyc` | Python compiled bytecode |
| 15 | `scripts/__pycache__/diagnose_docx.cpython-310.pyc` | 2,804 | `*.pyc` | Python compiled bytecode |
| 16 | `scripts/__pycache__/dsur_transfer_v7.cpython-310.pyc` | 13,272 | `*.pyc` | Python compiled bytecode |
| 17 | `scripts/__pycache__/extract_doc_text.cpython-310.pyc` | 4,770 | `*.pyc` | Python compiled bytecode |
| 18 | `scripts/__pycache__/extract_docx_full.cpython-310.pyc` | 8,694 | `*.pyc` | Python compiled bytecode |
| 19 | `scripts/__pycache__/extract_docx_full.cpython-314.pyc` | 16,505 | `*.pyc` | Python compiled bytecode |
| 20 | `scripts/__pycache__/extract_ib_texts.cpython-310.pyc` | 7,981 | `*.pyc` | Python compiled bytecode |
| 21 | `scripts/__pycache__/extract_review_doc_stdlib.cpython-310.pyc` | 6,377 | `*.pyc` | Python compiled bytecode |
| 22 | `scripts/__pycache__/extract_tables_to_docx.cpython-310.pyc` | 29,580 | `*.pyc` | Python compiled bytecode |
| 23 | `scripts/__pycache__/extract_xlsx_full.cpython-310.pyc` | 10,153 | `*.pyc` | Python compiled bytecode |
| 24 | `scripts/__pycache__/generate_audit_report_docx.cpython-310.pyc` | 13,752 | `*.pyc` | Python compiled bytecode |
| 25 | `scripts/__pycache__/generate_clinical_doc_audit_report.cpython-310.pyc` | 6,983 | `*.pyc` | Python compiled bytecode |
| 26 | `scripts/__pycache__/generate_clinical_overview_doc_review_docx.cpython-310.pyc` | 14,252 | `*.pyc` | Python compiled bytecode |
| 27 | `scripts/__pycache__/generate_csr_docx.cpython-310.pyc` | 26,578 | `*.pyc` | Python compiled bytecode |
| 28 | `scripts/__pycache__/generate_mmr_audit_report.cpython-310.pyc` | 18,848 | `*.pyc` | Python compiled bytecode |
| 29 | `scripts/__pycache__/generate_norovirus_review_docx.cpython-310.pyc` | 11,231 | `*.pyc` | Python compiled bytecode |
| 30 | `scripts/__pycache__/generate_norovirus_trial_lit_docx.cpython-310.pyc` | 14,118 | `*.pyc` | Python compiled bytecode |
| 31 | `scripts/__pycache__/generate_phase_summary_doc_review_docx.cpython-310.pyc` | 12,008 | `*.pyc` | Python compiled bytecode |
| 32 | `scripts/__pycache__/make_safe_md_copies.cpython-310.pyc` | 4,789 | `*.pyc` | Python compiled bytecode |
| 33 | `scripts/__pycache__/md_to_docx.cpython-310.pyc` | 3,509 | `*.pyc` | Python compiled bytecode |
| 34 | `scripts/__pycache__/norovirus_trial_search.cpython-310.pyc` | 6,322 | `*.pyc` | Python compiled bytecode |
| 35 | `scripts/__pycache__/project_self_check.cpython-310.pyc` | 8,478 | `*.pyc` | Python compiled bytecode |
| 36 | `scripts/__pycache__/pubmed_lit_search.cpython-310.pyc` | 5,700 | `*.pyc` | Python compiled bytecode |
| 37 | `scripts/__pycache__/review_clinical_xlsx.cpython-310.pyc` | 13,092 | `*.pyc` | Python compiled bytecode |
| 38 | `scripts/__pycache__/skill_dedupe_report.cpython-310.pyc` | 6,419 | `*.pyc` | Python compiled bytecode |
| 39 | `scripts/__pycache__/verify_data.cpython-310.pyc` | 6,907 | `*.pyc` | Python compiled bytecode |
| 40 | `scripts/_archive_2026_consolidation/__pycache__` | 43,027 | `__pycache__` | Python bytecode cache |
| 41 | `scripts/_archive_2026_consolidation/__pycache__/_commit_fix.cpython-310.pyc` | 1,464 | `*.pyc` | Python compiled bytecode |
| 42 | `scripts/_archive_2026_consolidation/__pycache__/_extract_docx_text.cpython-310.pyc` | 4,935 | `*.pyc` | Python compiled bytecode |
| 43 | `scripts/_archive_2026_consolidation/__pycache__/_extract_utf8.cpython-310.pyc` | 920 | `*.pyc` | Python compiled bytecode |
| 44 | `scripts/_archive_2026_consolidation/__pycache__/_fix_duplicate_import.cpython-310.pyc` | 1,216 | `*.pyc` | Python compiled bytecode |
| 45 | `scripts/_archive_2026_consolidation/__pycache__/_fix_path_import.cpython-310.pyc` | 2,331 | `*.pyc` | Python compiled bytecode |
| 46 | `scripts/_archive_2026_consolidation/__pycache__/_full_lint.cpython-310.pyc` | 1,252 | `*.pyc` | Python compiled bytecode |
| 47 | `scripts/_archive_2026_consolidation/__pycache__/_move_to_archive.cpython-310.pyc` | 1,178 | `*.pyc` | Python compiled bytecode |
| 48 | `scripts/_archive_2026_consolidation/__pycache__/_stricter_lint.cpython-310.pyc` | 2,722 | `*.pyc` | Python compiled bytecode |
| 49 | `scripts/_archive_2026_consolidation/__pycache__/_upgrade_docx_utils.cpython-310.pyc` | 3,496 | `*.pyc` | Python compiled bytecode |
| 50 | `scripts/_archive_2026_consolidation/__pycache__/_upgrade_extract.cpython-310.pyc` | 6,178 | `*.pyc` | Python compiled bytecode |
| 51 | `scripts/_archive_2026_consolidation/__pycache__/_verify_data.cpython-310.pyc` | 5,509 | `*.pyc` | Python compiled bytecode |
| 52 | `scripts/_archive_2026_consolidation/__pycache__/_verify_final.cpython-310.pyc` | 1,440 | `*.pyc` | Python compiled bytecode |
| 53 | `scripts/_archive_2026_consolidation/__pycache__/append_supplement.cpython-310.pyc` | 3,460 | `*.pyc` | Python compiled bytecode |
| 54 | `scripts/_archive_2026_consolidation/__pycache__/convert_audit_report_md_to_docx.cpython-310.pyc` | 1,311 | `*.pyc` | Python compiled bytecode |
| 55 | `scripts/_archive_2026_consolidation/__pycache__/convert_doc_to_docx.cpython-310.pyc` | 1,134 | `*.pyc` | Python compiled bytecode |
| 56 | `scripts/_archive_2026_consolidation/__pycache__/extract_docx_to_md.cpython-310.pyc` | 4,481 | `*.pyc` | Python compiled bytecode |
| 57 | `scripts/_tools/__pycache__` | 15,176 | `__pycache__` | Python bytecode cache |
| 58 | `scripts/_tools/__pycache__/_audit_deps.cpython-310.pyc` | 1,241 | `*.pyc` | Python compiled bytecode |
| 59 | `scripts/_tools/__pycache__/_audit_extr.cpython-310.pyc` | 1,255 | `*.pyc` | Python compiled bytecode |
| 60 | `scripts/_tools/__pycache__/_audit_overlap.cpython-310.pyc` | 2,025 | `*.pyc` | Python compiled bytecode |
| 61 | `scripts/_tools/__pycache__/_audit_phase1.cpython-310.pyc` | 2,572 | `*.pyc` | Python compiled bytecode |
| 62 | `scripts/_tools/__pycache__/_audit_scripts.cpython-310.pyc` | 3,566 | `*.pyc` | Python compiled bytecode |
| 63 | `scripts/_tools/__pycache__/scan_cleanup.cpython-310.pyc` | 4,517 | `*.pyc` | Python compiled bytecode |
| 64 | `scripts/common_scripts/__pycache__` | 39,029 | `__pycache__` | Python bytecode cache |
| 65 | `scripts/common_scripts/__pycache__/build_bridge_docs_v2.cpython-310.pyc` | 13,724 | `*.pyc` | Python compiled bytecode |
| 66 | `scripts/common_scripts/__pycache__/docx_utils.cpython-310.pyc` | 5,059 | `*.pyc` | Python compiled bytecode |
| 67 | `scripts/common_scripts/__pycache__/docx_utils.cpython-314.pyc` | 8,605 | `*.pyc` | Python compiled bytecode |
| 68 | `scripts/common_scripts/__pycache__/generator_base.cpython-310.pyc` | 4,782 | `*.pyc` | Python compiled bytecode |
| 69 | `scripts/common_scripts/__pycache__/generator_base.cpython-314.pyc` | 6,859 | `*.pyc` | Python compiled bytecode |
| 70 | `skills/antibody-kinetics/scripts/__pycache__` | 29,095 | `__pycache__` | Python bytecode cache |
| 71 | `skills/antibody-kinetics/scripts/__pycache__/fit_mixedlm_subject.cpython-310.pyc` | 6,904 | `*.pyc` | Python compiled bytecode |
| 72 | `skills/antibody-kinetics/scripts/__pycache__/fit_powerlaw_summary.cpython-310.pyc` | 7,507 | `*.pyc` | Python compiled bytecode |
| 73 | `skills/antibody-kinetics/scripts/__pycache__/run_antibody_kinetics_pipeline.cpython-310.pyc` | 14,684 | `*.pyc` | Python compiled bytecode |
| 74 | `skills/arboreto/scripts/__pycache__` | 2,743 | `__pycache__` | Python bytecode cache |
| 75 | `skills/arboreto/scripts/__pycache__/basic_grn_inference.cpython-310.pyc` | 2,743 | `*.pyc` | Python compiled bytecode |
| 76 | `skills/biorxiv-database/scripts/__pycache__` | 11,843 | `__pycache__` | Python bytecode cache |
| 77 | `skills/biorxiv-database/scripts/__pycache__/biorxiv_search.cpython-310.pyc` | 11,843 | `*.pyc` | Python compiled bytecode |
| 78 | `skills/bioservices/scripts/__pycache__` | 35,837 | `__pycache__` | Python bytecode cache |
| 79 | `skills/bioservices/scripts/__pycache__/batch_id_converter.cpython-310.pyc` | 9,556 | `*.pyc` | Python compiled bytecode |
| 80 | `skills/bioservices/scripts/__pycache__/compound_cross_reference.cpython-310.pyc` | 8,299 | `*.pyc` | Python compiled bytecode |
| 81 | `skills/bioservices/scripts/__pycache__/pathway_analysis.cpython-310.pyc` | 8,228 | `*.pyc` | Python compiled bytecode |
| 82 | `skills/bioservices/scripts/__pycache__/protein_analysis_workflow.cpython-310.pyc` | 9,754 | `*.pyc` | Python compiled bytecode |
| 83 | `skills/brenda-database/scripts/__pycache__` | 67,413 | `__pycache__` | Python bytecode cache |
| 84 | `skills/brenda-database/scripts/__pycache__/brenda_queries.cpython-310.pyc` | 19,660 | `*.pyc` | Python compiled bytecode |
| 85 | `skills/brenda-database/scripts/__pycache__/brenda_visualization.cpython-310.pyc` | 20,751 | `*.pyc` | Python compiled bytecode |
| 86 | `skills/brenda-database/scripts/__pycache__/enzyme_pathway_builder.cpython-310.pyc` | 27,002 | `*.pyc` | Python compiled bytecode |
| 87 | `skills/chembl-database/scripts/__pycache__` | 6,896 | `__pycache__` | Python bytecode cache |
| 88 | `skills/chembl-database/scripts/__pycache__/example_queries.cpython-310.pyc` | 6,896 | `*.pyc` | Python compiled bytecode |
| 89 | `skills/citation-management/scripts/__pycache__` | 55,862 | `__pycache__` | Python bytecode cache |
| 90 | `skills/citation-management/scripts/__pycache__/doi_to_bibtex.cpython-310.pyc` | 5,232 | `*.pyc` | Python compiled bytecode |
| 91 | `skills/citation-management/scripts/__pycache__/extract_metadata.cpython-310.pyc` | 14,559 | `*.pyc` | Python compiled bytecode |
| 92 | `skills/citation-management/scripts/__pycache__/format_bibtex.cpython-310.pyc` | 8,602 | `*.pyc` | Python compiled bytecode |
| 93 | `skills/citation-management/scripts/__pycache__/search_google_scholar.cpython-310.pyc` | 6,856 | `*.pyc` | Python compiled bytecode |
| 94 | `skills/citation-management/scripts/__pycache__/search_pubmed.cpython-310.pyc` | 9,372 | `*.pyc` | Python compiled bytecode |
| 95 | `skills/citation-management/scripts/__pycache__/validate_citations.cpython-310.pyc` | 11,241 | `*.pyc` | Python compiled bytecode |
| 96 | `skills/clinical-decision-support/scripts/__pycache__` | 55,508 | `__pycache__` | Python bytecode cache |
| 97 | `skills/clinical-decision-support/scripts/__pycache__/biomarker_classifier.cpython-310.pyc` | 10,348 | `*.pyc` | Python compiled bytecode |
| 98 | `skills/clinical-decision-support/scripts/__pycache__/build_decision_tree.cpython-310.pyc` | 11,390 | `*.pyc` | Python compiled bytecode |
| 99 | `skills/clinical-decision-support/scripts/__pycache__/create_cohort_tables.cpython-310.pyc` | 13,000 | `*.pyc` | Python compiled bytecode |
| 100 | `skills/clinical-decision-support/scripts/__pycache__/generate_survival_analysis.cpython-310.pyc` | 11,039 | `*.pyc` | Python compiled bytecode |
| 101 | `skills/clinical-decision-support/scripts/__pycache__/validate_cds_document.cpython-310.pyc` | 9,731 | `*.pyc` | Python compiled bytecode |
| 102 | `skills/clinical-reports/scripts/__pycache__` | 35,784 | `__pycache__` | Python bytecode cache |
| 103 | `skills/clinical-reports/scripts/__pycache__/check_deidentification.cpython-310.pyc` | 8,521 | `*.pyc` | Python compiled bytecode |
| 104 | `skills/clinical-reports/scripts/__pycache__/compliance_checker.cpython-310.pyc` | 2,181 | `*.pyc` | Python compiled bytecode |
| 105 | `skills/clinical-reports/scripts/__pycache__/extract_clinical_data.cpython-310.pyc` | 2,541 | `*.pyc` | Python compiled bytecode |
| 106 | `skills/clinical-reports/scripts/__pycache__/format_adverse_events.cpython-310.pyc` | 2,800 | `*.pyc` | Python compiled bytecode |
| 107 | `skills/clinical-reports/scripts/__pycache__/generate_report_template.cpython-310.pyc` | 4,104 | `*.pyc` | Python compiled bytecode |
| 108 | `skills/clinical-reports/scripts/__pycache__/terminology_validator.cpython-310.pyc` | 3,260 | `*.pyc` | Python compiled bytecode |
| 109 | `skills/clinical-reports/scripts/__pycache__/validate_case_report.cpython-310.pyc` | 9,392 | `*.pyc` | Python compiled bytecode |
| 110 | `skills/clinical-reports/scripts/__pycache__/validate_trial_report.cpython-310.pyc` | 2,985 | `*.pyc` | Python compiled bytecode |
| 111 | `skills/clinicaltrials-database/scripts/__pycache__` | 5,808 | `__pycache__` | Python bytecode cache |
| 112 | `skills/clinicaltrials-database/scripts/__pycache__/query_clinicaltrials.cpython-310.pyc` | 5,808 | `*.pyc` | Python compiled bytecode |
| 113 | `skills/clinpgx-database/scripts/__pycache__` | 13,163 | `__pycache__` | Python bytecode cache |
| 114 | `skills/clinpgx-database/scripts/__pycache__/query_clinpgx.cpython-310.pyc` | 13,163 | `*.pyc` | Python compiled bytecode |
| 115 | `skills/cosmic-database/scripts/__pycache__` | 6,291 | `__pycache__` | Python bytecode cache |
| 116 | `skills/cosmic-database/scripts/__pycache__/download_cosmic.cpython-310.pyc` | 6,291 | `*.pyc` | Python compiled bytecode |
| 117 | `skills/deepchem/scripts/__pycache__` | 21,277 | `__pycache__` | Python bytecode cache |
| 118 | `skills/deepchem/scripts/__pycache__/graph_neural_network.cpython-310.pyc` | 7,345 | `*.pyc` | Python compiled bytecode |
| 119 | `skills/deepchem/scripts/__pycache__/predict_solubility.cpython-310.pyc` | 5,274 | `*.pyc` | Python compiled bytecode |
| 120 | `skills/deepchem/scripts/__pycache__/transfer_learning.cpython-310.pyc` | 8,658 | `*.pyc` | Python compiled bytecode |
| 121 | `skills/deeptools/scripts/__pycache__` | 17,949 | `__pycache__` | Python bytecode cache |
| 122 | `skills/deeptools/scripts/__pycache__/validate_files.cpython-310.pyc` | 4,869 | `*.pyc` | Python compiled bytecode |
| 123 | `skills/deeptools/scripts/__pycache__/workflow_generator.cpython-310.pyc` | 13,080 | `*.pyc` | Python compiled bytecode |
| 124 | `skills/diffdock/scripts/__pycache__` | 23,679 | `__pycache__` | Python bytecode cache |
| 125 | `skills/diffdock/scripts/__pycache__/analyze_results.cpython-310.pyc` | 9,198 | `*.pyc` | Python compiled bytecode |
| 126 | `skills/diffdock/scripts/__pycache__/prepare_batch_csv.cpython-310.pyc` | 6,805 | `*.pyc` | Python compiled bytecode |
| 127 | `skills/diffdock/scripts/__pycache__/setup_check.cpython-310.pyc` | 7,676 | `*.pyc` | Python compiled bytecode |
| 128 | `skills/document-skills-docx/ooxml/scripts/__pycache__` | 7,415 | `__pycache__` | Python bytecode cache |
| 129 | `skills/document-skills-docx/ooxml/scripts/__pycache__/pack.cpython-310.pyc` | 4,511 | `*.pyc` | Python compiled bytecode |
| 130 | `skills/document-skills-docx/ooxml/scripts/__pycache__/unpack.cpython-310.pyc` | 1,108 | `*.pyc` | Python compiled bytecode |
| 131 | `skills/document-skills-docx/ooxml/scripts/__pycache__/validate.cpython-310.pyc` | 1,796 | `*.pyc` | Python compiled bytecode |
| 132 | `skills/document-skills-docx/ooxml/scripts/validation/__pycache__` | 43,464 | `__pycache__` | Python bytecode cache |
| 133 | `skills/document-skills-docx/ooxml/scripts/validation/__pycache__/__init__.cpython-310.pyc` | 518 | `*.pyc` | Python compiled bytecode |
| 134 | `skills/document-skills-docx/ooxml/scripts/validation/__pycache__/base.cpython-310.pyc` | 21,982 | `*.pyc` | Python compiled bytecode |
| 135 | `skills/document-skills-docx/ooxml/scripts/validation/__pycache__/docx.cpython-310.pyc` | 6,498 | `*.pyc` | Python compiled bytecode |
| 136 | `skills/document-skills-docx/ooxml/scripts/validation/__pycache__/pptx.cpython-310.pyc` | 7,792 | `*.pyc` | Python compiled bytecode |
| 137 | `skills/document-skills-docx/ooxml/scripts/validation/__pycache__/redlining.cpython-310.pyc` | 6,674 | `*.pyc` | Python compiled bytecode |
| 138 | `skills/document-skills-docx/scripts/__pycache__` | 47,076 | `__pycache__` | Python bytecode cache |
| 139 | `skills/document-skills-docx/scripts/__pycache__/__init__.cpython-310.pyc` | 197 | `*.pyc` | Python compiled bytecode |
| 140 | `skills/document-skills-docx/scripts/__pycache__/document.cpython-310.pyc` | 34,484 | `*.pyc` | Python compiled bytecode |
| 141 | `skills/document-skills-docx/scripts/__pycache__/utilities.cpython-310.pyc` | 12,395 | `*.pyc` | Python compiled bytecode |
| 142 | `skills/document-skills-pdf/scripts/__pycache__` | 22,791 | `__pycache__` | Python bytecode cache |
| 143 | `skills/document-skills-pdf/scripts/__pycache__/check_bounding_boxes.cpython-310.pyc` | 2,523 | `*.pyc` | Python compiled bytecode |
| 144 | `skills/document-skills-pdf/scripts/__pycache__/check_bounding_boxes_test.cpython-310.pyc` | 7,283 | `*.pyc` | Python compiled bytecode |
| 145 | `skills/document-skills-pdf/scripts/__pycache__/check_fillable_fields.cpython-310.pyc` | 488 | `*.pyc` | Python compiled bytecode |
| 146 | `skills/document-skills-pdf/scripts/__pycache__/convert_pdf_to_images.cpython-310.pyc` | 1,141 | `*.pyc` | Python compiled bytecode |
| 147 | `skills/document-skills-pdf/scripts/__pycache__/create_validation_image.cpython-310.pyc` | 1,305 | `*.pyc` | Python compiled bytecode |
| 148 | `skills/document-skills-pdf/scripts/__pycache__/extract_form_field_info.cpython-310.pyc` | 3,588 | `*.pyc` | Python compiled bytecode |
| 149 | `skills/document-skills-pdf/scripts/__pycache__/fill_fillable_fields.cpython-310.pyc` | 3,914 | `*.pyc` | Python compiled bytecode |
| 150 | `skills/document-skills-pdf/scripts/__pycache__/fill_pdf_form_with_annotations.cpython-310.pyc` | 2,549 | `*.pyc` | Python compiled bytecode |
| 151 | `skills/document-skills-pptx/ooxml/scripts/__pycache__` | 7,415 | `__pycache__` | Python bytecode cache |
| 152 | `skills/document-skills-pptx/ooxml/scripts/__pycache__/pack.cpython-310.pyc` | 4,511 | `*.pyc` | Python compiled bytecode |
| 153 | `skills/document-skills-pptx/ooxml/scripts/__pycache__/unpack.cpython-310.pyc` | 1,108 | `*.pyc` | Python compiled bytecode |
| 154 | `skills/document-skills-pptx/ooxml/scripts/__pycache__/validate.cpython-310.pyc` | 1,796 | `*.pyc` | Python compiled bytecode |
| 155 | `skills/document-skills-pptx/ooxml/scripts/validation/__pycache__` | 43,464 | `__pycache__` | Python bytecode cache |
| 156 | `skills/document-skills-pptx/ooxml/scripts/validation/__pycache__/__init__.cpython-310.pyc` | 518 | `*.pyc` | Python compiled bytecode |
| 157 | `skills/document-skills-pptx/ooxml/scripts/validation/__pycache__/base.cpython-310.pyc` | 21,982 | `*.pyc` | Python compiled bytecode |
| 158 | `skills/document-skills-pptx/ooxml/scripts/validation/__pycache__/docx.cpython-310.pyc` | 6,498 | `*.pyc` | Python compiled bytecode |
| 159 | `skills/document-skills-pptx/ooxml/scripts/validation/__pycache__/pptx.cpython-310.pyc` | 7,792 | `*.pyc` | Python compiled bytecode |
| 160 | `skills/document-skills-pptx/ooxml/scripts/validation/__pycache__/redlining.cpython-310.pyc` | 6,674 | `*.pyc` | Python compiled bytecode |
| 161 | `skills/document-skills-pptx/scripts/__pycache__` | 48,565 | `__pycache__` | Python bytecode cache |
| 162 | `skills/document-skills-pptx/scripts/__pycache__/inventory.cpython-310.pyc` | 24,885 | `*.pyc` | Python compiled bytecode |
| 163 | `skills/document-skills-pptx/scripts/__pycache__/rearrange.cpython-310.pyc` | 5,721 | `*.pyc` | Python compiled bytecode |
| 164 | `skills/document-skills-pptx/scripts/__pycache__/replace.cpython-310.pyc` | 8,449 | `*.pyc` | Python compiled bytecode |
| 165 | `skills/document-skills-pptx/scripts/__pycache__/thumbnail.cpython-310.pyc` | 9,510 | `*.pyc` | Python compiled bytecode |
| 166 | `skills/drugbank-database/scripts/__pycache__` | 9,248 | `__pycache__` | Python bytecode cache |
| 167 | `skills/drugbank-database/scripts/__pycache__/drugbank_helper.cpython-310.pyc` | 9,248 | `*.pyc` | Python compiled bytecode |
| 168 | `skills/ensembl-database/scripts/__pycache__` | 11,803 | `__pycache__` | Python bytecode cache |
| 169 | `skills/ensembl-database/scripts/__pycache__/ensembl_query.cpython-310.pyc` | 11,803 | `*.pyc` | Python compiled bytecode |
| 170 | `skills/etetoolkit/scripts/__pycache__` | 12,759 | `__pycache__` | Python bytecode cache |
| 171 | `skills/etetoolkit/scripts/__pycache__/quick_visualize.cpython-310.pyc` | 5,601 | `*.pyc` | Python compiled bytecode |
| 172 | `skills/etetoolkit/scripts/__pycache__/tree_operations.cpython-310.pyc` | 7,158 | `*.pyc` | Python compiled bytecode |
| 173 | `skills/exploratory-data-analysis/scripts/__pycache__` | 15,274 | `__pycache__` | Python bytecode cache |
| 174 | `skills/exploratory-data-analysis/scripts/__pycache__/eda_analyzer.cpython-310.pyc` | 15,274 | `*.pyc` | Python compiled bytecode |
| 175 | `skills/fda-database/scripts/__pycache__` | 22,552 | `__pycache__` | Python bytecode cache |
| 176 | `skills/fda-database/scripts/__pycache__/fda_examples.cpython-310.pyc` | 8,439 | `*.pyc` | Python compiled bytecode |
| 177 | `skills/fda-database/scripts/__pycache__/fda_query.cpython-310.pyc` | 14,113 | `*.pyc` | Python compiled bytecode |
| 178 | `skills/fireworks-tech-graph/scripts/__pycache__` | 49,527 | `__pycache__` | Python bytecode cache |
| 179 | `skills/fireworks-tech-graph/scripts/__pycache__/generate-from-template.cpython-310.pyc` | 47,879 | `*.pyc` | Python compiled bytecode |
| 180 | `skills/fireworks-tech-graph/scripts/__pycache__/sanitize-svg-text.cpython-310.pyc` | 1,648 | `*.pyc` | Python compiled bytecode |
| 181 | `skills/fred-economic-data/scripts/__pycache__` | 24,353 | `__pycache__` | Python bytecode cache |
| 182 | `skills/fred-economic-data/scripts/__pycache__/fred_examples.cpython-310.pyc` | 9,191 | `*.pyc` | Python compiled bytecode |
| 183 | `skills/fred-economic-data/scripts/__pycache__/fred_query.cpython-310.pyc` | 15,162 | `*.pyc` | Python compiled bytecode |
| 184 | `skills/gene-database/scripts/__pycache__` | 22,013 | `__pycache__` | Python bytecode cache |
| 185 | `skills/gene-database/scripts/__pycache__/batch_gene_lookup.cpython-310.pyc` | 7,681 | `*.pyc` | Python compiled bytecode |
| 186 | `skills/gene-database/scripts/__pycache__/fetch_gene_data.cpython-310.pyc` | 7,466 | `*.pyc` | Python compiled bytecode |
| 187 | `skills/gene-database/scripts/__pycache__/query_gene.cpython-310.pyc` | 6,866 | `*.pyc` | Python compiled bytecode |
| 188 | `skills/generate-image/scripts/__pycache__` | 6,998 | `__pycache__` | Python bytecode cache |
| 189 | `skills/generate-image/scripts/__pycache__/generate_image.cpython-310.pyc` | 6,998 | `*.pyc` | Python compiled bytecode |
| 190 | `skills/get-available-resources/scripts/__pycache__` | 10,036 | `__pycache__` | Python bytecode cache |
| 191 | `skills/get-available-resources/scripts/__pycache__/detect_resources.cpython-310.pyc` | 10,036 | `*.pyc` | Python compiled bytecode |
| 192 | `skills/gget/scripts/__pycache__` | 15,278 | `__pycache__` | Python bytecode cache |
| 193 | `skills/gget/scripts/__pycache__/batch_sequence_analysis.cpython-310.pyc` | 4,976 | `*.pyc` | Python compiled bytecode |
| 194 | `skills/gget/scripts/__pycache__/enrichment_pipeline.cpython-310.pyc` | 5,566 | `*.pyc` | Python compiled bytecode |
| 195 | `skills/gget/scripts/__pycache__/gene_analysis.cpython-310.pyc` | 4,736 | `*.pyc` | Python compiled bytecode |
| 196 | `skills/infographics/scripts/__pycache__` | 43,883 | `__pycache__` | Python bytecode cache |
| 197 | `skills/infographics/scripts/__pycache__/generate_infographic.cpython-310.pyc` | 9,297 | `*.pyc` | Python compiled bytecode |
| 198 | `skills/infographics/scripts/__pycache__/generate_infographic_ai.cpython-310.pyc` | 34,586 | `*.pyc` | Python compiled bytecode |
| 199 | `skills/iso-13485-certification/scripts/__pycache__` | 11,981 | `__pycache__` | Python bytecode cache |
| 200 | `skills/iso-13485-certification/scripts/__pycache__/gap_analyzer.cpython-310.pyc` | 11,981 | `*.pyc` | Python compiled bytecode |
| 201 | `skills/kegg-database/scripts/__pycache__` | 7,684 | `__pycache__` | Python bytecode cache |
| 202 | `skills/kegg-database/scripts/__pycache__/kegg_api.cpython-310.pyc` | 7,684 | `*.pyc` | Python compiled bytecode |
| 203 | `skills/labarchive-integration/scripts/__pycache__` | 21,635 | `__pycache__` | Python bytecode cache |
| 204 | `skills/labarchive-integration/scripts/__pycache__/entry_operations.cpython-310.pyc` | 8,700 | `*.pyc` | Python compiled bytecode |
| 205 | `skills/labarchive-integration/scripts/__pycache__/notebook_operations.cpython-310.pyc` | 7,056 | `*.pyc` | Python compiled bytecode |
| 206 | `skills/labarchive-integration/scripts/__pycache__/setup_config.cpython-310.pyc` | 5,879 | `*.pyc` | Python compiled bytecode |
| 207 | `skills/literature-review/scripts/__pycache__` | 18,012 | `__pycache__` | Python bytecode cache |
| 208 | `skills/literature-review/scripts/__pycache__/generate_pdf.cpython-310.pyc` | 4,349 | `*.pyc` | Python compiled bytecode |
| 209 | `skills/literature-review/scripts/__pycache__/search_databases.cpython-310.pyc` | 7,185 | `*.pyc` | Python compiled bytecode |
| 210 | `skills/literature-review/scripts/__pycache__/verify_citations.cpython-310.pyc` | 6,478 | `*.pyc` | Python compiled bytecode |
| 211 | `skills/market-research-reports/scripts/__pycache__` | 15,288 | `__pycache__` | Python bytecode cache |
| 212 | `skills/market-research-reports/scripts/__pycache__/generate_market_visuals.cpython-310.pyc` | 15,288 | `*.pyc` | Python compiled bytecode |
| 213 | `skills/markitdown/scripts/__pycache__` | 18,883 | `__pycache__` | Python bytecode cache |
| 214 | `skills/markitdown/scripts/__pycache__/batch_convert.cpython-310.pyc` | 5,632 | `*.pyc` | Python compiled bytecode |
| 215 | `skills/markitdown/scripts/__pycache__/convert_literature.cpython-310.pyc` | 6,641 | `*.pyc` | Python compiled bytecode |
| 216 | `skills/markitdown/scripts/__pycache__/convert_with_ai.cpython-310.pyc` | 6,610 | `*.pyc` | Python compiled bytecode |
| 217 | `skills/matplotlib/scripts/__pycache__` | 21,141 | `__pycache__` | Python bytecode cache |
| 218 | `skills/matplotlib/scripts/__pycache__/plot_template.cpython-310.pyc` | 10,212 | `*.pyc` | Python compiled bytecode |
| 219 | `skills/matplotlib/scripts/__pycache__/style_configurator.cpython-310.pyc` | 10,929 | `*.pyc` | Python compiled bytecode |
| 220 | `skills/medchem/scripts/__pycache__` | 14,216 | `__pycache__` | Python bytecode cache |
| 221 | `skills/medchem/scripts/__pycache__/filter_molecules.cpython-310.pyc` | 14,216 | `*.pyc` | Python compiled bytecode |
| 222 | `skills/neuropixels-analysis/scripts/__pycache__` | 27,874 | `__pycache__` | Python bytecode cache |
| 223 | `skills/neuropixels-analysis/scripts/__pycache__/compute_metrics.cpython-310.pyc` | 3,965 | `*.pyc` | Python compiled bytecode |
| 224 | `skills/neuropixels-analysis/scripts/__pycache__/explore_recording.cpython-310.pyc` | 4,876 | `*.pyc` | Python compiled bytecode |
| 225 | `skills/neuropixels-analysis/scripts/__pycache__/export_to_phy.cpython-310.pyc` | 2,326 | `*.pyc` | Python compiled bytecode |
| 226 | `skills/neuropixels-analysis/scripts/__pycache__/neuropixels_pipeline.cpython-310.pyc` | 10,674 | `*.pyc` | Python compiled bytecode |
| 227 | `skills/neuropixels-analysis/scripts/__pycache__/preprocess_recording.cpython-310.pyc` | 3,549 | `*.pyc` | Python compiled bytecode |
| 228 | `skills/neuropixels-analysis/scripts/__pycache__/run_sorting.cpython-310.pyc` | 2,484 | `*.pyc` | Python compiled bytecode |
| 229 | `skills/open-notebook/scripts/__pycache__` | 32,258 | `__pycache__` | Python bytecode cache |
| 230 | `skills/open-notebook/scripts/__pycache__/chat_interaction.cpython-310.pyc` | 5,204 | `*.pyc` | Python compiled bytecode |
| 231 | `skills/open-notebook/scripts/__pycache__/notebook_management.cpython-310.pyc` | 3,714 | `*.pyc` | Python compiled bytecode |
| 232 | `skills/open-notebook/scripts/__pycache__/source_ingestion.cpython-310.pyc` | 4,466 | `*.pyc` | Python compiled bytecode |
| 233 | `skills/open-notebook/scripts/__pycache__/test_open_notebook_skill.cpython-310.pyc` | 18,874 | `*.pyc` | Python compiled bytecode |
| 234 | `skills/openalex-database/scripts/__pycache__` | 14,823 | `__pycache__` | Python bytecode cache |
| 235 | `skills/openalex-database/scripts/__pycache__/openalex_client.cpython-310.pyc` | 8,404 | `*.pyc` | Python compiled bytecode |
| 236 | `skills/openalex-database/scripts/__pycache__/query_helpers.cpython-310.pyc` | 6,419 | `*.pyc` | Python compiled bytecode |
| 237 | `skills/opentargets-database/scripts/__pycache__` | 10,202 | `__pycache__` | Python bytecode cache |
| 238 | `skills/opentargets-database/scripts/__pycache__/query_opentargets.cpython-310.pyc` | 10,202 | `*.pyc` | Python compiled bytecode |
| 239 | `skills/opentrons-integration/scripts/__pycache__` | 7,124 | `__pycache__` | Python bytecode cache |
| 240 | `skills/opentrons-integration/scripts/__pycache__/basic_protocol_template.cpython-310.pyc` | 1,439 | `*.pyc` | Python compiled bytecode |
| 241 | `skills/opentrons-integration/scripts/__pycache__/pcr_setup_template.cpython-310.pyc` | 3,227 | `*.pyc` | Python compiled bytecode |
| 242 | `skills/opentrons-integration/scripts/__pycache__/serial_dilution_template.cpython-310.pyc` | 2,458 | `*.pyc` | Python compiled bytecode |
| 243 | `skills/perplexity-search/scripts/__pycache__` | 10,886 | `__pycache__` | Python bytecode cache |
| 244 | `skills/perplexity-search/scripts/__pycache__/perplexity_search.cpython-310.pyc` | 6,667 | `*.pyc` | Python compiled bytecode |
| 245 | `skills/perplexity-search/scripts/__pycache__/setup_env.cpython-310.pyc` | 4,219 | `*.pyc` | Python compiled bytecode |
| 246 | `skills/pptx-gmc-sync-from-word/scripts/__pycache__` | 11,111 | `__pycache__` | Python bytecode cache |
| 247 | `skills/pptx-gmc-sync-from-word/scripts/__pycache__/export_ppt_tables_to_word.cpython-310.pyc` | 2,749 | `*.pyc` | Python compiled bytecode |
| 248 | `skills/pptx-gmc-sync-from-word/scripts/__pycache__/sync_pptx_from_word.cpython-310.pyc` | 8,362 | `*.pyc` | Python compiled bytecode |
| 249 | `skills/pubchem-database/scripts/__pycache__` | 16,588 | `__pycache__` | Python bytecode cache |
| 250 | `skills/pubchem-database/scripts/__pycache__/bioactivity_query.cpython-310.pyc` | 8,482 | `*.pyc` | Python compiled bytecode |
| 251 | `skills/pubchem-database/scripts/__pycache__/compound_search.cpython-310.pyc` | 8,106 | `*.pyc` | Python compiled bytecode |
| 252 | `skills/pufferlib/scripts/__pycache__` | 13,917 | `__pycache__` | Python bytecode cache |
| 253 | `skills/pufferlib/scripts/__pycache__/env_template.cpython-310.pyc` | 8,122 | `*.pyc` | Python compiled bytecode |
| 254 | `skills/pufferlib/scripts/__pycache__/train_template.cpython-310.pyc` | 5,795 | `*.pyc` | Python compiled bytecode |
| 255 | `skills/pydeseq2/scripts/__pycache__` | 9,510 | `__pycache__` | Python bytecode cache |
| 256 | `skills/pydeseq2/scripts/__pycache__/run_deseq2_analysis.cpython-310.pyc` | 9,510 | `*.pyc` | Python compiled bytecode |
| 257 | `skills/pydicom/scripts/__pycache__` | 13,544 | `__pycache__` | Python bytecode cache |
| 258 | `skills/pydicom/scripts/__pycache__/anonymize_dicom.cpython-310.pyc` | 4,034 | `*.pyc` | Python compiled bytecode |
| 259 | `skills/pydicom/scripts/__pycache__/dicom_to_image.cpython-310.pyc` | 4,778 | `*.pyc` | Python compiled bytecode |
| 260 | `skills/pydicom/scripts/__pycache__/extract_metadata.cpython-310.pyc` | 4,732 | `*.pyc` | Python compiled bytecode |
| 261 | `skills/pymatgen/scripts/__pycache__` | 17,308 | `__pycache__` | Python bytecode cache |
| 262 | `skills/pymatgen/scripts/__pycache__/phase_diagram_generator.cpython-310.pyc` | 6,022 | `*.pyc` | Python compiled bytecode |
| 263 | `skills/pymatgen/scripts/__pycache__/structure_analyzer.cpython-310.pyc` | 6,544 | `*.pyc` | Python compiled bytecode |
| 264 | `skills/pymatgen/scripts/__pycache__/structure_converter.cpython-310.pyc` | 4,742 | `*.pyc` | Python compiled bytecode |
| 265 | `skills/pymc/scripts/__pycache__` | 20,391 | `__pycache__` | Python bytecode cache |
| 266 | `skills/pymc/scripts/__pycache__/model_comparison.cpython-310.pyc` | 11,308 | `*.pyc` | Python compiled bytecode |
| 267 | `skills/pymc/scripts/__pycache__/model_diagnostics.cpython-310.pyc` | 9,083 | `*.pyc` | Python compiled bytecode |
| 268 | `skills/pymoo/scripts/__pycache__` | 14,754 | `__pycache__` | Python bytecode cache |
| 269 | `skills/pymoo/scripts/__pycache__/custom_problem_example.cpython-310.pyc` | 4,547 | `*.pyc` | Python compiled bytecode |
| 270 | `skills/pymoo/scripts/__pycache__/decision_making_example.cpython-310.pyc` | 4,371 | `*.pyc` | Python compiled bytecode |
| 271 | `skills/pymoo/scripts/__pycache__/many_objective_example.cpython-310.pyc` | 2,206 | `*.pyc` | Python compiled bytecode |
| 272 | `skills/pymoo/scripts/__pycache__/multi_objective_example.cpython-310.pyc` | 1,851 | `*.pyc` | Python compiled bytecode |
| 273 | `skills/pymoo/scripts/__pycache__/single_objective_example.cpython-310.pyc` | 1,779 | `*.pyc` | Python compiled bytecode |
| 274 | `skills/pytdc/scripts/__pycache__` | 22,016 | `__pycache__` | Python bytecode cache |
| 275 | `skills/pytdc/scripts/__pycache__/benchmark_evaluation.cpython-310.pyc` | 7,802 | `*.pyc` | Python compiled bytecode |
| 276 | `skills/pytdc/scripts/__pycache__/load_and_split_data.cpython-310.pyc` | 5,000 | `*.pyc` | Python compiled bytecode |
| 277 | `skills/pytdc/scripts/__pycache__/molecular_generation.cpython-310.pyc` | 9,214 | `*.pyc` | Python compiled bytecode |
| 278 | `skills/pytorch-lightning/scripts/__pycache__` | 20,480 | `__pycache__` | Python bytecode cache |
| 279 | `skills/pytorch-lightning/scripts/__pycache__/quick_trainer_setup.cpython-310.pyc` | 7,530 | `*.pyc` | Python compiled bytecode |
| 280 | `skills/pytorch-lightning/scripts/__pycache__/template_datamodule.cpython-310.pyc` | 7,593 | `*.pyc` | Python compiled bytecode |
| 281 | `skills/pytorch-lightning/scripts/__pycache__/template_lightning_module.cpython-310.pyc` | 5,357 | `*.pyc` | Python compiled bytecode |
| 282 | `skills/rdkit/scripts/__pycache__` | 23,581 | `__pycache__` | Python bytecode cache |
| 283 | `skills/rdkit/scripts/__pycache__/molecular_properties.cpython-310.pyc` | 6,396 | `*.pyc` | Python compiled bytecode |
| 284 | `skills/rdkit/scripts/__pycache__/similarity_search.cpython-310.pyc` | 8,188 | `*.pyc` | Python compiled bytecode |
| 285 | `skills/rdkit/scripts/__pycache__/substructure_filter.cpython-310.pyc` | 8,997 | `*.pyc` | Python compiled bytecode |
| 286 | `skills/reactome-database/scripts/__pycache__` | 8,690 | `__pycache__` | Python bytecode cache |
| 287 | `skills/reactome-database/scripts/__pycache__/reactome_query.cpython-310.pyc` | 8,690 | `*.pyc` | Python compiled bytecode |
| 288 | `skills/scanpy/scripts/__pycache__` | 5,509 | `__pycache__` | Python bytecode cache |
| 289 | `skills/scanpy/scripts/__pycache__/qc_analysis.cpython-310.pyc` | 5,509 | `*.pyc` | Python compiled bytecode |
| 290 | `skills/scientific-schematics/scripts/__pycache__` | 28,029 | `__pycache__` | Python bytecode cache |
| 291 | `skills/scientific-schematics/scripts/__pycache__/generate_schematic.cpython-310.pyc` | 4,659 | `*.pyc` | Python compiled bytecode |
| 292 | `skills/scientific-schematics/scripts/__pycache__/generate_schematic_ai.cpython-310.pyc` | 23,370 | `*.pyc` | Python compiled bytecode |
| 293 | `skills/scikit-learn/scripts/__pycache__` | 14,564 | `__pycache__` | Python bytecode cache |
| 294 | `skills/scikit-learn/scripts/__pycache__/classification_pipeline.cpython-310.pyc` | 6,069 | `*.pyc` | Python compiled bytecode |
| 295 | `skills/scikit-learn/scripts/__pycache__/clustering_analysis.cpython-310.pyc` | 8,495 | `*.pyc` | Python compiled bytecode |
| 296 | `skills/simpy/scripts/__pycache__` | 16,791 | `__pycache__` | Python bytecode cache |
| 297 | `skills/simpy/scripts/__pycache__/basic_simulation_template.cpython-310.pyc` | 5,368 | `*.pyc` | Python compiled bytecode |
| 298 | `skills/simpy/scripts/__pycache__/resource_monitor.cpython-310.pyc` | 11,423 | `*.pyc` | Python compiled bytecode |
| 299 | `skills/stable-baselines3/scripts/__pycache__` | 14,873 | `__pycache__` | Python bytecode cache |
| 300 | `skills/stable-baselines3/scripts/__pycache__/custom_env_template.cpython-310.pyc` | 6,808 | `*.pyc` | Python compiled bytecode |
| 301 | `skills/stable-baselines3/scripts/__pycache__/evaluate_agent.cpython-310.pyc` | 4,968 | `*.pyc` | Python compiled bytecode |
| 302 | `skills/stable-baselines3/scripts/__pycache__/train_rl_agent.cpython-310.pyc` | 3,097 | `*.pyc` | Python compiled bytecode |
| 303 | `skills/statistical-analysis/scripts/__pycache__` | 12,675 | `__pycache__` | Python bytecode cache |
| 304 | `skills/statistical-analysis/scripts/__pycache__/assumption_checks.cpython-310.pyc` | 12,675 | `*.pyc` | Python compiled bytecode |
| 305 | `skills/string-database/scripts/__pycache__` | 10,007 | `__pycache__` | Python bytecode cache |
| 306 | `skills/string-database/scripts/__pycache__/string_api.cpython-310.pyc` | 10,007 | `*.pyc` | Python compiled bytecode |
| 307 | `skills/timesfm-forecasting/scripts/__pycache__` | 20,369 | `__pycache__` | Python bytecode cache |
| 308 | `skills/timesfm-forecasting/scripts/__pycache__/check_system.cpython-310.pyc` | 12,605 | `*.pyc` | Python compiled bytecode |
| 309 | `skills/timesfm-forecasting/scripts/__pycache__/forecast_csv.cpython-310.pyc` | 7,764 | `*.pyc` | Python compiled bytecode |
| 310 | `skills/torch_geometric/scripts/__pycache__` | 32,314 | `__pycache__` | Python bytecode cache |
| 311 | `skills/torch_geometric/scripts/__pycache__/benchmark_model.cpython-310.pyc` | 8,616 | `*.pyc` | Python compiled bytecode |
| 312 | `skills/torch_geometric/scripts/__pycache__/create_gnn_template.cpython-310.pyc` | 15,422 | `*.pyc` | Python compiled bytecode |
| 313 | `skills/torch_geometric/scripts/__pycache__/visualize_graph.cpython-310.pyc` | 8,276 | `*.pyc` | Python compiled bytecode |
| 314 | `skills/treatment-plans/scripts/__pycache__` | 33,955 | `__pycache__` | Python bytecode cache |
| 315 | `skills/treatment-plans/scripts/__pycache__/check_completeness.cpython-310.pyc` | 8,279 | `*.pyc` | Python compiled bytecode |
| 316 | `skills/treatment-plans/scripts/__pycache__/generate_template.cpython-310.pyc` | 6,494 | `*.pyc` | Python compiled bytecode |
| 317 | `skills/treatment-plans/scripts/__pycache__/timeline_generator.cpython-310.pyc` | 9,182 | `*.pyc` | Python compiled bytecode |
| 318 | `skills/treatment-plans/scripts/__pycache__/validate_treatment_plan.cpython-310.pyc` | 10,000 | `*.pyc` | Python compiled bytecode |
| 319 | `skills/uniprot-database/scripts/__pycache__` | 8,790 | `__pycache__` | Python bytecode cache |
| 320 | `skills/uniprot-database/scripts/__pycache__/uniprot_client.cpython-310.pyc` | 8,790 | `*.pyc` | Python compiled bytecode |
| 321 | `skills/uspto-database/scripts/__pycache__` | 25,614 | `__pycache__` | Python bytecode cache |
| 322 | `skills/uspto-database/scripts/__pycache__/patent_search.cpython-310.pyc` | 8,280 | `*.pyc` | Python compiled bytecode |
| 323 | `skills/uspto-database/scripts/__pycache__/peds_client.cpython-310.pyc` | 8,363 | `*.pyc` | Python compiled bytecode |
| 324 | `skills/uspto-database/scripts/__pycache__/trademark_client.cpython-310.pyc` | 8,971 | `*.pyc` | Python compiled bytecode |
| 325 | `tests/__pycache__` | 288 | `__pycache__` | Python bytecode cache |
| 326 | `tests/__pycache__/test_basic.cpython-310.pyc` | 288 | `*.pyc` | Python compiled bytecode |

## 🟡 中置信度（LIKELY_TMP）

临时日志：通常可删除，建议抽查

| # | 路径 | 大小 (B) | 模式 | 理由 |
|---:|---|---:|---|---|
| 1 | `ar.log` | 0 | `\.log$` | runtime log |
| 2 | `audit.log` | 241 | `\.log$` | runtime log |
| 3 | `cm.log` | 202 | `\.log$` | runtime log |
| 4 | `cm2.log` | 526 | `\.log$` | runtime log |
| 5 | `cm3.log` | 890 | `\.log$` | runtime log |
| 6 | `dep.log` | 495 | `\.log$` | runtime log |
| 7 | `extr2.log` | 778 | `\.log$` | runtime log |
| 8 | `extracted_doc.err` | 0 | `\.err$` | stderr capture |
| 9 | `fd.log` | 205 | `\.log$` | runtime log |
| 10 | `fix.log` | 1,134 | `\.log$` | runtime log |
| 11 | `fl.log` | 111 | `\.log$` | runtime log |
| 12 | `hp.log` | 574 | `\.log$` | runtime log |
| 13 | `lf.log` | 236 | `\.log$` | runtime log |
| 14 | `mv.log` | 1,182 | `\.log$` | runtime log |
| 15 | `ov.log` | 1,881 | `\.log$` | runtime log |
| 16 | `pc.log` | 0 | `\.log$` | runtime log |
| 17 | `pf.log` | 59 | `\.log$` | runtime log |
| 18 | `pf3.log` | 145 | `\.log$` | runtime log |
| 19 | `pip.log` | 326 | `\.log$` | runtime log |
| 20 | `reports/cleanup_logon.log` | 90,811 | `\.log$` | runtime log |
| 21 | `s2.log` | 620 | `\.log$` | runtime log |
| 22 | `strict.log` | 939 | `\.log$` | runtime log |
| 23 | `ug.log` | 117 | `\.log$` | runtime log |
| 24 | `ug2.log` | 61 | `\.log$` | runtime log |
| 25 | `vf.log` | 1,061 | `\.log$` | runtime log |

## 🔴 低置信度（UNTRACKED）

git 未追踪：业务产物或临时输出，需人工判定

| # | 路径 | 大小 (B) | 模式 | 理由 |
|---:|---|---:|---|---|
| 1 | `cross_check_result.txt` | 6,558 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 2 | `diag.txt` | 0 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 3 | `doc_utf8.txt` | 15,504 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 4 | `extracted_doc.err` | 0 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 5 | `extracted_doc.txt` | 11,651 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 6 | `extracted_review_doc.txt` | 13,769 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 7 | `output_doc_full.txt` | 56,325 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 8 | `scripts/generate_norovirus_trial_lit_docx.py` | 17,491 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 9 | `scripts/norovirus_trial_search.py` | 7,141 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |
| 10 | `verify_result.txt` | 3,664 | `(untracked)` | git untracked file (NOT in .gitignore); business deliverable or temp output |

## 受保护文件（不会处理）

```
  cleanup_plan.md
  docs/audit_phase1.md
  docs/cleanup_phase2_plan.md
  reports/phase2_scan.json
  review_report.md
  scripts_consolidation_analysis.md
  verify_data_result.txt
```

## 待用户指令

- 全部批准：回复「**批准删除**」将执行 HIGH + MEDIUM 全部；LOW 跳过
- 仅 HIGH：回复「**仅高置信度**」
- 列出子集：回复「**仅删除 X, Y, Z**」
- 全部拒绝：回复「**取消**」

## 回滚预案

- 当前基线 commit: `0e5207a`
- 回滚命令: `git reset --hard 0e5207a`（会丢弃所有 untracked 工作）
- 软回滚（保留工作）: `git reset --soft 0e5207a`
