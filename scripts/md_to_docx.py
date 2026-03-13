#!/usr/bin/env python3
"""
Markdown 转 Word 文档转换脚本
将审核报告等 Markdown 文件转换为格式优化的 Word 文档，便于阅读和打印。

依赖: pip install python-docx
可选: 安装 pandoc 可获得更佳转换效果（自动检测）

用法:
  python scripts/md_to_docx.py [input.md] [-o output.docx]
  python scripts/md_to_docx.py                                    # 默认转换审核报告
  python scripts/md_to_docx.py report.md -o report.docx
  python scripts/md_to_docx.py --no-pandoc                        # 仅用 python-docx
"""

import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("请安装 python-docx: pip install python-docx")
    sys.exit(1)


def add_hyperlink(paragraph, text, url):
    """在段落中添加超链接"""
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    rPr.append(color)
    rPr.append(underline)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)
    return hyperlink


def parse_markdown(md_text):
    """解析 Markdown 为结构化块"""
    blocks = []
    lines = md_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 表格
        if stripped.startswith("|") and "|" in stripped[1:]:
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [cell.strip() for cell in lines[i].split("|")[1:-1]]
                # 跳过分隔行 |---|---|
                if not all(re.match(r'^[-:]+$', c.replace(" ", "")) for c in row if c):
                    table_rows.append(row)
                i += 1
            if table_rows:
                blocks.append(("table", table_rows))
            continue

        # 一级标题 #
        if stripped.startswith("# ") and not stripped.startswith("## "):
            blocks.append(("h1", stripped[2:].strip()))
            i += 1
            continue

        # 二级标题 ##
        if stripped.startswith("## ") and not stripped.startswith("### "):
            blocks.append(("h2", stripped[3:].strip()))
            i += 1
            continue

        # 三级标题 ###
        if stripped.startswith("### "):
            blocks.append(("h3", stripped[4:].strip()))
            i += 1
            continue

        # 分隔线 ---
        if stripped in ("---", "***", "___"):
            blocks.append(("hr", None))
            i += 1
            continue

        # 空行
        if not stripped:
            blocks.append(("blank", None))
            i += 1
            continue

        # 普通段落（合并连续非空行）
        para_lines = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", "|", "---", "***")):
            para_lines.append(lines[i].strip())
            i += 1
        blocks.append(("paragraph", " ".join(para_lines)))

    return blocks


