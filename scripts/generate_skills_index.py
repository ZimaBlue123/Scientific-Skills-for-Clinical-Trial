"""Auto-generate a categorized skills index from SKILL.md frontmatter.

Scans all ``skills/*/SKILL.md`` files, parses their YAML frontmatter, assigns
each skill to a category based on keyword rules, and writes a formatted
``SKILLS_INDEX.md`` with tables grouped by category.

Inspired by the ``public-apis/public-apis`` README structure — a giant Markdown
table organized into categories with counts, descriptions, and metadata.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

# --------------------------------------------------------------------------- #
# YAML frontmatter parser (lightweight, no PyYAML dependency)
# --------------------------------------------------------------------------- #

_FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _extract_frontmatter(text: str) -> str | None:
    m = _FM_RE.match(text)
    return m.group(1) if m else None


def _top_level_entries(frontmatter: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in frontmatter.splitlines():
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m:
            entries[m.group(1)] = m.group(2).strip()
    return entries


def _metadata_scalars(frontmatter: str) -> dict[str, str]:
    lines = frontmatter.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("metadata:"))
    except StopIteration:
        return {}
    scalars: dict[str, str] = {}
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith((" ", "\t")):
            break
        m = re.match(r"^  ([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m and m.group(2).strip():
            scalars[m.group(1)] = m.group(2).strip().strip("\"'")
    return scalars


def _resolve_description(frontmatter: str, value: str) -> str:
    if value and value not in (">", ">-", "|", "|-"):
        return value.strip("\"'")
    lines = frontmatter.splitlines()
    desc_lines: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith("description:"):
            collecting = True
            continue
        if collecting:
            if line.startswith((" ", "\t")):
                desc_lines.append(line.strip())
            else:
                break
    return " ".join(desc_lines)


# --------------------------------------------------------------------------- #
# Skill data model
# --------------------------------------------------------------------------- #

@dataclass
class SkillInfo:
    name: str
    description: str
    version: str
    license: str
    category: str
    has_scripts: bool


# --------------------------------------------------------------------------- #
# Category classification engine
# --------------------------------------------------------------------------- #

# Order matters: first match wins.  More specific patterns come before general.
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("🧬 生物信息学 & 基因组学", [
        "alphafold", "anndata", "biopython", "cellxgene", "deeptools",
        "ena-database", "ensembl", "esm", "etetoolkit", "flowio", "gene-database",
        "geniml", "geo-database", "gget", "gnomad", "gtars", "gwas-database",
        "histolab", "lamindb", "neurokit2", "neuropixels", "pathml",
        "pathogen-variant", "pysam", "pydeseq2", "scanpy", "scikit-bio",
        "scvi-tools", "tiledbvcf", "umap-learn", "zarr-python",
    ]),
    ("💊 临床试验 & 合规", [
        "clinical-", "clinicaltrials", "clinpgx", "clinvar", "csr-stage",
        "fda-database", "iso-standards", "treatment-plans", "word-audit",
        "pptx-gmc-sync", "analytical-method",
    ]),
    ("📄 文档处理 & 报告生成", [
        "document-skills", "document-format", "clinical-docx", "clinical-pdf",
        "clinical-ppt", "clinical-word", "clinical-excel", "clinical-sae",
        "markitdown", "latex-posters", "pptx-posters", "infographics",
        "scientific-slides", "scientific-writing", "paper-2-web",
        "markdown-mermaid",
    ]),
    ("📊 统计分析 & 建模", [
        "statistical-", "statsmodels", "scikit-learn", "scikit-survival",
        "shap", "pymc", "pymoo", "experimental-design", "exploratory-data",
        "hypothesis-generation", "statistical-power", "timesfm",
        "pkpd-modeling", "antibody-kinetics",
    ]),
    ("🔬 化学 & 药物设计", [
        "rdkit", "datamol", "deepchem", "medchem", "molfeat", "pubchem",
        "chembl", "drugbank", "zinc-database", "pytdc", "diffdock",
        "matchms", "pyopenms", "cobrapy", "rowan",
    ]),
    ("📚 文献检索 & 知识管理", [
        "pubmed", "openalex", "biorxiv", "paper-lookup", "literature-review",
        "citation-management", "pyzotero", "bgpt-paper", "perplexity",
        "custom-pubmed", "peer-review", "scientific-schematics",
    ]),
    ("🗃️ 数据库接口", [
        "database-lookup", "brenda", "cosmic", "hmdb", "kegg",
        "metabolomics-workbench", "opentargets", "pdb-database",
        "reactome", "string-database", "uniprot", "bioservices",
        "datacommons", "ontology-term", "imaging-data",
    ]),
    ("📈 数据可视化", [
        "matplotlib", "plotly", "seaborn", "scientific-visualization",
        "fireworks-tech-graph", "networkx",
    ]),
    ("🧪 实验设计 & 实验室集成", [
        "benchling", "dnanexus", "ginkgo", "labarchive", "latchbio",
        "omero", "opentrons", "protocolsio", "pylabrobot", "adaptyv",
        "open-notebook",
    ]),
    ("💰 金融 & 经济数据", [
        "alpha-vantage", "fred-economic", "edgartools", "hedgefundmonitor",
        "denario", "usfiscaldata",
    ]),
    ("🔧 量子计算 & 物理", [
        "cirq", "qiskit", "pennylane", "qutip", "astropy", "pymatgen",
        "fluidsim", "sympy",
    ]),
    ("🤖 机器学习 & 深度学习", [
        "pytorch-lightning", "transformers", "stable-baselines3",
        "torch_geometric", "torchdrug", "pufferlib", "hypogenic",
    ]),
    ("🛠️ 通用工具", [
        "dask", "polars", "vaex", "simpy", "modal", "matlab", "aeon",
        "arboreto", "geopandas", "geomaster", "get-available-resources",
        "github-proxy-push", "generate-image", "market-research",
        "pydicom", "pyhealth", "usptodata", "uspto",
    ]),
]


def _classify(skill_name: str) -> str:
    """Assign a category to a skill based on its name."""
    lower = skill_name.lower()
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in lower:
                return category
    return "🛠️ 通用工具"


# --------------------------------------------------------------------------- #
# Index generation
# --------------------------------------------------------------------------- #

def _scan_skills(skills_dir: Path) -> list[SkillInfo]:
    """Scan all skills and extract metadata."""
    skills: list[SkillInfo] = []

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue

        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue

        fm = _extract_frontmatter(text)
        if fm is None:
            skills.append(SkillInfo(
                name=skill_dir.name,
                description="⚠️ Missing frontmatter",
                version="—",
                license="—",
                category=_classify(skill_dir.name),
                has_scripts=any((skill_dir / "scripts").rglob("*"))
                if (skill_dir / "scripts").is_dir() else False,
            ))
            continue

        entries = _top_level_entries(fm)
        meta = _metadata_scalars(fm)

        desc_raw = entries.get("description", "")
        desc = _resolve_description(fm, desc_raw)
        # Truncate for table display
        if len(desc) > 120:
            desc = desc[:117] + "..."

        lic = entries.get("license", "—").strip("\"'")
        if lic in ("Unknown", ""):
            lic = "—"

        skills.append(SkillInfo(
            name=skill_dir.name,
            description=desc,
            version=meta.get("version", "—"),
            license=lic,
            category=_classify(skill_dir.name),
            has_scripts=any((skill_dir / "scripts").rglob("*"))
            if (skill_dir / "scripts").is_dir() else False,
        ))

    return skills


def _generate_index(skills: list[SkillInfo]) -> str:
    """Generate the SKILLS_INDEX.md content."""
    lines: list[str] = [
        "# Skills Index",
        "",
        "<!-- ⚠️ AUTO-GENERATED — do not edit manually. -->",
        f"<!-- Generated by scripts/generate_skills_index.py on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -->",
        "",
        f"本项目共包含 **{len(skills)}** 个 AI Skills，按功能领域分类如下。",
        "",
    ]

    # Build table of contents
    by_cat: dict[str, list[SkillInfo]] = {}
    for s in skills:
        by_cat.setdefault(s.category, []).append(s)

    # Preserve category order from CATEGORY_RULES
    cat_order = [cat for cat, _ in CATEGORY_RULES]
    # Add any uncategorized
    for cat in by_cat:
        if cat not in cat_order:
            cat_order.append(cat)

    lines.append("## 目录\n")
    for cat in cat_order:
        if cat not in by_cat:
            continue
        count = len(by_cat[cat])
        anchor = re.sub(r"[^\w\s-]", "", cat).strip().lower().replace(" ", "-")
        anchor = re.sub(r"-+", "-", anchor)
        lines.append(f"- [{cat} ({count})](#{anchor}-{count})")
    lines.append("")

    # Build category sections
    for cat in cat_order:
        if cat not in by_cat:
            continue
        cat_skills = by_cat[cat]
        count = len(cat_skills)
        lines.append(f"## {cat} ({count})\n")
        lines.append("| Skill | Description | Version | License | Scripts |")
        lines.append("|-------|-------------|---------|---------|---------|")

        for s in sorted(cat_skills, key=lambda x: x.name.lower()):
            scripts_badge = "✅" if s.has_scripts else "—"
            # Escape pipe characters in description
            desc = s.description.replace("|", "\\|")
            lines.append(
                f"| [{s.name}](skills/{s.name}/SKILL.md) "
                f"| {desc} "
                f"| {s.version} "
                f"| {s.license} "
                f"| {scripts_badge} |"
            )
        lines.append("")

    # Summary footer
    with_scripts = sum(1 for s in skills if s.has_scripts)
    lines.append("---\n")
    lines.append(f"**总计**: {len(skills)} skills | "
                 f"{with_scripts} 含自定义脚本 | "
                 f"{len(by_cat)} 个分类")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-generate categorized SKILLS_INDEX.md from SKILL.md frontmatter.",
    )
    parser.add_argument(
        "--out", type=str, default=None,
        help="Output file path (default: SKILLS_INDEX.md at repo root)",
    )
    parser.add_argument(
        "--skills-dir", type=str, default=None,
        help="Path to skills directory (default: auto-detect)",
    )
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir) if args.skills_dir else SKILLS_DIR
    if not skills_dir.is_dir():
        print(f"ERROR: skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    skills = _scan_skills(skills_dir)
    if not skills:
        print("ERROR: no skills found", file=sys.stderr)
        sys.exit(1)

    content = _generate_index(skills)

    out_path = args.out or str(REPO_ROOT / "SKILLS_INDEX.md")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated index with {len(skills)} skills → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
