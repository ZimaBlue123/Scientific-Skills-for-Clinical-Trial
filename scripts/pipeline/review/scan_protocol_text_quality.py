#!/usr/bin/env python3
"""Scan a numbered protocol markdown for typos, grammar and formatting defects.

Companion to ``audit_protocol_numeric_consistency.py`` (which looks at numbers);
this one looks at *language*:

  1. placeholders            - ``<待定>``, ``XX``, ``××`` left in the text
  2. quote styles            - mixing “ ” / " " / ' ' inside one document
  3. full-width punctuation  - ``．，：［］`` used inside Latin-script references
  4. digit-for-letter        - ``oligonuc1eotides`` (the digit 1 between letters)
  5. dose-unit wording       - 针 vs 剂 used for the same concept
  6. duplicated punctuation  - ？？ ，， 。。 ；；
  7. unit spacing            - ``4.0~5.0mL`` vs ``4.0~5.0 mL`` in the same file
  8. spelling watchlist      - known misspellings seen in earlier versions
  9. colloquial / vague      - 拉齐、远远高于、大约、五分之几 …

Usage
-----
    python scripts/scan_protocol_text_quality.py \
        review_materials/converted/<protocol>.md
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PLACEHOLDER = re.compile(r"<待定>|××+|[X]{2,}")
FULLWIDTH = re.compile(r"[．，：；［］（）]")
DIGIT_FOR_L = re.compile(r"(?<=[A-Za-z])1(?=[A-Za-z])")
DUP_PUNCT = re.compile(r"([。，；：、？！])\1")
UNIT_TIGHT = re.compile(r"\d\s?[~—-]\s?\d?\.?\d*\s?(mL|ml|mIU/mL|mIU/ml)")
ZH_QUOTE = "“”"
EN_QUOTE = "\""

WATCHLIST = [
    "at al.", "et a1", "atoll-like", "atoll ", "e la Hoz", "Janssena",
    "Mangoo-Karimb", "药物注册管理办法", "疫苗临床不良事件分级",
    "oligonuc1", "Klasehik", "Pergola. et al",
]

COLLOQUIAL = [
    "拉齐", "远远高于", "大约有", "五分之三", "五分之二", "五分之",
    "三针", "两针", "一针", "针免疫", "有待", "等相关", "等等",
]

DOSE_ZHEN = re.compile(r"[两三一二四五六]针|[0-9]针")


def iter_blocks(text: str):
    anchor = None
    buf: list[str] = []
    for line in text.split("\n"):
        m = re.match(r"^##\s+(P|T)(\d+)\s*$", line.strip())
        if m:
            if anchor:
                yield anchor, "\n".join(buf).strip()
            anchor = f"{m.group(1)}{m.group(2)}"
            buf = []
        elif anchor is not None:
            buf.append(line)
    if anchor:
        yield anchor, "\n".join(buf).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--show", type=int, default=3, help="examples per finding")
    args = ap.parse_args()

    text = Path(args.markdown).read_text(encoding="utf-8")
    blocks = list(iter_blocks(text))
    print(f"FILE : {Path(args.markdown).name}")
    print(f"BLOCKS: {len(blocks)}")
    print("=" * 70)

    findings: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for anchor, body in blocks:
        if not body:
            continue
        if PLACEHOLDER.search(body):
            findings["1 占位符残留"].append((anchor, PLACEHOLDER.search(body).group(0)))
        if FULLWIDTH.search(body) and re.search(r"[A-Za-z]{4,}", body):
            findings["3 英文内容中的全角标点"].append(
                (anchor, FULLWIDTH.search(body).group(0))
            )
        if DIGIT_FOR_L.search(body):
            findings["4 数字1误代字母l"].append((anchor, DIGIT_FOR_L.search(body).group(0)))
        if DUP_PUNCT.search(body):
            findings["6 重复标点"].append((anchor, DUP_PUNCT.search(body).group(0)))
        for word in WATCHLIST:
            if word in body:
                findings["8 已知错拼/错误名称"].append((anchor, word))
        for word in COLLOQUIAL:
            if word in body:
                findings["9 口语化/不精确表述"].append((anchor, word))
        if DOSE_ZHEN.search(body):
            findings["5 剂量单位“针”"].append((anchor, DOSE_ZHEN.search(body).group(0)))

    # ---- quote style census
    zh = text.count("“") + text.count("”")
    en = text.count(EN_QUOTE)
    print(f"\n[2] 引号使用统计：中文引号 “” {zh} 处；英文直引号 \" {en} 处")
    if zh and en:
        print("    → 混用，建议统一为中文引号（正文）")

    # ---- unit spacing census
    tight = len(re.findall(r"\d\s?[~—-]\s?\d+(?:\.\d+)?(mL|ml|mIU/mL|mIU/ml)", text))
    spaced = len(re.findall(r"\d\s?[~—-]\s?\d+(?:\.\d+)?\s+(mL|ml|mIU/mL|mIU/ml)", text))
    print(f"\n[7] 单位书写：数字与单位连写 {tight} 处；带空格 {spaced} 处")
    if tight and spaced:
        print("    → 不一致，建议择一统一")

    print()
    for key in sorted(findings):
        items = findings[key]
        print(f"[{key[0]}] {key[2:]}  —— {len(items)} 处")
        for anchor, sample in items[: args.show]:
            print(f"      {anchor:<6} {sample}")
        if len(items) > args.show:
            print(f"      …（共 {len(items)} 处）")
        print()

    if not findings:
        print("未发现上述类型的缺陷。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
