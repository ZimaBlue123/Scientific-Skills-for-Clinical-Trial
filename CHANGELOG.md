# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **`scripts/common_scripts/generator_base.py`**: Added OSError guards to `save_document()` and `load_template()` with `logger.exception()` and `raise RuntimeError` on failure, replacing silent pass-throughs that could mask data-loss bugs.

### Changed
- **Phase 3 (2026-08-07) — configuration alignment**:
  - `.gitignore`: confirmed comprehensive; no changes needed.
  - `requirements.txt`: confirmed all active dependencies declared; no changes needed.
  - `README.md`: removed stale references to deleted scripts (`convert_doc_to_docx.py`, `extract_docx_to_md.py`, `convert_audit_report_md_to_docx.py`, `_extract_docx_text.py`); fixed duplicate line; updated deprecated-scripts table to reflect actual file inventory.
- **Phase 2 (2026-08-07) — redundant file cleanup**: removed 5 root-level temp files, 53 stale report files, 231 `.pyc` files, 77 `__pycache__/` directories, `.ruff_cache/`, and the emptied `review_materials/` directory.
- **Phase 1 (2026-08-07) — code quality baseline**: audited 32 active Python scripts with ruff (0 errors); auto-fixed import ordering and deprecated UTF-8 declarations; hardened `generator_base.py` with OSError guards. Safety baseline committed as `8254cec`.
- **Refactor (2026-07-30)**: audited 240 .py files and fixed a UTF-8 BOM in `scripts/verify_data.py`; removed 351 stale `__pycache__/` directories and `.log` artifacts; added `requests>=2.31`, `scipy>=1.10`, `lxml>=4.9`, `defusedxml>=0.7` to `requirements.txt`.
- **scripts/ consolidation**: 19 root-level `.py` files migrated into `scripts/`, `scripts/_tools/`, and `scripts/_archive_2026_consolidation/`.
- **README / README.en**: removed duplicated sections and stray Chinese sentences in English README.
- **.gitignore**: added archive types and IDE/Mavis/Claude local-state exclusions.
- **Documentation**: added `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.

### Notes
- No source code semantics were changed; the goal was repository cleanup and documentation correctness.
- Self-check (`scripts/project_self_check.py`) still reports import-time failures for skills whose third-party dependencies are not installed locally; this is expected on a developer machine.

## Earlier history

See git log for the detailed commit history prior to the introduction of this changelog. Key milestones:

- Initial extraction and curation of clinical-research skills from [`K-Dense-AI/claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills).
- Integration of [`fireworks-tech-graph`](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) (MIT) under `skills/`.
- Establishment of the bilingual `README.md` / `README.en.md`, `docs/skills_guide.md`, `docs/skills_catalog.md`, and `docs/repo_layout.md`.
- Standardization of the in-repo skill policy via `.cursor/rules/skills-location-policy.mdc`.
