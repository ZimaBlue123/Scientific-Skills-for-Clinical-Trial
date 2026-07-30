"""Find callers of scripts-to-be-merged."""
import os, re

ROOT = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial"
TARGETS = [
    "_extract_docx_text",
    "extract_docx_to_md",
    "convert_doc_to_docx",
    "convert_audit_report_md_to_docx",
]
RX = re.compile(r"(?:from %s import|import %s|runpy\.run_path)" % (r"(\w+)", r"(\w+)",))


def main():
    for target in TARGETS:
        print(f"=== callers of {target} ===")
        found = False
        for dp, dirs, files in os.walk(ROOT):
            if ".git" in dp or "_archive" in dp or os.sep + "skills" in dp:
                continue
            for f in files:
                if not f.endswith(".py"):
                    continue
                full = os.path.join(dp, f)
                try:
                    txt = open(full, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                if target in txt:
                    # crude check: contains an import / mention
                    if re.search(rf"\b{target}\b", txt):
                        rel = os.path.relpath(full, ROOT).replace("\\", "/")
                        print(f"  {rel}")
                        found = True
        if not found:
            print("  (no callers)")


if __name__ == "__main__":
    main()