# -*- coding: utf-8 -*-
"""用 PowerPoint 打开并另存为，使其重写/规范化 XML 关系，修复弹窗问题。"""
import os, sys, time
import win32com.client as win32
from pathlib import Path

src = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\TVAX-009项目3期临床试验启动前沟通交流ppt-20260903（临床部分-新增糖尿病亚组）.pptx"
tmp = src + ".tmp"

if not os.path.exists(src):
    print("not found:", src); sys.exit(1)

# remove old tmp if exists
if os.path.exists(tmp):
    os.remove(tmp)

ppt = win32.DispatchEx("PowerPoint.Application")
ppt.Visible = True
try:
    # OpenAndRepair=True 让 PowerPoint 自动修复后打开（可能以只读打开）
    prs = ppt.Presentations.Open2007(src, ReadOnly=False, Untitled=False, WithWindow=True, OpenAndRepair=True)
    time.sleep(2)
    # 以其他名字保存，再替换原文件
    prs.SaveAs(tmp)
    print("saved tmp:", tmp)
finally:
    try:
        prs.Close()
    except Exception:
        pass
    ppt.Quit()

# replace original with repaired tmp
os.replace(tmp, src)
print("replaced:", src)
