"""
把逐字稿写入 PPTX 每页的备注页，并同步导出一份 Word 版逐字稿。

用法:
    python inject_pptx_notes_and_export_docx.py <源pptx> <逐字稿json> <输出pptx> <输出docx>

JSON 结构:
{
  "meta": {"source": "...", "speech_rate_cn_chars_per_min": 220, "target_minutes": 30},
  "slides": [{"page": 1, "seconds": 40, "text": "..."}, ...]
}
"""

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from pptx import Presentation


def load_script(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    rate_per_sec = meta.get("speech_rate_cn_chars_per_min", 220) / 60.0

    scripts = {}
    for s in data["slides"]:
        text = s["text"]
        chars = len(text.replace("\n", ""))
        # 未显式给出 seconds 时，按语速自动折算，并留出少量换气停顿
        seconds = s.get("seconds") or int(round(chars / rate_per_sec))
        scripts[int(s["page"])] = {
            "page": int(s["page"]),
            "text": text,
            "seconds": seconds,
            "chars": chars,
        }
    return meta, scripts


def inject_notes(pptx_path: Path, out_pptx: Path, scripts: dict) -> int:
    prs = Presentation(str(pptx_path))
    if len(prs.slides) != len(scripts):
        print(f"[WARN] PPT 页数 {len(prs.slides)} 与逐字稿条数 {len(scripts)} 不一致")

    written = 0
    for idx, slide in enumerate(prs.slides, start=1):
        item = scripts.get(idx)
        if not item:
            continue
        notes = f"【建议时长：约{item['seconds']}秒】\n\n{item['text']}"
        slide.notes_slide.notes_text_frame.text = notes
        written += 1

    out_pptx.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_pptx))
    return written


def slide_title(pptx_path: Path) -> dict:
    """提取每页的标题文本（取首个非空文本块）。"""
    prs = Presentation(str(pptx_path))
    titles = {}
    for idx, slide in enumerate(prs.slides, start=1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                t = shape.text_frame.text.strip().replace("\n", " ")
                if t:
                    texts.append(t)
        titles[idx] = texts[0][:60] if texts else ""
    return titles


def export_docx(out_docx: Path, scripts: dict, titles: dict, meta: dict, pptx_path: Path):
    rate = meta.get("speech_rate_cn_chars_per_min", 220)
    doc = Document()

    # 默认中文字体
    style = doc.styles["Normal"]
    style.font.name = "Microsoft YaHei"
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia",
        "微软雅黑",
    )

    h = doc.add_heading("TVAX-009 III期临床试验启动前沟通会｜汇报逐字稿", level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(
        f"源文件：{pptx_path.name}　|　共 {len(scripts)} 页　|　按中文约 {rate} 字/分钟语速估算"
    )
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph()

    total_chars = sum(len(s["text"].replace("\n", "")) for s in scripts.values())
    total_sec = sum(s["seconds"] for s in scripts.values())
    t = doc.add_table(rows=1, cols=4)
    t.style = "Light Grid Accent 1"
    hdr = t.rows[0].cells
    for i, v in enumerate(["总字数", "建议总时长", "平均每页", "目标时长"]):
        hdr[i].text = v
    row = t.add_row().cells
    row[0].text = f"{total_chars} 字"
    row[1].text = f"{total_sec // 60} 分 {total_sec % 60} 秒"
    row[2].text = f"{total_sec / len(scripts):.1f} 秒"
    row[3].text = f"{meta.get('target_minutes', 30)} 分钟"

    doc.add_page_break()

    for idx in sorted(scripts):
        item = scripts[idx]
        text = item["text"].replace("\n", "")
        hp = doc.add_heading(f"第 {idx} 页", level=2)
        hp.add_run(f"　{titles.get(idx, '')}").font.size = Pt(11)

        meta_p = doc.add_paragraph()
        r = meta_p.add_run(f"建议时长：约 {item['seconds']} 秒　|　正文 {len(text)} 字")
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

        for para in item["text"].split("\n"):
            p = doc.add_paragraph(para)
            p.paragraph_format.space_after = Pt(6)
        doc.add_paragraph()

    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_docx))
    return total_chars, total_sec


def main():
    pptx_path = Path(sys.argv[1])
    json_path = Path(sys.argv[2])
    out_pptx = Path(sys.argv[3])
    out_docx = Path(sys.argv[4])

    meta, scripts = load_script(json_path)
    titles = slide_title(pptx_path)

    n = inject_notes(pptx_path, out_pptx, scripts)
    print(f"[OK] 已写入备注页：{n} 页 -> {out_pptx}")

    chars, secs = export_docx(out_docx, scripts, titles, meta, pptx_path)
    print(
        f"[OK] Word 已生成：{out_docx}　总字数 {chars}　建议总时长 {secs // 60} 分 {secs % 60} 秒"
    )


if __name__ == "__main__":
    main()
