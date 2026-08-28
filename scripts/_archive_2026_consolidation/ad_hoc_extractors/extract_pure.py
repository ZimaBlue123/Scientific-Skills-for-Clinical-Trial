import os
import re
import xml.etree.ElementTree as ET
import zipfile


def extract_text_from_docx(filename):
    paras = []
    try:
        with zipfile.ZipFile(filename) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            for p in tree.iter():
                if p.tag.endswith("}p"):
                    p_text = []
                    for node in p.iter():
                        if node.tag.endswith("}t") and node.text:
                            p_text.append(node.text)
                    if p_text:
                        paras.append("".join(p_text))
    except Exception:
        pass
    return paras


os.chdir("review_materials")

with open("extracted_text.txt", "w", encoding="utf-8") as f:
    for file in os.listdir("."):
        if file.endswith(".docx") and any(proj in file for proj in ["009", "009B", "006"]):
            f.write(f"\n========== {file} ==========\n")
            lines = extract_text_from_docx(file)
            snippets = set()
            for l in lines:
                l = l.replace("\n", " ").strip()
                if (
                    ("剂量" in l or "用量" in l or "mg" in l or "最大" in l or "最低" in l)
                    and len(l) > 3
                    and len(l) < 500
                ):
                    snippets.add(l)

            for s in list(snippets):
                if (
                    "最大" in s
                    or "最高" in s
                    or "每日" in s
                    or "mg" in s
                    or "最低" in s
                    or "用量" in s
                    or "LDD" in s
                    or "MDD" in s
                ) and re.search(r"\d+", s):
                    f.write(f" - {s}\n")
