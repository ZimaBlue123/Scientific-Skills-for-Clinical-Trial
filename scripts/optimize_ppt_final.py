"""
Optimise the merged PPT:
 - Delete 3 outer section marker slides (slides 1, 4, 11 in the original).
 - For section-3 internal CHAPTER dividers (slides 12, 14, 17, 19): keep them
   but tame the huge "01"/"02"/"03"/"04" numbers (165 pt -> 60 pt) and shrink
   subtitles/bullet text proportionally. Rename CHAPTER -> 03-1, 03-2 etc.
 - Global: white background, brand red (192,0,0) for slide-title text & table
   header rows.
 - Section 3 content slides: cap body text at 16pt, table cell text at 13pt,
   big stat numbers (66pt, 40.5pt etc.) scaled down by ~40%.
 - Section 1 & 2: gentle adjustments (title color, table header color) only.
"""

import codecs
import os
import re

import win32com.client


def rgb(r, g, b):
    return r + (g * 256) + (b * 65536)


WHITE = rgb(255, 255, 255)
RED = rgb(192, 0, 0)


# ---- helpers ----
def set_bg_white(slide):
    slide.FollowMasterBackground = False
    slide.Background.Fill.Solid()
    slide.Background.Fill.ForeColor.RGB = WHITE


def set_runs_color(text_range, color):
    try:
        for r in text_range.Runs():
            r.Font.Color.RGB = color
    except:
        try:
            text_range.Font.Color.RGB = color
        except:
            pass


def cap_runs_size(text_range, max_size, scale=None):
    """Cap every run's font size.  If *scale* is given, multiply first."""
    try:
        for r in text_range.Runs():
            sz = r.Font.Size
            if scale:
                sz = sz * scale
            if sz > max_size:
                sz = max_size
            r.Font.Size = sz
    except:
        pass


def is_outer_marker(slide, idx):
    """Return True for the 3 outer section-separator slides (01/02/03 …)."""
    for sh in slide.Shapes:
        if sh.HasTextFrame and sh.TextFrame.HasText:
            t = sh.TextFrame.TextRange.Text.strip().replace("\r", " ")
            # Pattern: "01 60岁以上..." / "02 CpG..." / "03 乙肝..."
            if (
                re.match(r"^0[123]\s", t)
                and "CHAPTER" not in t
                and "|" not in t
                and len(t) < 50
            ):
                return True
    return False


def is_chapter_divider(slide):
    """Return True for internal chapter divider pages inside section 3
    (they contain a shape with text '01'/'02'/'03'/'04' at 165 pt)."""
    for sh in slide.Shapes:
        if sh.HasTextFrame and sh.TextFrame.HasText:
            t = sh.TextFrame.TextRange.Text.strip()
            if t in ("01", "02", "03", "04"):
                try:
                    if sh.TextFrame.TextRange.Runs(1).Font.Size >= 100:
                        return True
                except:
                    pass
    return False


