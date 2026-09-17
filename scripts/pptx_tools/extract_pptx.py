#!/usr/bin/env python3
"""Extract text content from PPTX for review."""

from pptx import Presentation

src = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\TVAX-009 EOP2 面对面专家会议-20260910 GJ-LL.pptx"
prs = Presentation(src)

print(f"Total slides: {len(prs.slides)}\n")

for idx, slide in enumerate(prs.slides, 1):
    print(f"========= SLIDE {idx} =========")
    # Detect layout
    layout = slide.slide_layout.name
    print(f"[Layout: {layout}]")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                txt = "".join(run.text for run in para.runs)
                if txt.strip():
                    print(txt)
        elif shape.has_table:
            tbl = shape.table
            print("[TABLE]")
            for row in tbl.rows:
                cells = []
                for cell in row.cells:
                    cells.append(cell.text.replace("\n", " | "))
                print(" || ".join(cells))
        elif shape.shape_type == 13:  # picture
            print(f"[PICTURE: {shape.name}]")
        else:
            if shape.has_text_frame is False and hasattr(shape, "text") and shape.text:
                print(f"[SHAPE TEXT] {shape.text}")
    print()
