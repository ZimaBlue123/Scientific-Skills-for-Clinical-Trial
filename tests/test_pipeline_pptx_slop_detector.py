"""Unit tests for ``scripts/pipeline/validate/pptx_slop_detector.py``."""

from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pipeline.validate.pptx_slop_detector import (  # noqa: E402
    main,
    scan_pptx_slop,
    summarize_slop,
)


def _make_clean_deck(path: Path) -> None:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9.0), Inches(0.8))
    run = tb.text_frame.paragraphs[0].add_run()
    run.text = "TVAX-033 Phase II Immunogenicity Summary"
    run.font.name = "Arial"
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)

    tbl_shape = slide.shapes.add_table(2, 2, Inches(0.5), Inches(1.5), Inches(8.5), Inches(1.2))
    cell = tbl_shape.table.cell(0, 0)
    c_run = cell.text_frame.paragraphs[0].add_run()
    c_run.text = "Cohort A (n=120)"
    c_run.font.name = "Arial"
    c_run.font.size = Pt(11)
    c_run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    prs.save(str(path))


def _make_slop_deck(path: Path) -> None:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 1) Placeholder + micro-font + low contrast on filled box
    card_outer = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.4), Inches(0.4), Inches(8.0), Inches(4.5)
    )
    card_outer.fill.solid()
    card_outer.fill.fore_color.rgb = RGBColor(0xAA, 0xAA, 0xAA)

    for idx, font_name in enumerate(("Arial", "Calibri", "Georgia", "Verdana")):
        inner = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.6 + idx * 1.8),
            Inches(0.8),
            Inches(1.6),
            Inches(1.2),
        )
        inner.fill.solid()
        inner.fill.fore_color.rgb = RGBColor(0xAA, 0xAA, 0xAA)
        r = inner.text_frame.paragraphs[0].add_run()
        r.text = "[待补充] TODO" if idx == 0 else f"Item {idx}"
        r.font.name = font_name
        r.font.size = Pt(7) if idx == 0 else Pt(11)
        r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    prs.save(str(path))


def test_clean_deck_passes_with_zero_floor_and_reflex(tmp_path: Path):
    pptx_path = tmp_path / "clean.pptx"
    _make_clean_deck(pptx_path)
    findings = scan_pptx_slop(pptx_path)
    summary = summarize_slop(findings)
    assert summary["by_tier"]["floor"] == 0
    assert summary["by_tier"]["reflex"] == 0
    assert main([str(pptx_path), "--strict"]) == 0


def test_slop_deck_catches_floor_and_reflex_rules(tmp_path: Path):
    pptx_path = tmp_path / "slop.pptx"
    _make_slop_deck(pptx_path)
    findings = scan_pptx_slop(pptx_path)
    rules = {f.rule for f in findings}
    assert "placeholder-remnant" in rules
    assert "micro-font" in rules
    assert "low-contrast-text" in rules
    assert "font-family-sprawl" in rules
    assert "nested-card-stack" in rules
    assert main([str(pptx_path)]) == 1
