import json

with open(
    r"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\misc_abstracts.json",
    encoding="utf-8",
) as f:
    data = json.load(f)
with open("misc_abs.txt", "w", encoding="utf-8") as out:
    for item in data:
        out.write(f"PMID: {item.get('pmid')} | DOI: {item.get('doi')}\n")
        out.write(f"Title: {item.get('title')}\n")
        out.write(f"Abstract:\n{item.get('abstract')}\n")
        out.write("-" * 80 + "\n")
