"""统计 review_materials 目录（含子文件夹）内所有 Word 文件的总页数（用于打印预估）。
使用 Word COM 自动化，按 Word 实际分页计算页数（最接近打印页数）。
"""

import os

import pythoncom
import win32com.client

ROOT = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials"

WD_STATISTIC_PAGES = 2


def collect_files(root):
    exts = (".docx", ".doc")
    files = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if fn.lower().endswith(exts) and not fn.startswith("~$"):
                files.append(os.path.join(dirpath, fn))
    return files


def main():
    files = collect_files(ROOT)
    print(f"共找到 {len(files)} 个 Word 文件\n")

    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0  # wdAlertsNone

    total = 0
    results = []
    try:
        for i, path in enumerate(files, 1):
            try:
                doc = word.Documents.Open(
                    path, ReadOnly=True, AddToRecentFiles=False, Visible=False
                )
                try:
                    # 强制重分页，避免工具生成的 docx 无分页缓存导致统计返回 1 页
                    doc.Repaginate()
                    pages = doc.ComputeStatistics(WD_STATISTIC_PAGES)
                    pages = int(pages)
                finally:
                    doc.Close(SaveChanges=False)
                rel = os.path.relpath(path, ROOT)
                total += pages
                results.append((rel, pages))
                print(f"[{i:02d}/{len(files)}] {pages:4d} 页  {rel}")
            except Exception as e:
                rel = os.path.relpath(path, ROOT)
                print(f"[{i:02d}/{len(files)}] 错误   {rel}  -> {e}")
    finally:
        word.Quit()
        pythoncom.CoUninitialize()

    print("\n" + "=" * 60)
    print(f"文件数: {len(files)}")
    print(f"总页数: {total}")
    print("=" * 60)

    # 写入结果文件
    out = os.path.join(ROOT, "_page_count_summary.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"文件数: {len(files)}\n总页数: {total}\n\n")
        for rel, pages in results:
            f.write(f"{pages}\t{rel}\n")
    print(f"\n结果已写入: {out}")


if __name__ == "__main__":
    main()
