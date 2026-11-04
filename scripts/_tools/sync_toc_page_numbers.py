# -*- coding: utf-8 -*-
"""把 Word 实际分页结果回写进 docx 的目录（TOC）缓存页码。

场景：用 python-docx 生成/修改文档后，为保持原文件版式不动（不走 Word 保存），
但目录里缓存的静态页码已过期。做法：
  1. 用 Word COM 打开副本、刷新 TOC、读出每个条目的真实页码；
  2. 用 lxml 只改原文件 TOC 段落里最后一个 w:t 的文字（页码），其余一律不动。

用法：
  python scripts/_tools/sync_toc_page_numbers.py <docx>            # 探测并回写
  python scripts/_tools/sync_toc_page_numbers.py <docx> --check     # 只比对不写
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


def read_word_toc(docx_path: Path) -> list[tuple[str, str]]:
    """用 Word 刷新目录后返回 [(标题文本, 页码), ...]。"""
    import win32com.client as win32

    tmp = Path(tempfile.gettempdir()) / ("_toc_probe_" + docx_path.name)
    shutil.copy2(docx_path, tmp)
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    out: list[tuple[str, str]] = []
    try:
        doc = word.Documents.Open(str(tmp), ReadOnly=False,
                                  AddToRecentFiles=False, Visible=False)
        for i in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents(i).Update()
        doc.Repaginate()
        rng = doc.TablesOfContents(1).Range
        for k in range(1, rng.Paragraphs.Count + 1):
            t = rng.Paragraphs(k).Range.Text.replace("\r", "").replace("\x07", "")
            t = t.replace("\t", "\t").strip("\n")
            if not t.strip():
                continue
            # 形如 "16.2.2支持性数据\t16"
            parts = t.rsplit("\t", 1)
            if len(parts) == 2 and parts[1].strip().isdigit():
                out.append((parts[0].strip(), parts[1].strip()))
    finally:
        if doc is not None:
            doc.Close(SaveChanges=0)
        word.Quit()
        tmp.unlink(missing_ok=True)
    return out


def toc_paragraph_texts(doc) -> list[str]:
    res = []
    for p in doc.paragraphs:
        if p.style is not None and p.style.name.upper().startswith("TOC"):
            res.append(p.text)
    return res


def current_toc_pairs(doc) -> list[tuple[str, str]]:
    out = []
    for p in doc.paragraphs:
        if p.style is None or not p.style.name.upper().startswith("TOC"):
            continue
        t = p.text.replace("\x07", "")
        parts = t.rsplit("\t", 1)
        if len(parts) == 2 and parts[1].strip().isdigit():
            out.append((parts[0].strip(), parts[1].strip()))
    return out


def set_last_wt(paragraph, text: str) -> bool:
    ts = list(paragraph._p.iter(qn("w:t")))
    if not ts:
        return False
    ts[-1].text = text
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Synchronize cached TOC page numbers in a .docx via Word COM.")
    ap.add_argument("docx")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = Path(args.docx).resolve()
    if not path.is_file():
        print(f"[ERR] File not found: {path}", file=sys.stderr)
        return 1
    doc = Document(str(path))
    cur = current_toc_pairs(doc)
    truth = read_word_toc(path)

    if len(cur) != len(truth):
        print(f"[WARN] 条目数不一致：缓存 {len(cur)}，Word {len(truth)}")

    diffs = []
    for (ct, cp), (tt, tp) in zip(cur, truth):
        if ct != tt:
            print(f"[WARN] 标题不匹配：{ct!r} vs {tt!r}")
        if cp != tp:
            diffs.append((ct, cp, tp))

    if not diffs:
        print("[OK] 目录页码与 Word 实际分页一致，无需修改。")
        return 0

    print("需要更新的条目：")
    for ct, cp, tp in diffs:
        print(f"  {ct[:50]:<50} {cp} -> {tp}")

    if args.check:
        print("\n[--check] 未写入。")
        return 0

    n = 0
    for p in doc.paragraphs:
        if p.style is None or not p.style.name.upper().startswith("TOC"):
            continue
        t = p.text.replace("\x07", "")
        parts = t.rsplit("\t", 1)
        if len(parts) != 2 or not parts[1].strip().isdigit():
            continue
        head, page = parts[0].strip(), parts[1].strip()
        for ct, cp, tp in diffs:
            if ct == head and cp == page:
                if set_last_wt(p, tp):
                    n += 1
                break

    doc.save(str(path))
    print(f"\n[OK] 已回写 {n} 个页码：{path.name}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    raise SystemExit(main())
