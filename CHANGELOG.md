# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **`scripts/common_scripts/generator_base.py`**: Added OSError guards to `save_document()` and `load_template()` with `logger.exception()` and `raise RuntimeError` on failure, replacing silent pass-throughs that could mask data-loss bugs.

### Added
- **Clinical Data Automation capability layer (2026-09-18)**: vendored the external
  `1-Clinical Data Automation` toolkit under `scripts/clinical-automation/` with its full
  history preserved. Modules 25, 26, 27, 28, 29, 30, 31 and 32 were deliberately not
  imported, so directory numbering is intentionally non-contiguous.
- **Ten capability skills (2026-09-18)**: `clinical-pdf-ectd`, `clinical-sae-extraction`,
  `clinical-word-tables`, `clinical-pdf-extraction`, `clinical-docx-editing`,
  `clinical-excel-charts`, `clinical-pdf-hygiene`, `clinical-ppt-toolkit`,
  `document-format-convert`, `clinical-document-translation`. Each is a documentation-only
  skill that points at the vendored scripts, so no code is duplicated.
- **`scripts/audit_robustness_smells.py`**: AST audit for bare `except:`, silently swallowed
  handlers, encoding-less text opens, mutable default arguments, `shell=True`, `os.system`
  and hardcoded absolute paths. Scoped to repository-owned code so the vendored subtree stays
  byte-identical.

### Changed
- **Phase 1 (2026-09-18) — code quality baseline**: 92 repository-owned Python files audited
  with pyflakes (0 findings) and the new robustness auditor (0 blocking findings); 420 files
  re-checked for encoding declarations (0 missing). The ten new skills now carry `license`,
  `compatibility`, `allowed-tools` and a `metadata` block, satisfying the frontmatter rule in
  `tests/_contract/structure.py`. Safety baseline committed as `2f7f4bc`.
- **Phase 2 (2026-09-18) — redundant file cleanup**: removed 122 stale `__pycache__/`
  directories left behind by the vendored toolkit import.
- **Phase 3 (2026-09-18) — configuration alignment**: `requirements.txt` verified against every
  third-party import in repository-owned code — all 18 are declared, no changes needed.
  `.gitignore` confirmed comprehensive. `plugin.json` is still absent from the repository root,
  which is a known pre-existing gap in `tests/_meta` (see Notes).
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
- **Known pre-existing gap:** `tests/_meta/test_repo_contract.py` does not pass on this checkout,
  and did not before this refactor. Running it without pytest reproduces 259 failures across 165
  skills, almost all from `frontmatter` (no `metadata` block) and `local_links_resolve`
  (SKILL.md paths written relative to the repository root rather than to the skill directory).
  `plugin.json` has never existed in the repository, so `AgentPluginTests` fails on the missing
  file. The six `shell_scripts` failures are a Windows artifact: git does not preserve the
  executable bit for `.sh` files here. Bringing the remaining 165 skills into conformance is a
  separate, repo-wide remediation and was deliberately not folded into this run.
- Self-check (`scripts/project_self_check.py`) still reports import-time failures for skills whose third-party dependencies are not installed locally; this is expected on a developer machine.

## Earlier history

See git log for the detailed commit history prior to the introduction of this changelog. Key milestones:

- Initial extraction and curation of clinical-research skills from [`K-Dense-AI/claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills).
- Integration of [`fireworks-tech-graph`](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) (MIT) under `skills/`.
- Establishment of the bilingual `README.md` / `README.en.md`, `docs/skills_guide.md`, `docs/skills_catalog.md`, and `docs/repo_layout.md`.
- Standardization of the in-repo skill policy via `.cursor/rules/skills-location-policy.mdc`.
