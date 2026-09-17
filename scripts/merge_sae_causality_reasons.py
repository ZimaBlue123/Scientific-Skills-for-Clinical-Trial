#!/usr/bin/env python3
"""
merge_sae_causality_reasons.py

Fill the 相关性判定原因 column of SAE清单_Ⅰ期+Ⅱ期.xlsx with the investigator's
causality rationale taken verbatim from the scanned 肥城现场 SAE 总结报告 PDFs
(review_materials/统计/远大乙肝Ⅱ期-肥城现场-SAE总结报告汇总/).

The reports are scanned images, so they are OCR'd with RapidOCR (cache under
.workbuddy/sae_report_ocr/). Two reports (774 / 370) have their 相关性 paragraph
overlapped by a stamp at 200 dpi and are re-recognised at 400 dpi.

Matching: 受试者编号 (研究号 from the file name) + SAE name containment between
the report file name and the TFL row's SAE描述 / 首选术语. Rows without a
matching report keep an empty 相关性判定原因.

A new column 判定原因来源 records which report the text came from.

Usage:
    python scripts/merge_sae_causality_reasons.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz  # pymupdf
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "review_materials" / "统计" / "SAE清单_Ⅰ期+Ⅱ期.xlsx"
STAT_DIR = ROOT / "review_materials" / "统计"

# (pdf folder, ocr cache folder, label used in 判定原因来源, pdf glob)
REPORT_SOURCES = [
    (
        STAT_DIR / "远大乙肝Ⅱ期-肥城现场-SAE总结报告汇总",
        ROOT / ".workbuddy" / "sae_report_ocr",
        "肥城现场SAE总结报告",
        "*.pdf",
    ),
    (
        STAT_DIR / "远大赛微信乙肝Ⅱ期-SAE总结报告汇总-邹城",
        ROOT / ".workbuddy" / "sae_report_ocr_zoucheng",
        "邹城现场SAE总结报告",
        "*.pdf",
    ),
    (
        STAT_DIR / "Ⅰ期的SAE(1)",
        ROOT / ".workbuddy" / "sae_report_ocr_phase1",
        "Ⅰ期SAE总结报告（东阿）",
        "*总结报告*.pdf",
    ),
]
HIRES_DIR = ROOT / ".workbuddy" / "sae_report_ocr_hires"

# Reports whose 相关性 paragraph is lost at 200 dpi -> re-OCR these pages at 400 dpi.
HIRES_PAGES = {
    "19-肥城现场SAE-远大重组乙肝疫苗二期-研究号774-蛛网膜下出血(Hunt-Hess分级IV级)-总结报告-修订报告20251017.pdf": [
        4
    ],
    "22-肥城现场SAE-远大重组乙肝疫苗二期-研究号370-头盆不称-首次&总结报告-20260603.pdf": [4],
}

NOISE_LINE = re.compile(r"^(={3,}.*PAGE \d+.*={3,}|方案编号：.*|文件编号.*|第\d+页.*)$")
CONCLUSION = re.compile(
    r"(综合判定相关性为|综上判定相关性为|故判定相关性为|初步判定相关性为|判定其相关性为"
    r"|判定相关性为|相关性判定为|判定此SAE与研究疫苗|判定此SAE与试验用疫苗"
    r"|判定与研究疫苗无关|判定与试验用疫苗无关|判定为可能无关|判定为无关"
    r"|与接种疫苗肯定无关|与接种疫苗可能无关|与研究疫苗肯定无关|与研究疫苗可能无关)"
)
STOP_PREFIX = (
    "药物治疗",
    "非药物治疗",
    "治疗情况",
    "修订内容",
    "修订说明",
    "修订：",
    "修订:",
    "修订（",
    "修订(",
    "报告单位名称",
    "报告人职务",
    "报告人签名",
    "用药原因",
    "药物名称",
    "用药途径",
    "单次剂量",
    "给药频率",
    "起止时间",
    "是否持续",
    "长住院时间",
    "十、",
    "十一、",
    "十二、",
    "用药记录表",
    "用药记录",
    "用药清单",
    "附表",
    "药物治疗",
    "非药物治疗",
)

PUNCT = re.compile(r"[\s（）()【】\[\]“”\"'、，,；;：:。．\.·—\-_/\\]+")


def norm(text: str) -> str:
    return PUNCT.sub("", text or "")


def clean_pages(text: str) -> str:
    kept = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or NOISE_LINE.match(s):
            continue
        kept.append(s)
    return "\n".join(kept)


def _slice_end(body: str, start: int) -> int:
    cut = len(body)
    for token in STOP_PREFIX:
        pos = body.find(token, start)
        if pos != -1:
            cut = min(cut, pos)
    return cut


def choose_start(body: str) -> int | None:
    """Pick the 相关性 label that opens the real rationale.

    Some reports restate 相关性 in a later 修订说明 section; only the first
    candidate that actually contains a conclusion sentence is accepted.
    """
    cands = [m.end() for m in re.finditer(r"相关性[:：]", body)]
    if not cands:  # label lost in OCR -> fall back to the 严重程度 line
        sev = list(re.finditer(r"严重程度[:：]", body))
        return sev[-1].end() if sev else None
    for s in cands:
        seg = body[s : _slice_end(body, s)]
        if len(seg) >= 60 and CONCLUSION.search(seg):
            return s
    return cands[0]


def extract_reason(text: str) -> str | None:
    """Return the verbatim 相关性 rationale of one SAE summary report.

    The reports use slightly different section labels ("相关性：" / "九、相关性：")
    and the OCR occasionally splits the closing sentence, so the rationale is
    delimited structurally instead of by the conclusion wording:
        start = after the last 相关性 label (or the 严重程度 line)
        end   = the next form section (药物治疗 / 修订 / 报告单位 ...)
                then trimmed back to the last full stop.
    """
    # Chinese lines wrap arbitrarily in these reports, so join them back into a
    # continuous string before locating the rationale.
    body = "".join(clean_pages(text).split("\n"))

    start = choose_start(body)
    if start is None:
        return None

    cut = len(body)
    for token in STOP_PREFIX:
        pos = body.find(token, start)
        if pos != -1:
            cut = min(cut, pos)
    reason = body[start:cut]

    # prefer closing at the conclusion sentence; fall back to the last full stop
    m = CONCLUSION.search(reason)
    if m:
        end = reason.find("。", m.end() - 1)
        if end != -1:
            reason = reason[: end + 1]
    else:
        last_stop = reason.rfind("。")
        if last_stop != -1:
            reason = reason[: last_stop + 1]

    reason = re.sub(r"^[\s，。、”）)】\*·—\-]+", "", reason)
    reason = re.sub(r"^\d级", "", reason)  # leftover 严重程度 grade
    if "。" not in reason and len(reason) < 12:
        return None
    return re.sub(r"\s+", "", reason).strip() or None


REASON_START = re.compile(r"^(受试者|该受试者|患者|本次|（1|\(1|1[.、]|一、|从|接种|根据|九|十)")


def reason_is_complete(reason: str | None) -> bool:
    """Heuristic gate: a usable rationale mentions the vaccine and starts cleanly."""
    if not reason:
        return False
    if "疫苗" not in reason or len(reason) < 40:
        return False
    return bool(REASON_START.match(reason))


SUBJECT_DIR_RE = re.compile(r"^[A-Za-z]{1,2}\d{2,3}$")


def parse_meta(pdf: Path, pdf_dir: Path, text: str = "") -> tuple[str, str]:
    """Return (受试者编号, SAE名称) for one report.

    Subject id: the containing folder wins when it looks like a subject code
    (Ⅰ期 reports live in G33/ G05/ ... folders), otherwise 研究号 in the name.
    SAE name: prefer the SAE诊断 / SAE名称 line inside the report itself.
    """
    sid = ""
    if pdf.parent != pdf_dir and SUBJECT_DIR_RE.match(pdf.parent.name):
        sid = pdf.parent.name
    if not sid:
        m = re.search(r"研究号[-–—\s]*([A-Za-z]?\d{2,3})", pdf.name)
        sid = m.group(1) if m else ""
    if not sid:
        m = re.search(r"(?<![A-Za-z0-9])([A-Za-z]\d{2,3})(?![A-Za-z0-9])", pdf.name)
        sid = m.group(1) if m else ""

    sae = ""
    if text:
        # line-based: the OCR dumps the form field by field, one per line
        for ln in text.split("\n"):
            s = ln.strip()
            m = re.match(r"^SAE(?:诊断|名称)[：:]\s*(.+)$", s)
            if m:
                sae = re.split(r"[。，,；;]", m.group(1))[0].strip()
                break
    if sae and (
        len(sae) > 45 or any(k in sae for k in ("SAE开始时间", "严重程度", "修订", "AE开始时间"))
    ):
        sae = ""
    if not sae:
        m2 = re.search(r"研究号[-–—\s]*[A-Za-z]?\d{2,3}-(.+)$", pdf.name)
        if not m2:
            m2 = re.search(r"(?<![0-9])[A-Za-z]\d{2,3}-(.+)$", pdf.name)
        if m2:
            sae = re.split(r"-(?:总结|首次)", m2.group(1))[0]
    sae = re.sub(r"\(\d*\)$|\s*\d*$", "", sae).strip()
    return sid, sae


def cache_stem(pdf_dir: Path, pdf: Path) -> str:
    """Cache key matching ocr_sae_summary_reports.py (keeps subject sub-folder)."""
    rel = pdf.relative_to(pdf_dir)
    stem = str(rel)[: -len(pdf.suffix)].replace("\\", "__").replace("/", "__")
    return re.sub(r'[\\/:*?"<>|]+', "_", stem)


def ocr_pages(pdf: Path, pages: list[int], dpi: int, engine, cache: Path) -> str:
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / (pdf.stem + f"_p{'_'.join(map(str, pages))}_{dpi}.txt")
    if dest.exists() and dest.stat().st_size:
        return dest.read_text(encoding="utf-8")
    doc = fitz.open(str(pdf))
    chunks = []
    for pn in pages:
        pix = doc[pn - 1].get_pixmap(dpi=dpi)
        res, _ = engine(pix.tobytes("png"))
        chunks.append("\n".join(item[1] for item in (res or [])))
        print(f"    hi-res OCR {pdf.name[:30]} p{pn} @{dpi}dpi", file=sys.stderr)
    doc.close()
    text = "\n".join(chunks)
    dest.write_text(text, encoding="utf-8")
    return text


def collect_reasons(engine) -> tuple[list[dict], list[str]]:
    reasons: list[dict] = []
    notes: list[str] = []

    for pdf_dir, ocr_dir, label, pattern in REPORT_SOURCES:
        if not pdf_dir.exists():
            notes.append(f"缺少报告目录：{pdf_dir}")
            continue
        print(f"-- {label}", file=sys.stderr)
        for pdf in sorted(pdf_dir.rglob(pattern)):
            if pdf.name in HIRES_PAGES:
                text = ocr_pages(pdf, HIRES_PAGES[pdf.name], 400, engine, HIRES_DIR)
            else:
                cached = ocr_dir / (cache_stem(pdf_dir, pdf) + ".txt")
                if not cached.exists():
                    notes.append(f"缺少 OCR 缓存：{pdf.name}")
                    continue
                text = cached.read_text(encoding="utf-8")

            sid, sae = parse_meta(pdf, pdf_dir, text)
            if not sid:
                notes.append(f"无法解析受试者编号：{pdf.name}")
                continue

            reason = extract_reason(text)
            # quality gate: a real rationale mentions the vaccine and starts cleanly
            if not reason_is_complete(reason) and pdf.name not in HIRES_PAGES:
                print(f"    low-quality OCR, retry at 400 dpi: {pdf.name[:40]}", file=sys.stderr)
                pages = list(range(1, fitz.open(str(pdf)).page_count + 1))
                text = ocr_pages(pdf, pages, 400, engine, HIRES_DIR)
                reason = extract_reason(text)
            if not reason:
                notes.append(f"未识别到相关性判定段落：{pdf.name}")
                continue
            reasons.append(
                {
                    "sid": sid,
                    "sae": sae,
                    "reason": reason,
                    "src": pdf.name,
                    "label": label,
                    "clean": bool(REASON_START.match(reason)),
                }
            )
            flag = "" if REASON_START.match(reason) else "  [OCR 不完整]"
            print(f"  [{sid}] {sae[:26]} -> {len(reason)} chars{flag}", file=sys.stderr)

    return reasons, notes


def main() -> int:
    engine = RapidOCR()
    print("extracting causality rationales ...", file=sys.stderr)
    reasons, notes = collect_reasons(engine)
    if not reasons:
        print("no rationales extracted", file=sys.stderr)
        return 1

    wb = load_workbook(str(XLSX))
    ws = wb["SAE清单"]
    headers = [c.value for c in ws[1]]
    col_reason = headers.index("相关性判定原因") + 1

    if "判定原因来源" in headers:
        col_src = headers.index("判定原因来源") + 1
    else:
        col_src = col_reason + 1
        ws.insert_cols(col_src)
        headers.insert(col_src - 1, "判定原因来源")
        ws.cell(row=1, column=col_src, value="判定原因来源")

    # idempotent re-run: clear previously written values first
    n_rows = ws.max_row
    for r in range(2, n_rows + 1):
        ws.cell(row=r, column=col_reason, value=None)
        ws.cell(row=r, column=col_src, value=None)

    filled = 0
    filled_p1 = 0
    unmatched_reports = []
    for item in reasons:
        id_col = headers.index("受试者编号") + 1
        target_rows = [
            r
            for r in range(2, ws.max_row + 1)
            if str(ws.cell(row=r, column=id_col).value or "").strip() == item["sid"]
        ]
        if not target_rows:
            unmatched_reports.append(f"{item['sid']}（{item['sae']}）：TFL 清单中无对应行")
            continue

        desc_col = headers.index("SAE描述") + 1
        pt_col = headers.index("首选术语(PT)") + 1
        descs = {str(ws.cell(row=r, column=desc_col).value or "") for r in target_rows}

        if len(descs) == 1:
            # one SAE event split over several PT rows (e.g. Ⅰ期 G07: 咯血 + 支气管扩张)
            matched = target_rows
        else:
            n_desc = norm(item["sae"])
            matched = []
            for r in target_rows:
                desc = str(ws.cell(row=r, column=desc_col).value or "")
                pt = str(ws.cell(row=r, column=pt_col).value or "")
                if n_desc and (
                    n_desc in norm(desc)
                    or n_desc in norm(pt)
                    or norm(desc) in n_desc
                    or norm(pt) in n_desc
                ):
                    matched.append(r)
            if not matched and len(target_rows) == 1:
                matched = target_rows
        if not matched:
            unmatched_reports.append(f"{item['sid']}（{item['sae']}）：SAE 名称未匹配上清单行")
            continue

        phase_col = headers.index("期别") + 1
        for r in matched:
            ws.cell(row=r, column=col_reason, value=item["reason"])
            ws.cell(row=r, column=col_src, value=f"{item['label']}/{item['src']}")
            filled += 1
            if str(ws.cell(row=r, column=phase_col).value or "") == "Ⅰ期":
                filled_p1 += 1

    # ---- styling -------------------------------------------------------
    hdr_fill = PatternFill("solid", fgColor="1F4E79")
    hdr_font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
    body_font = Font(name="微软雅黑", size=10)
    rel_fill = PatternFill("solid", fgColor="FFF2CC")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col in (col_reason, col_src):
        c = ws.cell(row=1, column=col)
        c.fill = hdr_fill
        c.font = hdr_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border
        ws.column_dimensions[get_column_letter(col)].width = 70 if col == col_reason else 46
        for r in range(2, ws.max_row + 1):
            cell = ws.cell(row=r, column=col)
            cell.font = body_font
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if col == col_reason:
                cell.fill = rel_fill
    ws.row_dimensions[1].height = 32

    # ---- notes sheet ---------------------------------------------------
    ns = wb["说明与数据来源"]
    for row in ns.iter_rows(min_row=1, max_row=ns.max_row, max_col=1):
        if row[0].value == "相关性判定原因":
            ns.cell(
                row=row[0].row,
                column=2,
                value="取自肥城现场各受试者 SAE 总结报告中的“相关性：”段落原文（扫描件经 OCR 识别后逐字引用）。"
                "TFL 清单本身无该列；未找到对应总结报告的例次仍留空。",
            )
            ns.cell(row=row[0].row, column=2).alignment = Alignment(vertical="top", wrap_text=True)
            ns.cell(row=row[0].row, column=2).font = body_font
    extra = [
        (
            "判定原因来源",
            "新增列“判定原因来源”记录该行判定原因所引自的 SAE 总结报告文件名；为空表示无对应报告。",
        ),
        (
            "判定原因补充情况",
            f"共回填 {filled} 例次（Ⅰ期 {filled_p1} 例次、Ⅱ期 {filled - filled_p1} 例次），"
            f"引自Ⅰ期东阿现场、Ⅱ期肥城现场与邹城现场 SAE 总结报告中的“相关性：”段落；"
            f"其余例次无对应总结报告，保持留空。",
        ),
    ]
    if unmatched_reports:
        extra.append(("未匹配报告", "；".join(unmatched_reports)))

    degraded = sorted({f"{i['sid']}（{i['sae']}）" for i in reasons if not i["clean"]})
    if degraded:
        extra.append(
            (
                "OCR 质量提示",
                "以下例次的判定原因在扫描件中识别不完整（起始句缺失或文字残缺），"
                "已按可识别原文照录，建议对照原始报告核对：" + "、".join(degraded) + "。",
            )
        )

    existing = {}
    for row in ns.iter_rows(min_row=1, max_row=ns.max_row, max_col=1):
        if row[0].value:
            existing[row[0].value] = row[0].row
    for k, v in extra:
        r = existing.get(k) or ns.max_row + 1
        ns.cell(row=r, column=1, value=k)
        c = ns.cell(row=r, column=2, value=v)
        c.alignment = Alignment(vertical="top", wrap_text=True)
        for cc in (1, 2):
            ns.cell(row=r, column=cc).font = body_font
            ns.cell(row=r, column=cc).border = border
        existing[k] = r

    wb.save(str(XLSX))
    print(f"OK -> {XLSX}  ({filled} rows filled)", file=sys.stderr)
    if notes:
        print("NOTES:", *notes, sep="\n  ", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
