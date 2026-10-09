#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""非劣效分析交付稿自检器。

交付前必跑。检查项：
  1. sheet 数与命名合法（≤31 字符，无 / \\ * ? : [ ]）
  2. 说明页八节齐全、无占位符
  3. 判定逻辑：判定结果必须等于「95%CI 下限 > 界值」（防止写反）
  4. 表内自洽：率 = n/N、GMC 比值 = GMC1/GMC2、CI 下限 < 点估计 < CI 上限
  5. 汇总页与比较页数值一致（同population同分析集同指标的估计量必须相等）
  6. 若 spec.verification.official 提供了官方值，逐项三方对账

退出码：0 = 全通过；1 = 有失败项。

CLI:
  python selfcheck_output.py --spec spec.json --xlsx report.xlsx
"""

from __future__ import annotations

import argparse
import json
import re
import sys

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    print("ERROR: 需要 openpyxl（pip install openpyxl）", file=sys.stderr)
    raise

ILLEGAL = re.compile(r"[\/\*\?\[\]:\\]")
PLACEHOLDERS = ("TODO", "XXX", "待填", "placeholder", "<placeholder>")
EXPECTED_SECTIONS = ("【核心结论速览】", "【一、分析目的】", "【二、数据来源】",
                     "【三、人群与组别】", "【四、时点口径】",
                     "【五、统计方法与非劣效判定】", "【六、与官方发表值的校准】",
                     "【七、最终结论与依据】", "【八、局限性说明】")

PASSES: list[str] = []
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    (PASSES if cond else FAILS).append(name)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    return cond


def nearly(a, b, tol):
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="非劣效分析交付稿自检")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--xlsx", required=True)
    args = ap.parse_args(argv)

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    wb = load_workbook(args.xlsx, data_only=True)

    print("=" * 78)
    print(f"交付稿自检：{args.xlsx}")
    print("=" * 78)

    # ---- 1. sheet 命名 ----
    for name in wb.sheetnames:
        check(f"sheet 名合法：{name}", len(name) <= 31 and not ILLEGAL.search(name))
    check("sheet 至少含 00_说明 / 01_汇总 / 1 个比较页", len(wb.sheetnames) >= 3,
          str(wb.sheetnames))

    # ---- 2. 说明页 ----
    notes = wb["00_说明"]
    joined = "\n".join(str(c.value) for c in notes["A"] if c.value)
    for sec in EXPECTED_SECTIONS:
        check(f"说明页含 {sec}", sec in joined)
    for ph in PLACEHOLDERS:
        check(f"说明页无占位符 {ph}", ph not in joined)

    # ---- 3~4. 汇总页 ----
    ws = wb["01_汇总"]
    summary = []
    for r in range(3, ws.max_row + 1):
        pop = ws.cell(row=r, column=1).value
        if not pop:
            continue
        metric = ws.cell(row=r, column=2).value
        a_set = ws.cell(row=r, column=3).value
        est = ws.cell(row=r, column=6).value
        lo = ws.cell(row=r, column=7).value
        hi = ws.cell(row=r, column=8).value
        verdict = ws.cell(row=r, column=10).value
        summary.append(dict(pop=pop, metric=metric, a_set=a_set,
                            est=est, lo=lo, hi=hi, p=ws.cell(row=r, column=9).value,
                            verdict=verdict))

        is_rate = metric in {p["rate_metric"]["name"] for p in spec["populations"]}
        margin = float(spec["margins"]["rate_diff" if is_rate else "gmc_ratio"])
        check(f"汇总 判定逻辑 {pop}/{metric}/{a_set}",
              verdict == ("成立" if lo > margin else "不成立"),
              f"下限={lo} 界值={margin} 判定={verdict}")
        check(f"汇总 CI 自洽 {pop}/{metric}/{a_set}", lo < est < hi, f"{lo} < {est} < {hi}")

    expected_rows = len(spec["populations"]) * len(spec["analysis_sets"]) * 2
    check(f"汇总页 {expected_rows} 行结果", len(summary) == expected_rows,
          f"实际 {len(summary)}")

    # ---- 5. 汇总页 vs 比较页一致 ----
    for sheet in wb.sheetnames:
        if not sheet.startswith("比较"):
            continue
        sh = wb[sheet]
        for r in range(9, sh.max_row + 1):
            a_set = sh.cell(row=r, column=1).value
            if a_set not in spec["analysis_sets"]:
                continue
            est_cell = sh.cell(row=r, column=10).value
            if est_cell is None:
                continue
            lo = sh.cell(row=r, column=11).value
            hi = sh.cell(row=r, column=12).value
            verdict = sh.cell(row=r, column=13).value

            is_rate = sh.cell(row=8, column=3).value == "率(%)"
            margin = float(spec["margins"]["rate_diff" if is_rate else "gmc_ratio"])
            check(f"{sheet}/{a_set} 判定",
                  verdict == ("成立" if lo > margin else "不成立"),
                  f"下限={lo} 判定={verdict}")
            check(f"{sheet}/{a_set} CI 自洽", lo < est_cell < hi,
                  f"{lo} < {est_cell} < {hi}")

            if is_rate:
                x1, n1 = _frac(sh.cell(row=r, column=2).value)
                check(f"{sheet}/{a_set} 率=n/N",
                      nearly(sh.cell(row=r, column=3).value, 100.0 * x1 / n1, 0.005),
                      f"{sh.cell(row=r, column=3).value} vs {100.0 * x1 / n1:.2f}")
            else:
                g1 = sh.cell(row=r, column=3).value
                g2 = sh.cell(row=r, column=7).value
                check(f"{sheet}/{a_set} 比值=GMC1/GMC2",
                      nearly(sh.cell(row=r, column=10).value, g1 / g2, 0.002),
                      f"{sh.cell(row=r, column=10).value} vs {g1 / g2:.4f}")

            match = [s for s in summary if s["a_set"] == a_set
                     and nearly(s["est"], est_cell, 0.005)]
            check(f"{sheet}/{a_set} 与汇总页一致", bool(match),
                  f"比较页={est_cell}")

    # ---- 6. 官方值三方对账 ----
    # 每项 official 需显式指定 sheet（比较页名）、analysis_set、arm；
    # kind=rate/gmc 读比较页对应的 4 列，kind=gmc_p 读汇总页 P 值列。
    official = spec.get("verification", {}).get("official", [])
    if official:
        print(f"\n--- 官方值三方对账（{len(official)} 项）---")
    for item in official:
        label = "/".join(str(item.get(k, ""))
                         for k in ("kind", "population", "analysis_set", "arm"))
        kind = item.get("kind")
        if kind == "gmc_p":
            want_pop = item.get("population")
            hit = [s for s in summary
                   if s["a_set"] == item["analysis_set"]
                   and s["metric"] == item.get("metric_label")
                   and (not want_pop or s["pop"] == want_pop)]
            if not hit:
                check(f"官方对账 {label}", False, "汇总页未找到对应行")
                continue
            check(f"官方对账 {label}",
                  nearly(hit[0]["p"], item["p"], 0.0001),
                  f"表 P={hit[0]['p']} 官方 {item['p']}")
            continue

        sheet = item.get("sheet")
        if sheet not in wb.sheetnames:
            check(f"官方对账 {label}", False, f"找不到 sheet：{sheet}")
            continue
        sh = wb[sheet]
        target_row = None
        for r in range(9, sh.max_row + 1):
            if sh.cell(row=r, column=1).value == item["analysis_set"]:
                target_row = r
                break
        if target_row is None:
            check(f"官方对账 {label}", False, f"sheet 内无分析集 {item['analysis_set']}")
            continue
        col_base = 2 if arm_is_trial(item, spec["arms"]) else 6
        got = _read_arm_block(sh, target_row, kind, col_base)
        keys = ("x", "n", "pct", "gmc", "lo", "hi")
        ok = True
        detail = []
        for key in keys:
            if key in got and item.get(key) is not None:
                ok = ok and nearly(got[key], item[key], _tol(item[key]))
                detail.append(f"{key}={got[key]}(官{item[key]})")
        check(f"官方对账 {label}", ok, " ".join(detail))

    print("\n" + "=" * 78)
    print(f"自检完成：PASS {len(PASSES)} / FAIL {len(FAILS)}")
    for failure in FAILS:
        print("  - " + failure)
    print("=" * 78)
    return 1 if FAILS else 0


def _frac(text):
    head, tail = str(text).split("/")
    return int(head), int(tail)


def arm_is_trial(item, arms):
    arm = item.get("arm")
    if arm in ("试验组", "trial"):
        return True
    if arm in ("对照组", "control"):
        return False
    return arm == arms.get("trial")


def _read_arm_block(sh, row, kind, col_base):
    """按指标类型读取某一组的连续 4 列（n/N 或 N、点估计、CI 下限、CI 上限）。"""
    if kind == "rate":
        head, tail = str(sh.cell(row=row, column=col_base).value).split("/")
        return dict(x=int(head), n=int(tail),
                    pct=sh.cell(row=row, column=col_base + 1).value,
                    lo=sh.cell(row=row, column=col_base + 2).value,
                    hi=sh.cell(row=row, column=col_base + 3).value)
    return dict(n=sh.cell(row=row, column=col_base).value,
                gmc=sh.cell(row=row, column=col_base + 1).value,
                lo=sh.cell(row=row, column=col_base + 2).value,
                hi=sh.cell(row=row, column=col_base + 3).value)


def _tol(value):
    if value is None:
        return 0.0
    return max(0.005, abs(value) * 0.001)


if __name__ == "__main__":
    sys.exit(main())
