from __future__ import annotations

import argparse
import heapq
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class SkillDoc:
    skill_path: str  # relative to skills/
    file_path: str
    tf: Counter


def _tokenize(markdown_text: str) -> List[str]:
    # Remove large code blocks and inline code to focus on semantic prose.
    text = re.sub(r"```[\s\S]*?```", " ", markdown_text)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = text.lower()
    return re.findall(r"[a-z0-9\u4e00-\u9fff]+", text)


def _iter_skill_docs(skills_root: Path) -> Iterable[SkillDoc]:
    for dp, _, fns in os.walk(skills_root):
        if "SKILL.md" not in fns:
            continue
        file_path = Path(dp) / "SKILL.md"
        skill_path = os.path.relpath(dp, str(skills_root)).replace("\\", "/")
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            print(f"WARN: failed to read {file_path}: {e}", file=sys.stderr)
            continue
        toks = _tokenize(text)
        yield SkillDoc(skill_path=skill_path, file_path=str(file_path), tf=Counter(toks))


def _idf(docs: List[SkillDoc]) -> Dict[str, float]:
    df = Counter()
    for d in docs:
        df.update(d.tf.keys())
    n = len(docs)
    return {t: math.log((n + 1) / (dfv + 1)) + 1.0 for t, dfv in df.items()}


def _tfidf(tf: Counter, idf: Dict[str, float]) -> Dict[str, float]:
    w: Dict[str, float] = {}
    for t, v in tf.items():
        w[t] = (1.0 + math.log(v)) * idf.get(t, 0.0)
    return w


def _l2_norm(w: Dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in w.values())) or 1.0


def _cosine(a: Dict[str, float], an: float, b: Dict[str, float], bn: float) -> float:
    # iterate smaller dict
    if len(a) > len(b):
        a, b, an, bn = b, a, bn, an
    dot = 0.0
    for t, vt in a.items():
        dot += vt * b.get(t, 0.0)
    return dot / (an * bn)


def build_report(
    repo_root: Path,
    skills_subdir: str = "skills",
    out_path: str = "docs/skill_dedupe_report.md",
    cosine_threshold: float = 0.87,
    top_k: int = 120,
) -> Tuple[int, int]:
    if not (0.0 <= cosine_threshold <= 1.0):
        raise ValueError(f"cosine_threshold must be within [0, 1], got {cosine_threshold}")
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")

    skills_root = repo_root / skills_subdir
    if not skills_root.exists():
        raise FileNotFoundError(f"skills root not found: {skills_root}")

    docs = list(_iter_skill_docs(skills_root))
    if not docs:
        # Still write a report so CI/docs stay consistent.
        (repo_root / "docs").mkdir(parents=True, exist_ok=True)
        full_out = repo_root / out_path
        full_out.parent.mkdir(parents=True, exist_ok=True)
        full_out.write_text(
            "# SKILL.md 深度去重报告（内容相似度）\n\n"
            f"- SKILL 数量：0\n"
            f"- 阈值：cosine >= {cosine_threshold}\n"
            f"- 命中对数（>=阈值）：0\n\n"
            "未发现任何可分析的 SKILL.md（请检查 skills 目录结构）。\n",
            encoding="utf-8",
        )
        return 0, 0

    idf = _idf(docs)

    vecs = []
    for d in docs:
        w = _tfidf(d.tf, idf)
        n = _l2_norm(w)
        vecs.append((d.skill_path, d.file_path, w, n))

    # Full pairwise cosine; keep a heap for Top-K and also keep all >= threshold.
    top_heap: List[Tuple[float, str, str]] = []
    hits: List[Tuple[float, str, str]] = []

    for i in range(len(vecs)):
        ai, _, wi, ni = vecs[i]
        for j in range(i + 1, len(vecs)):
            aj, _, wj, nj = vecs[j]
            sim = _cosine(wi, ni, wj, nj)
            if sim >= cosine_threshold:
                hits.append((sim, ai, aj))
            # Maintain top_k most similar (regardless of threshold) for discovery.
            if len(top_heap) < top_k:
                heapq.heappush(top_heap, (sim, ai, aj))
            else:
                if sim > top_heap[0][0]:
                    heapq.heapreplace(top_heap, (sim, ai, aj))

    hits.sort(reverse=True)
    top_all = sorted(top_heap, reverse=True)

    (repo_root / "docs").mkdir(parents=True, exist_ok=True)
    full_out = repo_root / out_path
    full_out.parent.mkdir(parents=True, exist_ok=True)
    with open(full_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# SKILL.md 深度去重报告（内容相似度）\n\n")
        f.write(f"- SKILL 数量：{len(docs)}\n")
        f.write(f"- 阈值：cosine >= {cosine_threshold}\n")
        f.write(f"- 命中对数（>=阈值）：{len(hits)}\n\n")

        f.write("## 命中对（>=阈值）\n\n")
        if not hits:
            f.write("未发现达到阈值的高相似对。\n")
        else:
            for sim, a, b in hits[:top_k]:
                f.write(f"- **{sim:.3f}**: `{a}`  <->  `{b}`\n")

        f.write("\n## 发现用：全库最相似 Top（不受阈值限制）\n\n")
        for sim, a, b in top_all[:top_k]:
            f.write(f"- **{sim:.3f}**: `{a}`  <->  `{b}`\n")

    return len(docs), len(hits)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SKILL.md similarity dedupe report.")
    parser.add_argument("--threshold", type=float, default=0.87, help="Cosine similarity threshold.")
    parser.add_argument("--top", type=int, default=120, help="Top N pairs to keep in report.")
    parser.add_argument(
        "--skills-subdir",
        type=str,
        default="skills",
        help="Skills directory name relative to repo root (default: skills).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="docs/skill_dedupe_report.md",
        help="Output markdown path (relative to repo root).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    try:
        skill_count, pair_count = build_report(
            repo_root=repo_root,
            skills_subdir=args.skills_subdir,
            out_path=args.out,
            cosine_threshold=args.threshold,
            top_k=args.top,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(2)
    print(f"Wrote {args.out} (skills={skill_count}, pairs={pair_count})")


if __name__ == "__main__":
    main()

