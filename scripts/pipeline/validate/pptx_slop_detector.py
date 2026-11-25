"""Deterministic anti-AI-slop visual & layout linter for PowerPoint (.pptx) decks.

Inspired by Hallmark (Floor / Reflex / Finish tiers) and Impeccable (P0-P3
deterministic slop rules), this validator requires zero LLM/API calls and pairs
with ``pptx_overflow_checker.py`` to catch template bloat before delivery.

Public API
----------
- ``SlopFinding``
- ``scan_pptx_slop``
- ``summarize_slop``
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EMU_PER_INCH = 914400.0
MIN_FONT_PT = 9.0
MIN_CONTRAST_RATIO = 3.0
MAX_SLIDE_FONTS = 3
MAX_SLIDE_TEXT_UNITS = 450
MAX_ACCENT_COLORS = 5

_PLACEHOLDER_RE = re.compile(
    r"(?:\b(?:TODO|TBD|FIXME)\b|lorem\s+ipsum|\[待补充\]|\[此处填写\]|<placeholder>)",
    re.IGNORECASE,
)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_WORD_RE = re.compile(r"[A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class SlopFinding:
    slide: int
    tier: str
    severity: str
    rule: str
    detail: str


def _srgb_channel(val: int) -> float:
    c = val / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    return (
        0.2126 * _srgb_channel(rgb[0])
        + 0.7152 * _srgb_channel(rgb[1])
        + 0.0722 * _srgb_channel(rgb[2])
    )


def _contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    l1, l2 = _relative_luminance(rgb1), _relative_luminance(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _rgb_tuple(color_obj: Any) -> tuple[int, int, int] | None:
    try:
        rgb = color_obj.rgb
    except AttributeError:
        return None
    if rgb is None:
        return None
    return (rgb[0], rgb[1], rgb[2])


def _shape_solid_fill_rgb(shape: Any) -> tuple[int, int, int] | None:
    try:
        fill = shape.fill
        if fill.type != 1:  # MSO_FILL.SOLID
            return None
        return _rgb_tuple(fill.fore_color)
    except (AttributeError, TypeError, ValueError):
        return None


def _count_text_units(text: str) -> int:
    return len(_CJK_RE.findall(text)) + len(_WORD_RE.findall(text))


def _box_contains(outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]) -> bool:
    ox1, oy1, ox2, oy2 = outer
    ix1, iy1, ix2, iy2 = inner
    return ox1 <= ix1 and oy1 <= iy1 and ox2 >= ix2 and oy2 >= iy2 and outer != inner


def _iter_slide_runs(slide: Any):
    for shape in slide.shapes:
        if shape.has_text_frame:
            shape_bg = _shape_solid_fill_rgb(shape)
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    yield shape, shape_bg, run
        if getattr(shape, "has_table", False):
            for row in shape.table.rows:
                for cell in row.cells:
                    cell_bg = _shape_solid_fill_rgb(cell)
                    for para in cell.text_frame.paragraphs:
                        for run in para.runs:
                            yield shape, cell_bg, run


def _scan_runs_on_slide(
    slide_num: int, slide: Any
) -> tuple[list[SlopFinding], set[str], set[tuple[int, int, int]]]:
    findings: list[SlopFinding] = []
    fonts: set[str] = set()
    accents: set[tuple[int, int, int]] = set()
    seen_placeholders: set[str] = set()

    for _shape, bg_rgb, run in _iter_slide_runs(slide):
        txt = run.text or ""
        if not txt.strip():
            continue

        m = _PLACEHOLDER_RE.search(txt)
        if m and m.group(0).lower() not in seen_placeholders:
            seen_placeholders.add(m.group(0).lower())
            findings.append(
                SlopFinding(
                    slide_num, "floor", "P0", "placeholder-remnant", f"Found {m.group(0)!r}"
                )
            )

        if run.font.size is not None and run.font.size.pt < MIN_FONT_PT:
            findings.append(
                SlopFinding(
                    slide_num,
                    "floor",
                    "P0",
                    "micro-font",
                    f"{run.font.size.pt:.1f}pt < {MIN_FONT_PT:.0f}pt ({txt.strip()[:30]!r})",
                )
            )

        if run.font.name:
            fonts.add(run.font.name)

        fg_rgb = _rgb_tuple(run.font.color)
        if fg_rgb is not None:
            if max(fg_rgb) - min(fg_rgb) > 60:
                accents.add(fg_rgb)
            if bg_rgb is not None:
                ratio = _contrast_ratio(fg_rgb, bg_rgb)
                if ratio < MIN_CONTRAST_RATIO:
                    findings.append(
                        SlopFinding(
                            slide_num,
                            "floor",
                            "P0",
                            "low-contrast-text",
                            f"contrast {ratio:.2f}:1 < {MIN_CONTRAST_RATIO:.1f}:1 "
                            f"({txt.strip()[:25]!r})",
                        )
                    )
    return findings, fonts, accents


def _is_eyebrow_text(shape: Any, txt: str) -> bool:
    return (
        bool(txt)
        and len(txt) <= 28
        and (shape.top / EMU_PER_INCH) < 1.0
        and (shape.height / EMU_PER_INCH) < 0.45
        and txt == txt.upper()
        and any(ch.isalpha() for ch in txt)
    )


def _is_empty_decorative_frame(shape: Any) -> bool:
    return (
        shape.shape_type == 1  # AUTO_SHAPE
        and not getattr(shape, "has_table", False)
        and not getattr(shape, "has_chart", False)
        and (shape.width / EMU_PER_INCH) > 0.5
        and (shape.height / EMU_PER_INCH) > 0.5
        and not (shape.has_text_frame and shape.text_frame.text.strip())
    )


def _evaluate_geometry_findings(
    slide_num: int,
    prose_units: int,
    filled_boxes: list[tuple[int, int, int, int]],
    all_boxes: list[tuple[int, int, int, int]],
    empty_frames: list[tuple[int, int, int, int]],
) -> list[SlopFinding]:
    findings: list[SlopFinding] = []
    if prose_units > MAX_SLIDE_TEXT_UNITS:
        findings.append(
            SlopFinding(
                slide_num,
                "reflex",
                "P1",
                "text-wall",
                f"{prose_units} non-table text units > {MAX_SLIDE_TEXT_UNITS}",
            )
        )

    nested_count = sum(
        1 for inner in filled_boxes if any(_box_contains(outer, inner) for outer in filled_boxes)
    )
    if nested_count >= 2 and len(filled_boxes) >= 3:
        findings.append(
            SlopFinding(
                slide_num,
                "reflex",
                "P2",
                "nested-card-stack",
                f"{nested_count} nested filled card shapes on slide",
            )
        )

    for frame in empty_frames:
        if not any(_box_contains(frame, other) for other in all_boxes):
            findings.append(
                SlopFinding(
                    slide_num, "finish", "P3", "empty-decorative-frame", "Empty AutoShape frame"
                )
            )
    return findings


def _scan_slide_geometry(
    slide_num: int,
    slide: Any,
    accents: set[tuple[int, int, int]],
) -> tuple[list[SlopFinding], bool]:
    prose_units = 0
    filled_boxes: list[tuple[int, int, int, int]] = []
    all_boxes: list[tuple[int, int, int, int]] = []
    empty_frames: list[tuple[int, int, int, int]] = []
    has_eyebrow = False

    for shape in slide.shapes:
        box = (
            int(shape.left),
            int(shape.top),
            int(shape.left + shape.width),
            int(shape.top + shape.height),
        )
        all_boxes.append(box)
        fill_rgb = _shape_solid_fill_rgb(shape)
        if fill_rgb is not None:
            if max(fill_rgb) - min(fill_rgb) > 60:
                accents.add(fill_rgb)
            if not getattr(shape, "has_table", False):
                filled_boxes.append(box)

        if shape.has_text_frame and not getattr(shape, "has_table", False):
            txt = shape.text_frame.text.strip()
            prose_units += _count_text_units(txt)
            if _is_eyebrow_text(shape, txt):
                has_eyebrow = True
        elif _is_empty_decorative_frame(shape):
            empty_frames.append(box)

    findings = _evaluate_geometry_findings(
        slide_num, prose_units, filled_boxes, all_boxes, empty_frames
    )
    return findings, has_eyebrow


def scan_pptx_slop(pptx_path: str | Path) -> list[SlopFinding]:
    """Scan a .pptx file and return deterministic Floor / Reflex / Finish findings."""
    path = Path(pptx_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    from pptx import Presentation

    prs = Presentation(str(path))
    findings: list[SlopFinding] = []
    eyebrow_slides: list[int] = []

    for idx, slide in enumerate(prs.slides, 1):
        run_findings, fonts, accents = _scan_runs_on_slide(idx, slide)
        findings.extend(run_findings)
        if len(fonts) > MAX_SLIDE_FONTS:
            findings.append(
                SlopFinding(
                    idx,
                    "reflex",
                    "P1",
                    "font-family-sprawl",
                    f"{len(fonts)} font families ({', '.join(sorted(fonts))}) > {MAX_SLIDE_FONTS}",
                )
            )
        geom_findings, has_eyebrow = _scan_slide_geometry(idx, slide, accents)
        findings.extend(geom_findings)
        if has_eyebrow:
            eyebrow_slides.append(idx)
        if len(accents) > MAX_ACCENT_COLORS:
            findings.append(
                SlopFinding(
                    idx,
                    "reflex",
                    "P2",
                    "rainbow-accent-sprawl",
                    f"{len(accents)} saturated accent colors > {MAX_ACCENT_COLORS}",
                )
            )

    if len(eyebrow_slides) >= 3:
        findings.append(
            SlopFinding(
                eyebrow_slides[0],
                "reflex",
                "P2",
                "eyebrow-cliche",
                f"Repeated uppercase eyebrow tags on {len(eyebrow_slides)} slides: "
                f"{eyebrow_slides}",
            )
        )
    return findings


def summarize_slop(findings: list[SlopFinding]) -> dict[str, Any]:
    """Summarize findings by tier (floor / reflex / finish) and severity."""
    by_tier = {"floor": 0, "reflex": 0, "finish": 0}
    for item in findings:
        if item.tier in by_tier:
            by_tier[item.tier] += 1
    return {
        "total": len(findings),
        "by_tier": by_tier,
        "findings": [asdict(item) for item in findings],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pptx", help="Path to the .pptx file")
    ap.add_argument("--json", action="store_true", help="Emit JSON report")
    ap.add_argument(
        "--strict", action="store_true", help="Fail on reflex findings as well as floor"
    )
    args = ap.parse_args(argv)

    try:
        findings = scan_pptx_slop(args.pptx)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    summary = summarize_slop(findings)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(
                f"P{item.slide:02d} [{item.tier.upper()}/{item.severity}] "
                f"{item.rule}: {item.detail}"
            )
        print(
            f"SUMMARY: floor={summary['by_tier']['floor']} "
            f"reflex={summary['by_tier']['reflex']} finish={summary['by_tier']['finish']}"
        )

    if summary["by_tier"]["floor"] > 0:
        return 1
    if args.strict and summary["by_tier"]["reflex"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
