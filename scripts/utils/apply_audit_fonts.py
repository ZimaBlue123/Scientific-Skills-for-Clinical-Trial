"""为审计报告 docx 全局应用宋体/Times New Roman 中英文字体。

依据: skills/word-audit-report-format/SKILL.md
- ASCII/HAnsi/CS: Times New Roman
- East Asia: 宋体
- 覆盖样式: Normal, Title, Heading 1-3, Table Grid
"""

from __future__ import annotations

from pathlib import Path

from docx import Document  # type: ignore
from docx.styles.style import _ParagraphStyle  # type: ignore

ASCII_FONT = "Times New Roman"
EAST_ASIA_FONT = "宋体"
STYLES_TO_SET = [
    "Normal",
    "Title",
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Table Grid",
    "List Bullet",
    "List Number",
]


def _set_run_fonts(style: _ParagraphStyle) -> None:
    """在样式级别统一中英文字体，含 East Asia XML 注入。"""
    from docx.oxml import OxmlElement  # type: ignore
    from docx.oxml.ns import qn  # type: ignore

    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    # ascii / hAnsi / cs (英文 / Latin)
    rfonts.set(qn("w:ascii"), ASCII_FONT)
    rfonts.set(qn("w:hAnsi"), ASCII_FONT)
    rfonts.set(qn("w:cs"), ASCII_FONT)
    # eastAsia / eastAsiaTheme (中文/东亚)
    rfonts.set(qn("w:eastAsia"), EAST_ASIA_FONT)


def _walk_all_paragraph_runs(doc: Document) -> None:
    """对所有段落与表格中的运行直接覆盖字体（确保非样式引用也生效）。"""
    from docx.oxml import OxmlElement  # type: ignore
    from docx.oxml.ns import qn  # type: ignore

    def _set_run_fonts(run):
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.insert(0, rfonts)
        rfonts.set(qn("w:ascii"), ASCII_FONT)
        rfonts.set(qn("w:hAnsi"), ASCII_FONT)
        rfonts.set(qn("w:cs"), ASCII_FONT)
        rfonts.set(qn("w:eastAsia"), EAST_ASIA_FONT)

    for para in doc.paragraphs:
        for run in para.runs:
            _set_run_fonts(run)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        _set_run_fonts(run)


def apply_audit_fonts(in_path: Path, out_path: Path) -> None:
    doc: Document = Document(str(in_path))

    # 1) 样式级别（覆盖样式表）
    for style_name in STYLES_TO_SET:
        try:
            style = doc.styles[style_name]
            _set_run_fonts(style)
        except KeyError:
            # 缺少该样式时跳过
            pass

    # 2) 运行级别（覆盖已写入的字面 run）
    _walk_all_paragraph_runs(doc)

    doc.save(str(out_path))


if __name__ == "__main__":
    import sys

    in_p = Path(sys.argv[1])
    out_p = Path(sys.argv[2]) if len(sys.argv) > 2 else in_p
    apply_audit_fonts(in_p, out_p)
    print(f"fonts applied: {out_p}")
