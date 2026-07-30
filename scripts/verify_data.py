#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify arithmetic self-consistency of the MMR (Medical Monitoring Report).

The script re-implements the counts the report claims and compares them
against the values it actually prints. Differences are flagged.

It writes a UTF-8 result file (``verify_data_result.txt`` by default) so
that downstream reviewers can spot-check without re-running the script.

Usage
-----
    py -3 verify_data.py [-o OUTPUT]

Exit codes
----------
    0  every assertion passed
    1  one or more mismatches detected
    2  I/O or runtime error
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logger = logging.getLogger("verify_data")

DEFAULT_OUTPUT = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\verify_data_result.txt"
)

OK = "[OK]"
NO = "[!!]"


@dataclass(frozen=True)
class Check:
    """A single arithmetic self-consistency check."""

    title: str
    computed: int
    expected: int

    @property
    def passed(self) -> bool:
        return self.computed == self.expected

    def render(self) -> str:
        flag = OK if self.passed else f"{NO} 期望 {self.expected}"
        return f"  {self.title}: 计算={self.computed}  {flag}"


@dataclass(frozen=True)
class SAECheck:
    subject: str
    vacc_date: date
    reported_interval: int
    sae_date: date

    @property
    def actual(self) -> int:
        return (self.sae_date - self.vacc_date).days

    @property
    def passed(self) -> bool:
        return self.actual == self.reported_interval

    def render(self) -> str:
        flag = OK if self.passed else f"{NO} (实差{self.actual}天, 偏差 {self.actual - self.reported_interval} 天)"
        return (
            f"  {self.subject}: 接种 {self.vacc_date.isoformat()} + "
            f"报告{self.reported_interval}天 vs 实际{self.actual}天  {flag}"
        )


def _build_sae_checks() -> list[SAECheck]:
    return [
        SAECheck("0020 左肺肺炎",        date(2025, 3, 6),  254, date(2025, 11, 15)),
        SAECheck("0039 桡骨茎突骨折",     date(2025, 3, 24), 245, date(2025, 11, 24)),
        SAECheck("1034 颅内占位",         date(2025, 3, 29), 301, date(2026, 1, 24)),
        SAECheck("1028 前列腺癌",         date(2025, 3, 29), 50,  date(2025, 5, 18)),
        SAECheck("1033 右上叶肺炎",       date(2025, 1, 22), 20,  date(2025, 2, 11)),
        SAECheck("1033 支气管哮喘",       date(2025, 1, 22), 20,  date(2025, 2, 11)),
    ]


def _group(label: str, lines: list[str]) -> list[str]:
    """Compose a titled, blank-line-bracketed block for the output report."""
    return [f"=== {label} ===", *lines, ""]


def verify() -> tuple[list[str], bool]:
    """Run all checks and return ``(lines, all_passed)``."""
    out: list[str] = []
    failed = False

    def add(line: str) -> None:
        out.append(line)

    def add_check(c: Check | SAECheck) -> None:
        nonlocal failed
        if not c.passed:
            failed = True
        add(c.render())

    # --- SAE 日期算术 ---
    add("=== SAE 日期算术 ===")
    for sae in _build_sae_checks():
        add_check(sae)
    add("")

    # --- 计数类校验 ---
    scalar_checks: list[Check] = [
        Check("合并用药 144+13+3",       144 + 13 + 3,    160),
        Check("AE 严重程度 159+98+11",   159 + 98 + 11,   268),
        Check("征集性 1+2+3 级 131+73+5", 131 + 73 + 5,   209),
        Check("非征集性 1+2+3 级 28+25+6", 28 + 25 + 6,    59),
        Check("表4 剂次例次合计",         (118 + 91) + (45 + 14), 268),
        Check("表6 部位例次合计",         (30 + 21 + 16 + 6 + 3) + (48 + 29 + 24 + 15 + 13 + 2 + 1), 208),
        Check("全部 AE 相关性 30+173+34+30+1", 30 + 173 + 34 + 30 + 1, 268),
        Check("征集性相关性 30+172+6",     30 + 172 + 6,    208),
        Check("实验室/ECG 例次",          5 + 6 + 7 + 1 + 4, 23),
        Check("合并非药物治疗",           1 + 6,            7),
        Check("筛败 115+34",              115 + 34,         149),
        Check("SAE 性质 可能无关5+无关1", 5 + 1,             6),
        Check("SAE 转归 痊愈4+好转1+未好转1", 4 + 1 + 1,     6),
    ]
    add("=== 计数与合计 ===")
    for c in scalar_checks:
        add_check(c)
    add("")

    # --- 主要矛盾: 非征集性 AE 维度混淆 ---
    add("=== 非征集性 AE (严重数据矛盾) ===")
    add("  报告原文(第 116 行): 39例 / 有关 21例29例次 / 无关 21例30例次")
    add("  -> 例数 21 + 21 = 42 ≠ 39, 维度不一致")
    add("  -> 推论: '无关' 一栏 '21 例' 应为 '18 例' (118 行: 18+3=21=有关)")
    add("")

    # --- 剂次叙述与去重分母 ---
    add("=== 剂次叙述 vs 去重分母 ===")
    add("  第 85 行: 第1剂 66例 + 第2剂 45例 = 111例 (跨剂次累计)")
    add("  全报告 AE 去重分母 72 例 → 维度差, 需表注说明")
    add("")

    # --- 表 6 受试者数 vs 例次 ---
    add("=== 表 6 受试者数 vs 例次错配 ===")
    add("  接种部位 例数 62 / 例次 76")
    add("  非接种部位 例数 103 / 例次 132")
    add("  总例数 165 > N=100, 需表注 (同一受试者可多部位)")
    add("")

    return out, not failed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify MMR numeric self-consistency."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output text file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format=LOG_FORMAT,
    )

    lines, all_passed = verify()

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        logger.error("failed to write %s: %s", args.output, exc)
        return 2

    logger.info(
        "wrote %d lines to %s (all_passed=%s)",
        len(lines),
        args.output,
        all_passed,
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
