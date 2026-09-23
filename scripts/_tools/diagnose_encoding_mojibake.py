#!/usr/bin/env python
"""
diagnose_encoding_mojibake.py

扫描仓库内的文本文件，识别 "UTF-8 中文被误按 GB18030/GBK 解码后再存成 UTF-8"
造成的乱码（mojibake）。

判定依据（三条任一命中即标记）：
  1) 出现 Unicode 私用区字符 U+E000-U+F8FF（GB18030 未定义双字节位的映射结果），
     这类字符没有任何字体有字形，渲染为 "豆腐块"。
  2) 出现典型 GBK 误码高频字：涓 锛 鈥 鏂 瀹 绾 鍜 鐨 缁 璁 鍑 铏 鍏 鍜 璺 绛
  3) 有效 UTF-8 但中文占比异常 + 上述特征字密度超阈值

用法:
    python scripts/diagnose_encoding_mojibake.py [根目录]
"""

from __future__ import annotations

import warnings

warnings.warn(
    "This module is deprecated as of Phase 4 Pipeline refactoring. Please use the new `scripts.pipeline` package instead.",
    DeprecationWarning,
    stacklevel=2
)


import os
import sys
from collections import Counter

# 典型 GBK 误码高频字。
# 选取原则：这些字在正常简体中文文本中几乎不会出现。
# 已剔除在合法语境下常见的汉字：缓(缓解)、互(交互)、板(模板)、
# 煎(煎熬)、娇(娇嫩) 等 —— 保留它们会造成大量误报。
MOJIBAKE_MARKERS = set(
    "涓锛鈥鏂瀹绾鍜鐨缁璁鍑铏鍏璺绛鎴鍦ㄩ噸"
    "椤圭洰氫綅闅愮搴擄紙寮虹儓鏈熷熀叏鍗曟枃"
    "鎵弿鍒犻櫎浜ゆ槗嶅悓姝ュ垪鏍纺鐢ヨ旈熶"
    "鐩爜铻嶈繍缂撴潯鑺傛暟鎹璁扮"
)

TEXT_EXT = {
    ".md",
    ".txt",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".svg",
    ".xml",
    ".drawio",
    ".ps1",
    ".cmd",
    ".bat",
    ".sh",
    ".rst",
    ".csv",
}

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".workbuddy"}


def is_pua(ch: str) -> bool:
    return 0xE000 <= ord(ch) <= 0xF8FF


def scan_file(path: str) -> dict | None:
    try:
        raw = open(path, "rb").read()
    except OSError:
        return None
    if b"\x00" in raw[:4096]:  # 二进制
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        # 非 UTF-8（可能是 GBK 本地文件），单独记录
        return {"kind": "not-utf8", "pua": 0, "markers": 0, "sample": ""}

    pua = sum(1 for c in text if is_pua(c))
    marker_counter = Counter(c for c in text if c in MOJIBAKE_MARKERS)
    markers = sum(marker_counter.values())
    if pua == 0 and markers < 5:
        return None

    sample = ""
    for line in text.splitlines():
        if any(is_pua(c) for c in line) or any(c in MOJIBAKE_MARKERS for c in line):
            sample = line.strip()[:100]
            break
    return {
        "kind": "mojibake",
        "pua": pua,
        "markers": markers,
        "top": [c for c, _ in marker_counter.most_common(6)],
        "sample": sample,
    }


def main() -> int:
    root = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    hits: list[tuple[str, dict]] = []
    scanned = 0
    self_path = os.path.abspath(__file__)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            full = os.path.join(dirpath, fn)
            # 本脚本自身含误码字表，必然自命中，跳过
            if os.path.abspath(full) == self_path:
                continue
            scanned += 1
            info = scan_file(full)
            if info:
                rel = os.path.relpath(full, root).replace("\\", "/")
                hits.append((rel, info))

    hits.sort(key=lambda kv: -(kv[1].get("pua", 0) + kv[1].get("markers", 0)))
    print(f"扫描文本文件: {scanned}    命中: {len(hits)}")
    print("-" * 78)
    for rel, info in hits:
        if info["kind"] == "not-utf8":
            print(f"[非UTF-8] {rel}   <-- 建议确认是否为本地 GBK 文件")
            continue
        print(
            f"[乱码] {rel}\n"
            f"        私用区字符={info['pua']}  误码高频字={info['markers']}  "
            f"样例={'/'.join(info['top'])}\n"
            f"        {info['sample']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