def process_inline_formatting(text, paragraph, doc):
    """处理段落内格式：粗体、链接"""
    # 匹配 [text](url) 或 **text**
    pattern = re.compile(r'(\*\*(.+?)\*\*|\[(.+?)\]\((https?://[^)]+)\))')
    last_end = 0

    for m in pattern.finditer(text):
        # 添加匹配前的普通文本
        if m.start() > last_end:
            run = paragraph.add_run(text[last_end:m.start()])
            run.font.size = Pt(10.5)
            run.font.name = "微软雅黑"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

        if m.group(4):  # [text](url) - 链接
            add_hyperlink(paragraph, m.group(3), m.group(4))
        elif m.group(2):  # **bold**
            run = paragraph.add_run(m.group(2))
            run.bold = True
            run.font.size = Pt(10.5)
            run.font.name = "微软雅黑"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

        last_end = m.end()

    if last_end < len(text):
        run = paragraph.add_run(text[last_end:])
        run.font.size = Pt(10.5)
        run.font.name = "微软雅黑"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def add_simple_formatted_paragraph(paragraph, text, bold_parts=None):
    """添加带格式的段落（简化版：支持粗体）"""
    # 分割 **text** 格式
    parts = re.split(r'(\*\*.+?\*\*)', text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2] + " ")
            run.bold = True
        else:
            run = paragraph.add_run(part)
        run.font.size = Pt(10.5)
        run.font.name = "微软雅黑"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def md_to_docx(md_path, docx_path=None):
    """将 Markdown 转为 Word 文档"""
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"文件不存在: {md_path}")

    if docx_path is None:
        docx_path = md_path.with_suffix(".docx")
    else:
        docx_path = Path(docx_path)

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = Document()

    # 页面设置
    section = doc.sections[0]
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)

    blocks = parse_markdown(md_text)

    for block_type, content in blocks:
        if block_type == "h1":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(content)
            run.bold = True
            run.font.size = Pt(18)
            run.font.name = "微软雅黑"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
            p.paragraph_format.space_after = Pt(12)

        elif block_type == "h2":
            p = doc.add_paragraph(content, style="Heading 1")
            p.runs[0].font.name = "微软雅黑"
            p.runs[0]._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
            p.runs[0].font.size = Pt(14)
            p.runs[0].bold = True
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)

        elif block_type == "h3":
            p = doc.add_paragraph(content, style="Heading 2")
            p.runs[0].font.name = "微软雅黑"
            p.runs[0]._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
            p.runs[0].font.size = Pt(12)
            p.runs[0].bold = True
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)

        elif block_type == "paragraph":
            if not content.strip():
                continue
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.25  # 1.25 倍行距
            # 检查是否包含链接
            if re.search(r'\[.+\]\(https?://', content):
                try:
                    process_inline_formatting(content, p, doc)
                except Exception:
                    add_simple_formatted_paragraph(p, content)
            else:
                add_simple_formatted_paragraph(p, content)

        elif block_type == "table":
            if not content:
                continue
            rows = len(content)
            cols = max(len(r) for r in content)
            table = doc.add_table(rows=rows, cols=cols)
            table.style = "Light Grid Accent 1"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            for ri, row_data in enumerate(content):
                row = table.rows[ri]
                for ci, cell_text in enumerate(row_data):
                    if ci < len(row.cells):
                        cell = row.cells[ci]
                        cell.text = cell_text
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_after = Pt(2)
                            for run in paragraph.runs:
                                run.font.size = Pt(9)
                                run.font.name = "微软雅黑"
                                run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
                        # 表头行加粗
                        if ri == 0:
                            for paragraph in cell.paragraphs:
                                for run in paragraph.runs:
                                    run.bold = True

            doc.add_paragraph()  # 表后空行

        elif block_type == "hr":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.border_bottom = None  # 可选：添加底线

        elif block_type == "blank":
            doc.add_paragraph()

    # 设置默认字体
    for para in doc.paragraphs:
        for run in para.runs:
            if run.font.name is None or run.font.name == "Calibri":
                run.font.name = "微软雅黑"
                run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    doc.save(docx_path)
    print(f"已生成: {docx_path.absolute()}")
    return docx_path


def try_pandoc(md_path, docx_path):
    """若已安装 pandoc，优先使用其转换（效果更好）"""
    try:
        import subprocess
        result = subprocess.run(
            ["pandoc", str(md_path), "-o", str(docx_path), "--from", "markdown", "--to", "docx"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"[pandoc] 已生成: {docx_path.absolute()}")
            return True
    except (FileNotFoundError, subprocess.SubprocessError, Exception):
        pass
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Markdown 转 Word（优化格式、便于阅读）")
    parser.add_argument("input", nargs="?", default="review_materials/YDSWX-TVAX-006-001-阶段性小结-审核报告.md",
                        help="输入的 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出的 Word 文件路径")
    parser.add_argument("--no-pandoc", action="store_true", help="不使用 pandoc，仅用 python-docx")
    args = parser.parse_args()

    # 相对路径基于项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    md_path = project_root / args.input if not Path(args.input).is_absolute() else Path(args.input)

    output = args.output
    if output:
        output = Path(output) if Path(output).is_absolute() else project_root / output
    else:
        output = md_path.with_suffix(".docx")

    if not args.no_pandoc and try_pandoc(md_path, output):
        return

    md_to_docx(md_path, output)


if __name__ == "__main__":
    main()
