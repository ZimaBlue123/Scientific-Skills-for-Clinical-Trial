#!/usr/bin/env python3
"""Extract text from the three TVAX-006 source files for PPT building.

Sources:
  1. TVAX-006 三期沟通交流 PPT (red template) -> PPTX full text
  2. Theravac Zoster phase 1 protocol V3.1 -> DOCX markdown
  3. CSR body TVAX-006-01 Phase1 -> DOCX markdown
Outputs to review_materials/006 PPT/_extracted/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract_office_utils import extract_full, extract_docx_to_markdown  # noqa: E402

BASE = Path(r"E:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial/review_materials/006 PPT")
OUT = BASE / "_extracted"
OUT.mkdir(parents=True, exist_ok=True)

PPTX = BASE / "TVAX-006项目3期临床试验启动前沟通交流ppt-红色模板-20260630.pptx"
PROTOCOL = next(BASE.glob("Theravac*protocol*.docx"))
CSR = next(BASE.glob("CSR body*Phase1*.docx"))

# 1. PPTX
extract_full(str(PPTX), str(OUT / "red_template_pptx.txt"))

# 2. Protocol
try:
    md = extract_docx_to_markdown(PROTOCOL)
    (OUT / "aus_phase1_protocol.md").write_text(md, encoding="utf-8")
    print(f"protocol OK: {len(md)} chars")
except Exception as e:
    print(f"protocol FAILED: {e}")

# 3. CSR
try:
    md = extract_docx_to_markdown(CSR)
    (OUT / "aus_phase1_csr.md").write_text(md, encoding="utf-8")
    print(f"csr OK: {len(md)} chars")
except Exception as e:
    print(f"csr FAILED: {e}")

print("DONE")
