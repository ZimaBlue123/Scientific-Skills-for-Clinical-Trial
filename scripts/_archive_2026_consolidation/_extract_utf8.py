# -*- coding: utf-8 -*-
"""一次性脚本：读取 extract_docx_full 输出的 GBK 文件并转换为 UTF-8 BOM。"""
import sys
sys.path.insert(0, r"e:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts")
from extract_docx_full import extract_docx

src = r"e:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\远大重组带状疱疹疫苗_Ⅱ期_第三次医学监查报告 V0.1_20260722.docx"
text = extract_docx(src)
out = r"e:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\doc_utf8.txt"
with open(out, "wb") as f:
    f.write(b"\xef\xbb\xbf")
    f.write(text.encode("utf-8"))
sys.stderr.write("written %d chars\n" % len(text))
