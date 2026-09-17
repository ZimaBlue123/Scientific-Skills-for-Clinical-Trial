"""渲染指定 PPTX 的指定幻灯片为高分辨率 PNG（PowerPoint COM）。

用法: python render_slide_highres.py <pptx> <slide_index_1based> <out_png> [width] [height]
"""

import os
import shutil
import sys
import tempfile

import pythoncom
import win32com.client


def main():
    pptx = os.path.abspath(sys.argv[1])
    idx = int(sys.argv[2])
    out_png = os.path.abspath(sys.argv[3])
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 3200
    h = int(sys.argv[5]) if len(sys.argv) > 5 else 1800

    tmp_root = os.path.join(tempfile.gettempdir(), "pptx_render_one")
    os.makedirs(tmp_root, exist_ok=True)
    tmp_pptx = os.path.join(tmp_root, "input.pptx")
    shutil.copyfile(pptx, tmp_pptx)

    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = None
    try:
        pres = app.Presentations.Open(tmp_pptx, ReadOnly=True, Untitled=False, WithWindow=False)
        tmp_png = os.path.join(tmp_root, "out.png")
        pres.Slides(idx).Export(tmp_png, "PNG", w, h)
        os.makedirs(os.path.dirname(out_png), exist_ok=True)
        shutil.copyfile(tmp_png, out_png)
        print("saved", out_png, w, h)
    finally:
        try:
            if pres is not None:
                pres.Close()
        except Exception:
            pass
        app.Quit()
        pythoncom.CoUninitialize()
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
