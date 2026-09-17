#!/usr/bin/env python
"""
verify_docx_toc_render.py

用本机 Microsoft Word (COM) 实际打开 .docx，**在临时副本上**更新域后导出 PDF /
首页 PNG，用于核验目录（TOC 域）能否正确生成目录条目与页码。

安全设计
--------
- 不直接打开目标文件：先复制一份 `_verify_copy.docx` 到输出目录，只操作副本，
  目标文件与源文件均不被修改。
- Word 关闭时不保存（SaveChanges=0），副本用后自动删除。

用法
----
    python verify_docx_toc_render.py "<待核验.docx>" [-o "<输出目录>"] [--pages 2]
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
from pathlib import Path

WD_EXPORT_FORMAT_PDF = 17
WD_DO_NOT_SAVE_CHANGES = 0


def _pymupdf():
    try:
        import fitz  # PyMuPDF

        return fitz
    except Exception:
        return None


def verify(docx_path: Path, out_dir: Path, pages: int = 1) -> dict:
    import win32com.client as win32

    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "_verify_copy.docx"
    pdf = out_dir / "_verify_preview.pdf"
    shutil.copy2(docx_path, work)

    result: dict = {"docx": str(docx_path), "pdf": str(pdf), "pngs": []}
    word = None
    doc = None
    try:
        word = win32.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(
            str(work), ConfirmConversions=False, ReadOnly=False, AddToRecentFiles=False
        )

        # 更新目录域（若自动更新未生效，这里兜底）
        toc_count = doc.TablesOfContents.Count
        for i in range(1, toc_count + 1):
            doc.TablesOfContents(i).Update()
        doc.Fields.Update()

        result["toc_count"] = toc_count
        result["page_count"] = doc.ComputeStatistics(2)  # wdStatisticPages
        result["toc_text"] = doc.TablesOfContents(1).Range.Text if toc_count else "(无目录域)"

        doc.ExportAsFixedFormat(str(pdf), WD_EXPORT_FORMAT_PDF)

        # 首页渲染 PNG
        fitz = _pymupdf()
        if fitz is not None and pdf.exists():
            with fitz.open(str(pdf)) as d:
                for i in range(min(pages, d.page_count)):
                    page = d.load_page(i)
                    pix = page.get_pixmap(dpi=110)
                    png = out_dir / f"_verify_page{i + 1}.png"
                    pix.save(str(png))
                    result["pngs"].append(str(png))
    finally:
        try:
            if doc is not None:
                doc.Close(WD_DO_NOT_SAVE_CHANGES)
        except Exception:
            pass
        try:
            if word is not None:
                word.Quit()
        except Exception:
            pass
        with contextlib.suppress(Exception):
            work.unlink(missing_ok=True)

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="用 Word 渲染核验 .docx 目录域")
    ap.add_argument("docx")
    ap.add_argument("-o", "--out-dir", default=None)
    ap.add_argument("--pages", type=int, default=1)
    args = ap.parse_args()

    src = Path(args.docx).resolve()
    if not src.exists():
        print(f"[ERROR] 文件不存在：{src}")
        return 2
    out_dir = Path(args.out_dir).resolve() if args.out_dir else src.parent / "_toc_verify"

    info = verify(src, out_dir, args.pages)

    print("===== Word 渲染核验 =====")
    print(f"核验文件  ：{info['docx']}")
    print(f"总页数    ：{info.get('page_count')}")
    print(f"目录域数量：{info.get('toc_count')}")
    print("----- 目录实际渲染内容 -----")
    print(info.get("toc_text", "").replace("\r", "\n").strip())
    print("----------------------------")
    print(f"PDF       ：{info['pdf']}")
    for p in info["pngs"]:
        print(f"页面截图  ：{p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
