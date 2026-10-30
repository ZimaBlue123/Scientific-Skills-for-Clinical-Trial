#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sync CTR registry records (transcribed from Word) into a clinical Excel database.

The pair of scripts in this skill implement the whole pipeline:
    extract_ctr_doc_text.py        .doc -> text/tables (Word COM)
    sync_ctr_registry_to_excel.py  records.json -> Excel (this file)

Usage
-----
  # 1) sync records into a copy of the database
  python sync_ctr_registry_to_excel.py --xlsx IN.xlsx --records rec.json \
         --out OUT.xlsx --diff diff.md

  # 2) dump existing rows as a records.json skeleton (bootstrap / regression base)
  python sync_ctr_registry_to_excel.py --xlsx IN.xlsx --dump CTR20263963,CTR20263799 \
         --dump-out base.json

Rules implemented
-----------------
1. Match by the key column (default 登记号):
     found   -> fill blanks, overwrite mismatches with the record value,
                leave already-correct cells untouched
     missing -> append a new row styled like the template row
2. A record value of null means "Word says 登记人暂未填写" -> the cell is
   cleared, even if it currently holds a (wrong) value.
3. De-duplicate by the KEY column, never by row number.
4. Sheet-wide wording/format unification (meaning-preserving only).
5. Re-sort the whole sheet by the key column, descending.
6. Emit a per-cell markdown diff marked 新增/补全/修正/格式统一/未动.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
import re
import sys

import openpyxl

DATE_FMT = r"yyyy\-mm\-dd"
PLACEHOLDERS = {"未登记", "暂未填写", "暂无", "—", "-", "N/A", "NA"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --------------------------------------------------------------------------
# value helpers
# --------------------------------------------------------------------------
def to_cell(v):
    """JSON value -> Excel value (ISO date strings become datetimes)."""
    if isinstance(v, str) and ISO.match(v.strip()):
        return dt.datetime.strptime(v.strip(), "%Y-%m-%d")
    return v


def from_cell(v):
    """Excel value -> JSON value."""
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, dt.date):
        return v.strftime("%Y-%m-%d")
    return v


def norm(v):
    """Comparable form of a cell value."""
    if v is None:
        return None
    if isinstance(v, (dt.datetime, dt.date)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, str):
        return v.strip()
    return v


def looks_like_date_col(name: str) -> bool:
    return any(k in name for k in ("日期", "公示", "入组", "完成", "启动"))


def normalize_cell(name, v):
    """Sheet-wide wording / format unification (semantics-preserving only)."""
    if not isinstance(v, str):
        return v, False
    s = v
    if looks_like_date_col(name):
        if s.strip() in PLACEHOLDERS:
            return None, True
    elif "申请人" in name or "申办" in name:
        s = re.sub(r"\s*/\s*", "/", s)
    elif "名称" in name or "制品" in name or "药物" in name:
        if "(" in s or ")" in s:
            s = s.replace("(", "（").replace(")", "）")
        s = re.sub(r"CHO\s*细胞", "CHO细胞", s)
    elif "分期" in name:
        for a, b in (("Ⅰ", "I"), ("Ⅱ", "II"), ("Ⅲ", "III"), ("Ⅳ", "IV")):
            s = s.replace(a, b)
    elif "设计" in name:
        s = re.sub(r"^随机、", "随机化、", s)
        s = re.sub(r"^非随机、", "非随机化、", s)
    s = re.sub(r"CHO\s+细胞", "CHO细胞", s)     # catch-all cleanup
    return s, s != v


# --------------------------------------------------------------------------
# sheet I/O
# --------------------------------------------------------------------------
def read_sheet(ws, header_row):
    headers = [ws.cell(header_row, c).value for c in range(1, ws.max_column + 1)]
    headers = [h for h in headers if h]
    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
        styles = [copy.copy(ws.cell(r, c)._style) for c in range(1, len(headers) + 1)]
        if all(v is None for v in vals):
            continue                                    # skip fully empty rows
        rows.append({"src": r, "vals": vals, "styles": styles,
                     "h": ws.row_dimensions[r].height})
    return headers, rows


