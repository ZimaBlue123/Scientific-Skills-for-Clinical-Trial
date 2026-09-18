#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
repair_mojibake_from_git.py

修复 "UTF-8 中文被按中文代码页(GBK/GB18030)解码后又存成 UTF-8" 造成的乱码文件。

背景
----
Windows 上 zh-CN 环境的默认 "ANSI" 代码页是 CP936(GBK)。某些工具读文件时不指定
编码，就会把 UTF-8 的中文按 GBK/GB18030 解码，再以 UTF-8 写回，产生乱码：

    正确文本  "中文"
    UTF-8 字节 E4 B8 AD E6 96 87
    按 GB18030 解码 → "涓\ue15f枃"   （\ue15f 落在 Unicode 私用区）
    再存成 UTF-8       → 乱码文件

私用区字符没有任何字体有字形，在 GitHub/浏览器里渲染成 "豆腐块"，
容易被误认为"字体问题"。

为什么不能程序化还原
--------------------
字符映射并非一一对应（同一个字符可能有多条字节路径，反之亦然），
且真实工具对非法字节的替换策略与 Python codec 不一致，
因此逆向还原会有不可恢复的字符丢失。**正确做法是从 Git 历史取回干净版本。**

本脚本做的事
------------
1. 从指定 Git 版本取回候选内容；
2. 用"往返判据"验证候选是否就是损坏前的原文：
       cand.encode('utf-8').decode(<中文代码页>) ≈ 当前乱码文件
   比较时把替换符/空白归一化，规避不同 decoder 的替换策略差异；
3. 相似度达标才输出，避免用错误的版本覆盖。

用法:
    python scripts/repair_mojibake_from_git.py <乱码文件> <Git版本> <输出文件>
    python scripts/repair_mojibake_from_git.py README.md 6c781b7 reports/README.restored.md
"""

from __future__ import annotations

import difflib
import subprocess
import sys

DEFAULT_CODECS = ("gb18030", "gbk", "cp936")

# 检判阈值：任一指标不达标即拒绝写出，避免用错误版本覆盖
MIN_FINGERPRINT = 0.95   # 私用区字符序列（损坏过程指纹），核心判据
MIN_CJK = 0.95           # 中文字符序列（内容一致性）
MIN_ASCII_LINES = 0.90   # 纯 ASCII 行（不受编码损坏影响；取回版本与损坏
                         # 版本之间可能有正常改动，故留出余量）


def git_show(rev: str, path: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip())
    return proc.stdout


def pua_seq(text: str) -> str:
    """私用区字符序列。这是损坏过程的指纹：真实 decoder 对 GBK 未定义字节位
    会映射到私用区，该序列几乎不可能被巧合复现。"""
    return "".join(c for c in text if 0xE000 <= ord(c) <= 0xF8FF)


def cjk_seq(text: str) -> str:
    """伪汉字（CJK 区）序列，用于比对中文内容是否一致。"""
    return "".join(c for c in text if 0x4E00 <= ord(c) <= 0x9FFF)


def ascii_lines(text: str) -> list[str]:
    """纯 ASCII 行。编码损坏不影响 ASCII，这部分应逐行完全一致。"""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip() and all(ord(c) < 128 for c in line):
            out.append(line.rstrip())
    return out


def roundtrip(text: str, codec: str) -> str:
    """把候选文本按 codec 解码一次，模拟损坏过程。"""
    return text.encode("utf-8").decode(codec, errors="replace")


def evaluate(candidate: str, corrupted: str, codec: str) -> dict:
    sim = roundtrip(candidate, codec)
    ratio = difflib.SequenceMatcher
    return {
        "codec": codec,
        "fingerprint": ratio(None, pua_seq(sim), pua_seq(corrupted)).ratio(),
        "cjk": ratio(None, cjk_seq(sim), cjk_seq(corrupted)).ratio(),
        "ascii": ratio(None, ascii_lines(sim), ascii_lines(corrupted)).ratio(),
    }


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    corrupted_path, rev, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        corrupted = open(corrupted_path, "rb").read().decode("utf-8")
    except OSError as exc:
        print(f"[失败] 无法读取 {corrupted_path}: {exc}")
        return 1
    except UnicodeDecodeError as exc:
        print(f"[失败] {corrupted_path} 不是合法 UTF-8，流程不适用: {exc}")
        return 1

    pua = sum(1 for c in corrupted if 0xE000 <= ord(c) <= 0xF8FF)
    print(f"损坏文件 {corrupted_path}: {len(corrupted)} 字符, 私用区 {pua} 个")
    if pua == 0:
        print("提示: 未发现私用区字符，可能不是本类乱码，仍将继续验证。")

    try:
        candidate = git_show(rev, corrupted_path).decode("utf-8")
    except (RuntimeError, UnicodeDecodeError) as exc:
        print(f"[失败] 无法从 {rev} 取回 {corrupted_path}: {exc}")
        return 1
    print(f"候选原文 {rev}:{corrupted_path}: {len(candidate)} 字符")

    best = None
    for codec in DEFAULT_CODECS:
        r = evaluate(candidate, corrupted, codec)
        print(f"  [{codec}] 指纹 {r['fingerprint']:.4f} | "
              f"中文 {r['cjk']:.4f} | ASCII行 {r['ascii']:.4f}")
        if best is None or r["fingerprint"] + r["cjk"] > (
            best["fingerprint"] + best["cjk"]
        ):
            best = r

    if best is None:  # 不依赖 assert：python -O 会剥离断言
        print("[中止] 无可用候选判定结果。")
        return 1

    ok = (
        best["fingerprint"] >= MIN_FINGERPRINT
        and best["cjk"] >= MIN_CJK
        and best["ascii"] >= MIN_ASCII_LINES
    )
    if not ok:
        print(f"\n[中止] {best['codec']} 未达阈值"
              f"（指纹>={MIN_FINGERPRINT}, 中文>={MIN_CJK}, ASCII行>={MIN_ASCII_LINES}）。"
              f"\n       该版本很可能不是损坏前的原文，未写出文件。")
        return 1

    print(f"\n[通过] {best['codec']} 三项指标全部达标，判定候选即损坏前的原文。")
    if best["ascii"] < 1.0:
        print(f"  注意: 纯 ASCII 行相似度 {best['ascii']:.4f} < 1.0，"
              f"说明取回版本与损坏版本之间另有正常改动（非乱码所致），"
              f"请人工确认这部分是否需要保留。")
    left = sum(1 for c in candidate if 0xE000 <= ord(c) <= 0xF8FF)
    print(f"  候选中的私用区字符: {left}（应为 0）")

    with open(out_path, "wb") as fh:
        fh.write(candidate.encode("utf-8"))
    print(f"已写出: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
