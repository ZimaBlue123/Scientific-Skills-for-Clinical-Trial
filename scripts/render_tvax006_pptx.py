#!/usr/bin/env python3
"""Render the generated TVAX-006 PPTX to PNG images for visual verification."""
import os
import sys

PPTX = r"E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials/006 PPT/TVAX-006_Clinical_Development_Overview_20260831.pptx"
OUT_DIR = r"E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials/006 PPT/_extracted/render"

import pythoncom
import win32com.client
import shutil

os.makedirs(OUT_DIR, exist_ok=True)

# PowerPoint COM cannot open paths containing spaces reliably -> copy to temp first
TMP_PPTX = os.path.join(os.environ["TEMP"], "tvax006_render.pptx")
TMP_DIR = os.path.join(os.environ["TEMP"], "tvax006_render_out")
os.makedirs(TMP_DIR, exist_ok=True)
shutil.copyfile(PPTX, TMP_PPTX)

pythoncom.CoInitialize()
app = win32com.client.Dispatch("PowerPoint.Application")
try:
    pres = app.Presentations.Open(TMP_PPTX, ReadOnly=True, Untitled=False, WithWindow=False)
    for i, slide in enumerate(pres.Slides, start=1):
        out = os.path.join(OUT_DIR, f"slide_{i}.png")
        tmp_out = os.path.join(TMP_DIR, f"slide_{i}.png")
        slide.Export(tmp_out, "PNG", 1600, 900)
        shutil.copyfile(tmp_out, out)
        print("exported", out)
    pres.Close()
finally:
    app.Quit()
    pythoncom.CoUninitialize()
print("DONE")
