"""V29 骨架复制: 从 V13 原文件复制幻灯片结构, 产出 V29-temp.pptx
24 条详表 / 分页: 已上市8条=2页(第4页仅3行HEPLISAV-B + 第5页5行), 在研16条=4页
=> 共 6 页详表页; 概览复制 1 页; 总计 10 页
"""

import math
import os

import win32com.client


def prepare_v29_presentation():
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.DisplayAlerts = False

    base = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial"
    abs_path = os.path.abspath(
        os.path.join(base, r"review_materials\CpG_Vaccine_Safety_Summary-V13-20260820-原文件.pptx")
    )
    out_path = os.path.abspath(
        os.path.join(base, r"review_materials\CpG_Vaccine_Safety_Summary-V29-20260827-temp.pptx")
    )

    if os.path.exists(out_path):
        try:
            os.remove(out_path)
        except OSError:
            pass  # 沙箱下由 SaveAs 覆盖

    prs = ppt.Presentations.Open(abs_path, WithWindow=False)

    # 1. Duplicate TOC for Pipeline (Slide 3)
    prs.Slides(2).Duplicate()

    s2 = prs.Slides(2)
    tbl2 = s2.Shapes(2).Duplicate()

    # 2. Number of details slides (分板块切页: 已上市8条=2页[3+5], 在研16条=4页, 共6页)
    from update_data_final import marketed_data as _md, pipeline_data as _pd

    num_slides_needed = math.ceil(len(_md) / 4.0) + math.ceil(len(_pd) / 4.0)

    # We already have 1 Details slide (Slide 4). Duplicate it (num_slides_needed - 1) times.
    for _ in range(num_slides_needed - 1):
        prs.Slides(4).Duplicate()

    # Old Det2, Det3, Det4 now sit at (4 + n) .. (6 + n); delete in reverse order.
    old_det4 = 4 + num_slides_needed + 2
    old_det3 = 4 + num_slides_needed + 1
    old_det2 = 4 + num_slides_needed

    prs.Slides(old_det4).Delete()
    prs.Slides(old_det3).Delete()
    prs.Slides(old_det2).Delete()

    prs.SaveAs(out_path)
    prs.Close()
    ppt.Quit()
    print(f"Saved: {out_path} ({1 + 1 + 1 + num_slides_needed + 1} slides expected)")


if __name__ == "__main__":
    prepare_v29_presentation()
