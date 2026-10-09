#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract Word comments (with anchoring text) and body paragraphs from a .docx.

Usage:
    python extract_docx_review_comments.py <docx_path> [--body-only]

Output (stdout / file): Markdown
  PART 1  - comments: index | author | date | anchored text | comment body | context paragraph
  PART 2  - body paragraphs (non-empty) with paragraph index
"""

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def para_text(p):
    """Text of a w:p element (runs + tabs + breaks), ignoring deleted text."""
    out = []
    for node in p.iter():
        tag = node.tag
        if tag == W + "t":
            out.append(node.text or "")
        elif tag == W + "tab":
            out.append("\t")
        elif tag in (W + "br", W + "cr"):
            out.append("\n")
    return "".join(out).strip()


def comment_body(c):
    return "\n".join(
        t for t in (para_text(p) for p in c.findall(W + "p")) if t
    ).strip()


def load(path: Path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    doc_xml = z.read("word/document.xml")
    comments_xml = z.read("word/comments.xml") if "word/comments.xml" in names else None
    return doc_xml, comments_xml, names


def extract_comments(path: Path):
    doc_xml, comments_xml, _ = load(path)
    root = ET.fromstring(doc_xml)

    # --- map comment id -> anchored text (between commentRangeStart/End)
    body = root.find(W + "body")
    anchors = {}
    open_ranges = {}
    texts = []  # (kind, id, text)

    def walk(container, in_table=False):
        for el in container:
            tag = el.tag
            if tag == W + "commentRangeStart":
                open_ranges[el.get(W + "id")] = len(texts)
            elif tag == W + "commentRangeEnd":
                cid = el.get(W + "id")
                start = open_ranges.pop(cid, None)
                if start is not None:
                    anchors[cid] = "".join(t for k, i, t in texts if False) or ""
                    anchors[cid] = "".join(
                        seg for idx in range(start, len(texts)) for seg in [texts[idx][2]]
                    )
            elif tag == W + "p":
                t = para_text(el)
                texts.append(("p", None, t))
                for sub in el:
                    if sub.tag == W + "commentRangeStart":
                        open_ranges[sub.get(W + "id")] = len(texts) - 1
                    elif sub.tag == W + "commentRangeEnd":
                        cid = sub.get(W + "id")
                        start = open_ranges.pop(cid, None)
                        if start is not None:
                            anchors[cid] = "".join(texts[j][2] for j in range(start, len(texts)))
                # nested walk already handled inline; recurse for tables inside? no
            elif tag == W + "tbl":
                for tr in el.findall(W + "tr"):
                    for tc in tr.findall(W + "tc"):
                        for p in tc.findall(W + "p"):
                            t = para_text(p)
                            texts.append(("tc", None, t))
                            for sub in p:
                                if sub.tag == W + "commentRangeStart":
                                    open_ranges[sub.get(W + "id")] = len(texts) - 1
                                elif sub.tag == W + "commentRangeEnd":
                                    cid = sub.get(W + "id")
                                    start = open_ranges.pop(cid, None)
                                    if start is not None:
                                        anchors[cid] = "".join(
                                            texts[j][2] for j in range(start, len(texts))
                                        )

    walk(body)

    # --- paragraph index for context: rebuild ordered paragraph list
    paras = []
    for p in body.iter(W + "p"):
        paras.append(para_text(p))

    # --- comments
    comments = []
    if comments_xml is None:
        return comments, paras, anchors

    croot = ET.fromstring(comments_xml)
    for c in croot.findall(W + "comment"):
        cid = c.get(W + "id")
        initial = c.get(W + "initials") or ""
        author = c.get(W + "author") or ""
        date = c.get(W + "date") or ""
        text = comment_body(c)
        anch = (anchors.get(cid) or "").strip()
        # locate context paragraph: first paragraph containing anchor
        ctx = ""
        if anch:
            key = anch[:20]
            for p in paras:
                if key and key in p:
                    ctx = p
                    break
        comments.append(
            {
                "id": cid,
                "author": author,
                "initials": initial,
                "date": date,
                "anchor": anch,
                "text": text,
                "context": ctx,
            }
        )
    return comments, paras, anchors


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = Path(sys.argv[1])
    comments, paras, anchors = extract_comments(path)

    out = []
    out.append(f"# 批注与正文提取：{path.name}\n")
    out.append(f"批注总数：**{len(comments)}**\n")
    out.append("## PART 1 — 批注明细\n")
    for i, c in enumerate(comments, 1):
        out.append(f"### 批注 {i}  (comment id={c['id']})")
        out.append(f"- **作者**：{c['author']}（{c['initials']}）  **时间**：{c['date']}")
        out.append(f"- **锚定原文**：{c['anchor'] or '（未捕获，可能锚定在表格/图形）'}")
        out.append(f"- **批注正文**：{c['text']}")
        if c["context"]:
            out.append(f"- **所在段落**：{c['context']}")
        out.append("")
    out.append("## PART 2 — 正文段落（按序）\n")
    for i, p in enumerate(paras, 1):
        if p:
            out.append(f"{i}. {p}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