def write_sheet(ws, header_row, headers, rows):
    for i, row in enumerate(rows):
        tr = header_row + 1 + i
        for c in range(1, len(headers) + 1):
            cell = ws.cell(tr, c)
            cell.value = row["vals"][c - 1]
            cell._style = row["styles"][c - 1]
            if isinstance(cell.value, dt.datetime):
                # a date filled into a previously blank cell inherits "General"
                cell.number_format = DATE_FMT
        ws.row_dimensions[tr].height = row["h"]
    last = header_row + len(rows)
    ws.auto_filter.ref = "A%d:%s%d" % (
        header_row, openpyxl.utils.get_column_letter(len(headers)), last)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def dump_records(ws, header_row, headers, rows, key, regs):
    ki = headers.index(key)
    out = {}
    for r in rows:
        reg = r["vals"][ki]
        if regs and reg not in regs:
            continue
        out[reg] = {h: from_cell(r["vals"][i])
                    for i, h in enumerate(headers) if h != key}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", required=True, help="input Excel database")
    ap.add_argument("--sheet", default=None, help="sheet name (default: first)")
    ap.add_argument("--header-row", type=int, default=1)
    ap.add_argument("--key", default="登记号", help="primary key column name")
    ap.add_argument("--records", help="records.json to sync in")
    ap.add_argument("--out", help="output xlsx (default: overwrite input)")
    ap.add_argument("--diff", help="markdown diff output path")
    ap.add_argument("--dump", help="comma separated keys to dump as records.json")
    ap.add_argument("--dump-out", help="dump destination json")
    ap.add_argument("--no-normalize", action="store_true",
                    help="skip sheet-wide format unification")
    ap.add_argument("--no-sort", action="store_true", help="keep original order")
    ap.add_argument("--template-row", type=int, default=2,
                    help="row whose cell style is copied for new rows")
    a = ap.parse_args()

    wb = openpyxl.load_workbook(a.xlsx)
    ws = wb[a.sheet] if a.sheet else wb.worksheets[0]
    headers, rows = read_sheet(ws, a.header_row)
    if a.key not in headers:
        sys.exit("key column %r not in headers: %s" % (a.key, headers))
    ki = headers.index(a.key)

    # ---- dump mode -------------------------------------------------------
    if a.dump:
        regs = [x.strip() for x in a.dump.split(",") if x.strip()]
        data = dump_records(ws, a.header_row, headers, rows, a.key, regs)
        dest = a.dump_out or "records.json"
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        print("dumped %d record(s) -> %s" % (len(data), dest))
        return 0

    records = {}
    if a.records:
        with open(a.records, encoding="utf-8") as fh:
            records = json.load(fh)

    log = []
    unknown_cols = set()

    # ---- 1. de-duplicate by key (never by row number) --------------------
    seen, keep = set(), []
    for r in rows:
        k = r["vals"][ki]
        if k in seen:
            print("DROP duplicate %s=%s (原第 %s 行)" % (a.key, k, r["src"]))
            continue
        seen.add(k)
        keep.append(r)
    rows = keep

    # ---- 2. apply records ------------------------------------------------
    by_key = {r["vals"][ki]: r for r in rows}
    tpl = next((r for r in rows if r["src"] == a.template_row), rows[0])
    for reg, fields in records.items():
        row = by_key.get(reg)
        if row is None:
            row = {"src": None, "vals": [None] * len(headers),
                   "styles": [copy.copy(s) for s in tpl["styles"]], "h": None}
            row["vals"][ki] = reg
            rows.append(row)
            print("新增 %s" % reg)
        else:
            print("更新 %s" % reg)
        for c, name in enumerate(headers):
            if name == a.key or name not in fields:
                continue
            new = to_cell(fields[name])
            old = row["vals"][c]
            o, n = norm(old), norm(new)
            if o == n:
                log.append({"登记号": reg, "列": name, "状态": "未动",
                            "原值": old, "新值": old})
                continue
            if o is None:
                state = "补全"
            elif n is None:
                state = "修正（清空，源文档标注暂未填写）"
            else:
                state = "修正"
            log.append({"登记号": reg, "列": name, "状态": state,
                        "原值": old, "新值": new})
            row["vals"][c] = new
            row["h"] = None         # content grew -> let Excel auto-fit
        unknown_cols.update(set(fields) - set(headers))

    if unknown_cols:
        print("WARN record keys not in sheet header (ignored): %s"
              % sorted(unknown_cols))

    # ---- 3. sheet-wide format unification --------------------------------
    flog = []
    if not a.no_normalize:
        for row in rows:
            for c, name in enumerate(headers):
                old = row["vals"][c]
                new, changed = normalize_cell(name, old)
                if changed:
                    flog.append({"登记号": row["vals"][ki], "列": name,
                                 "状态": "格式统一", "原值": old, "新值": new})
                    row["vals"][c] = new
        print("格式统一：%d 处" % len(flog))

    # ---- 4. sort by key descending ---------------------------------------
    if not a.no_sort:
        blank = [r for r in rows if not r["vals"][ki]]
        if blank:
            sys.exit("REFUSING TO SORT: blank %s in %d row(s)" % (a.key, len(blank)))
        rows.sort(key=lambda r: str(r["vals"][ki]), reverse=True)

    # ---- 5. write back ---------------------------------------------------
    write_sheet(ws, a.header_row, headers, rows)
    out = a.out or a.xlsx
    wb.save(out)
    print("saved -> %s   rows=%d" % (out, len(rows)))

    # ---- 6. diff markdown ------------------------------------------------
    def cell(v, n=60):
        s = "" if v is None else str(v)
        if isinstance(v, (dt.datetime, dt.date)):
            s = v.strftime("%Y-%m-%d")
        s = s.replace("\n", " ⏎ ")
        return (s[:n] + "…") if len(s) > n else s

    if a.diff:
        md = ["| %s | 列 | 状态 | 原值 | 新值 |" % a.key, "|---|---|---|---|---|"]
        for e in log + flog:
            md.append("| %s | %s | **%s** | %s | %s |" %
                      (e["登记号"], e["列"], e["状态"],
                       cell(e["原值"]), cell(e["新值"])))
        os.makedirs(os.path.dirname(os.path.abspath(a.diff)), exist_ok=True)
        with open(a.diff, "w", encoding="utf-8") as fh:
            fh.write("\n".join(md) + "\n")
        print("diff ->", a.diff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
