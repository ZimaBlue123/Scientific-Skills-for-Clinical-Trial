"""Extract text from the ClinicalTrials.gov registry-record PDFs archived in the
literature library (used to confirm CMI endpoints before citation)."""

from pathlib import Path

from pypdf import PdfReader

OUT = Path(__file__).with_name("_registry_extract.txt")
_BUF: list[str] = []


def print(*args, **kwargs):  # noqa: A001 - simple tee to file
    _BUF.append(" ".join(str(a) for a in args))


BASE = (
    Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials")
    / "文献库-F2F Meeting"
    / "02_同类产品-CpG佐剂与对照疫苗"
    / "HEPLISAV-B Dynavax"
    / "新增-细胞免疫补充（2026-09-15）"
)

TARGETS = [
    "NCT04843852_BOOST-9_HEPLISAV-B_chronic-HBV_clinicaltrial-record.pdf",
    "NCT05727267_TherVacB_HEPLISAV-B-arm_clinicaltrial-record.pdf",
]

for name in TARGETS:
    path = BASE / name
    print("=" * 70)
    print(name, "exists=", path.exists())
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001
        print("READ ERROR:", exc)
        continue
    print("pages", len(reader.pages))
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        print("-" * 20, "page", i, "chars", len(text))
        if text.strip():
            print(text[:6000])
        else:
            res = page.get("/Resources", {})
            fonts = res.get("/Font", {})
            try:
                fonts = fonts.get_object()
            except Exception:  # noqa: BLE001
                pass
            print(
                "  [no text layer] fonts:",
                list(fonts)[:10] if hasattr(fonts, "__iter__") else fonts,
            )
            xobj = res.get("/XObject", {})
            try:
                xobj = xobj.get_object()
            except Exception:  # noqa: BLE001
                pass
            print("  xobjects:", list(xobj)[:10] if hasattr(xobj, "__iter__") else xobj)

OUT.write_text("\n".join(_BUF), encoding="utf-8")
