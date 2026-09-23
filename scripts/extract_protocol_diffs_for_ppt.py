#!/usr/bin/env python
"""
提取两份乙肝疫苗 III 期方案文本（含修订痕迹）与参考 PPT 文本，供设计层面差异比对使用。

- 新版（痕迹版）: 保留 w:ins / w:del 标记，输出为 [+新增+] / [-删除-]
- 旧版（clean）: 纯文本
- 参考 PPT: 按页输出文字（含表格与备注）
输出目录: reports/protocol_diff/
"""
import argparse
import os

from docx import Document
from docx.oxml.ns import qn
from pptx import Presentation

BASE = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial"
OUT = os.path.join(BASE, "reports", "protocol_diff")

NEW_DOCX = os.path.join(
    BASE, "review_materials",
    "远大赛威信重组乙型肝炎疫苗（CpG和铝佐剂）Ⅲ期临床方案摘要 - 20260922-痕迹版（根据CDE沟通会意见调整）.docx",
)
OLD_DOCX = os.path.join(
    BASE, "review_materials",
    "远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）Ⅲ期临床方案-V1.0-20260526-clean.docx",
)
REF_PPTX = os.path.join(
    BASE, "review_materials", "15-F2F会议", "细胞免疫",
    "TVAX-009_细胞免疫_Ⅰ期结果与Ⅲ期设计调整-20260922.pptx",
)


def iter_block_items(parent):
    """按文档顺序遍历段落与表格。"""
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def para_text_tracked(p):
    """返回段落文本，带修订标记: [+ins+] / [-del-]"""
    out = []
    for node in p._p.iter():
        if node.tag == qn("w:ins"):
            continue
        if node.tag == qn("w:del"):
            continue
    # 逐 run 处理，同时识别 run 所在的最近修订祖先
    from docx.text.run import Run

    def nearest_rev(run_el):
        el = run_el
        while el is not None:
            tag = el.tag
            if tag == qn("w:ins"):
                return "ins"
            if tag == qn("w:del"):
                return "del"
            el = el.getparent()
        return None

    # 段落级直接子节点遍历（保留 w:ins/w:del 包裹的 run）
    for child in p._p.iterchildren():
        if child.tag == qn("w:r"):
            run = Run(child, p)
            t = run.text
            if not t:
                continue
            rev = nearest_rev(child)
            out.append(t)
        elif child.tag == qn("w:ins"):
            seg = "".join(r.text or "" for r in child.iter(qn("w:r")))
            # 也包含可能嵌套的 delText（罕见）
            if seg:
                out.append("[+" + seg + "+]")
        elif child.tag == qn("w:del"):
            seg = "".join(
                "".join(t.text or "" for t in dt.iter(qn("w:delText")))
                for dt in child.iter(qn("w:r"))
            )
            if seg:
                out.append("[-" + seg + "-]")
        elif child.tag == qn("w:hyperlink"):
            seg = "".join(t.text or "" for t in child.iter(qn("w:t")))
            if seg:
                out.append(seg)
    # 修订属性（rPr change / pPr change）
    if p._p.find(qn("w:pPr")) is not None:
        ppr = p._p.find(qn("w:pPr"))
        if ppr is not None and ppr.find(qn("w:rPr")) is not None:
            rpr = ppr.find(qn("w:rPr"))
            if rpr is not None and rpr.find(qn("w:ins")) is not None:
                pass
    return "".join(out)


def para_text_plain(p):
    return p.text


def dump_docx(path, tracked):
    doc = Document(path)
    lines = []
    for block in iter_block_items(doc):
        from docx.table import Table

        if isinstance(block, Table):
            lines.append("[[TABLE]]")
            for row in block.rows:
                cells = []
                for c in row.cells:
                    ct = []
                    for p in c.paragraphs:
                        ct.append(para_text_tracked(p) if tracked else para_text_plain(p))
                    cells.append(" ".join(x for x in ct if x).strip())
                lines.append(" | ".join(cells))
            lines.append("[[/TABLE]]")
        else:
            txt = para_text_tracked(block) if tracked else para_text_plain(block)
            if txt.strip():
                lines.append(txt.strip())
    return lines


def shape_text(sp):
    parts = []
    if sp.has_text_frame:
        for p in sp.text_frame.paragraphs:
            t = "".join(r.text or "" for r in p.runs)
            if t.strip():
                parts.append(t.strip())
    if getattr(sp, "has_table", False) and sp.has_table:
        parts.append("[[TABLE]]")
        for row in sp.table.rows:
            cells = []
            for c in row.cells:
                ct = []
                for p in c.text_frame.paragraphs:
                    t = "".join(r.text or "" for r in p.runs)
                    if t.strip():
                        ct.append(t.strip())
                cells.append(" ".join(ct))
            parts.append(" | ".join(cells))
        parts.append("[[/TABLE]]")
    return parts


def dump_pptx(path):
    prs = Presentation(path)
    pages = []
    for i, slide in enumerate(prs.slides, 1):
        buf = []
        buf.append(f"[slide {i}] layout={slide.slide_layout.name}")
        for sp in slide.shapes:
            if sp.shape_type is not None and sp.has_text_frame if sp.has_text_frame else False:
                pass
            parts = shape_text(sp)
            if parts:
                buf.extend(parts)
        if slide.has_notes_slide:
            nt = slide.notes_slide.notes_text_frame.text.strip()
            if nt:
                buf.append("[[NOTES]] " + nt.replace("\n", " / "))
        pages.append("\n".join(buf))
    return pages


def main():
    ap = argparse.ArgumentParser(description="导出 docx/pptx 文本（docx 可保留修订痕迹）")
    ap.add_argument("paths", nargs="*", help="待导出的 docx/pptx 路径；缺省则按内置的三份方案/PPT 对比任务执行")
    ap.add_argument("--tracked", action="store_true", help="docx 保留 [+新增+] / [-删除-] 修订标记")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)

    if args.paths:
        for p in args.paths:
            p = os.path.abspath(p)
            if p.lower().endswith(".pptx"):
                pages = dump_pptx(p)
                text = "\n\n".join(pages)
            else:
                text = "\n".join(dump_docx(p, tracked=args.tracked))
            dst = os.path.join(OUT, os.path.splitext(os.path.basename(p))[0][:80] + ".txt")
            with open(dst, "w", encoding="utf-8") as f:
                f.write(text)
            print("dumped ->", dst)
        return

    old_lines = dump_docx(OLD_DOCX, tracked=False)
    new_lines = dump_docx(NEW_DOCX, tracked=True)
    ppt_pages = dump_pptx(REF_PPTX)

    with open(os.path.join(OUT, "old_v1.0_20260526.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(old_lines))
    with open(os.path.join(OUT, "new_20260922_tracked.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    with open(os.path.join(OUT, "ref_ppt_20260922.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(ppt_pages))

    # 仅输出含修订标记的段落，便于快速定位修改点
    tracked_only = [l for l in new_lines if "[+" in l or "[-" in l]
    with open(os.path.join(OUT, "new_tracked_only.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tracked_only))

    print("old lines:", len(old_lines))
    print("new lines:", len(new_lines))
    print("tracked lines:", len(tracked_only))
    print("ppt pages:", len(ppt_pages))


if __name__ == "__main__":
    main()