# ====================================================================
def main():
    folder = (
        r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials"
    )
    src = os.path.join(folder, "合并版-20260820_重新整合版.pptx")
    dst = os.path.join(folder, "合并版-20260820_最终优化版.pptx")

    if os.path.exists(dst):
        os.remove(dst)

    ppt = win32com.client.Dispatch("PowerPoint.Application")
    pres = ppt.Presentations.Open(src, WithWindow=False)

    # Force 16:9
    pres.PageSetup.SlideWidth = 960
    pres.PageSetup.SlideHeight = 540

    total = pres.Slides.Count
    log = codecs.open(
        r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\optimize_log.txt",
        "w",
        "utf-8",
    )

    # --- Pass 1: identify slides to delete (outer markers) ----
    to_delete = []
    for i in range(1, total + 1):
        if is_outer_marker(pres.Slides(i), i):
            to_delete.append(i)
            log.write(f"DELETE outer marker slide {i}\n")

    # --- Pass 2: classify remaining slides into sections ----
    # After outer markers are noted, assign section numbers.
    # Section boundaries are at indices in to_delete.
    # Section 1: after marker 1 until marker 2
    # Section 2: after marker 2 until marker 3
    # Section 3: after marker 3 until end
    section_map = {}  # slide_index -> section_number (1/2/3)
    current_sec = 0
    for i in range(1, total + 1):
        if i in to_delete:
            current_sec += 1
            continue
        section_map[i] = current_sec if current_sec > 0 else 1

    log.write(f"Section map: {section_map}\n")

    # --- Pass 3: apply formatting ----
    sec3_content_counter = 0  # for 03-x numbering
    sec1_counter = 0
    sec2_counter = 0

    for i in range(1, total + 1):
        if i in to_delete:
            continue
        slide = pres.Slides(i)
        sec = section_map.get(i, 0)
        set_bg_white(slide)

        is_chap_div = is_chapter_divider(slide)

        # ---- Find the "visual title" (topmost large text) ----
        title_shape = None
        title_top = 9999
        for sh in slide.Shapes:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                try:
                    sz = sh.TextFrame.TextRange.Runs(1).Font.Size
                    # For normal content slides, title is typically 18-28pt at the top
                    if sz >= 18 and sh.Top < title_top and sz < 100:
                        title_top = sh.Top
                        title_shape = sh
                except:
                    pass

        # ---- Section 1 & 2: gentle touch ----
        if sec in (1, 2):
            counter_ref = "sec1_counter" if sec == 1 else "sec2_counter"
            if sec == 1:
                sec1_counter += 1
                prefix = f"01-{sec1_counter}"
            else:
                sec2_counter += 1
                prefix = f"02-{sec2_counter}"

            # Title -> brand red + add prefix
            if title_shape:
                old = title_shape.TextFrame.TextRange.Text
                # Don't double-prefix
                if not re.match(r"^\d{2}-\d", old.strip()):
                    title_shape.TextFrame.TextRange.Text = f"{prefix} {old.lstrip()}"
                set_runs_color(title_shape.TextFrame.TextRange, RED)

            # Table headers -> red bg, white text
            for sh in slide.Shapes:
                if sh.HasTable:
                    t = sh.Table
                    for c in range(1, t.Columns.Count + 1):
                        cell = t.Cell(1, c)
                        cell.Shape.Fill.Solid()
                        cell.Shape.Fill.ForeColor.RGB = RED
                        if cell.Shape.HasTextFrame:
                            set_runs_color(cell.Shape.TextFrame.TextRange, WHITE)

        # ---- Section 3 ----
        elif sec == 3:
            sec3_content_counter += 1
            prefix = f"03-{sec3_content_counter}"

            if is_chap_div:
                # Tame the giant number & recolour
                for sh in slide.Shapes:
                    if sh.HasTextFrame and sh.TextFrame.HasText:
                        t = sh.TextFrame.TextRange.Text.strip()
                        if t in ("01", "02", "03", "04"):
                            # Shrink giant number
                            try:
                                for r in sh.TextFrame.TextRange.Runs():
                                    r.Font.Size = 54
                                    r.Font.Color.RGB = RED
                            except:
                                pass
                        elif t.startswith("CHAPTER"):
                            # Replace "CHAPTER 01" -> "03-x"
                            sh.TextFrame.TextRange.Text = prefix
                            set_runs_color(sh.TextFrame.TextRange, RED)
                            try:
                                for r in sh.TextFrame.TextRange.Runs():
                                    r.Font.Size = 14
                            except:
                                pass
                        else:
                            # Subtitle / bullet text
                            set_runs_color(sh.TextFrame.TextRange, RED)
                            cap_runs_size(sh.TextFrame.TextRange, 22)

                    # Recolour rectangles (left column bg)
                    if sh.Type == 1:  # msoAutoShape / Rectangle
                        try:
                            if sh.Fill.ForeColor.RGB != WHITE and sh.Width < 400:
                                sh.Fill.Solid()
                                sh.Fill.ForeColor.RGB = RED
                        except:
                            pass
            else:
                # Normal content slide in section 3
                # Add prefix to title
                if title_shape:
                    old = title_shape.TextFrame.TextRange.Text
                    if not re.match(r"^\d{2}-\d", old.strip()):
                        title_shape.TextFrame.TextRange.Text = (
                            f"{prefix} {old.lstrip()}"
                        )
                    set_runs_color(title_shape.TextFrame.TextRange, RED)

                # Process all shapes
                for sh in slide.Shapes:
                    if sh.HasTable:
                        t = sh.Table
                        for c in range(1, t.Columns.Count + 1):
                            cell = t.Cell(1, c)
                            cell.Shape.Fill.Solid()
                            cell.Shape.Fill.ForeColor.RGB = RED
                            if cell.Shape.HasTextFrame:
                                set_runs_color(cell.Shape.TextFrame.TextRange, WHITE)
                        # Compact all cells
                        for row in range(1, t.Rows.Count + 1):
                            for col in range(1, t.Columns.Count + 1):
                                cell = t.Cell(row, col)
                                if cell.Shape.HasTextFrame:
                                    cell.Shape.TextFrame.MarginLeft = 3
                                    cell.Shape.TextFrame.MarginRight = 3
                                    cell.Shape.TextFrame.MarginTop = 2
                                    cell.Shape.TextFrame.MarginBottom = 2
                                    cap_runs_size(cell.Shape.TextFrame.TextRange, 13)

                    elif sh.HasTextFrame and sh.TextFrame.HasText:
                        if title_shape and sh.Id == title_shape.Id:
                            continue
                        # Scale down big stat numbers, cap body text
                        try:
                            for r in sh.TextFrame.TextRange.Runs():
                                sz = r.Font.Size
                                if sz >= 60:
                                    r.Font.Size = 36  # 66->36
                                elif sz >= 40:
                                    r.Font.Size = 24  # 42/40.5->24
                                elif sz >= 30:
                                    r.Font.Size = 22  # 33/30/34.5->22
                                elif sz >= 20:
                                    r.Font.Size = 16  # 19.5->16
                                elif sz > 16:
                                    r.Font.Size = 14  # 17.25/18->14
                                # Leave ≤16 as-is
                        except:
                            pass

            log.write(
                f"Slide {i} -> sec={sec} chap_div={is_chap_div} prefix={prefix}\n"
            )

    # --- Pass 4: delete outer markers (back to front) ----
    for i in reversed(to_delete):
        pres.Slides(i).Delete()

    pres.SaveAs(dst)
    pres.Close()
    ppt.Quit()
    log.write("DONE\n")
    log.close()
    print("Done!")


if __name__ == "__main__":
    main()
