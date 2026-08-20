import os
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

with open("009_search.txt", "w", encoding="utf-8") as f:
    for file in os.listdir("."):
        if file.endswith(".docx") and "009" in file:
            f.write(f"\n========== {file} ==========\n")
            lines = extract_text_from_docx(file)
            for l in lines:
                l = l.replace("\n", " ").strip()
                if (
                    "规格" in l
                    or "HBsAg" in l
                    or "含量" in l
                    or "活性成分" in l
                    or "每剂" in l
                ):
                    if "20" in l or "10" in l or "5" in l:
                        f.write(f" - {l}\n")
