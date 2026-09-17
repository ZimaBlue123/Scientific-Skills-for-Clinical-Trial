"""对单个 Word 文件强制重分页后统计页数（解决部分工具生成的 docx 分页缓存为空、直接统计返回 1 页的问题）。"""

import contextlib
import os
import sys

import pythoncom
import win32com.client

WD_STATISTIC_PAGES = 2
WD_PRINT_VIEW = 3


def count(path):
    # Word COM 对含空格/正斜杠的路径解析不稳，统一归一化为反斜杠绝对路径
    path = os.path.abspath(path).replace("/", "\\")
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(path, ReadOnly=True, AddToRecentFiles=False, Visible=False)
        try:
            # 强制切换到页面视图并重分页，确保页码统计准确
            with contextlib.suppress(Exception):
                word.ActiveWindow.View.Type = WD_PRINT_VIEW
            doc.Repaginate()
            pages = int(doc.ComputeStatistics(WD_STATISTIC_PAGES))
        finally:
            doc.Close(SaveChanges=False)
        return pages
    finally:
        word.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    p = sys.argv[1]
    n = count(p)
    print(n)
