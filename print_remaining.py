import json

with open(
    r"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\core_abstracts.json",
    encoding="utf-8",
) as f:
    data = json.load(f)
with open("temp_abs.txt", "w", encoding="utf-8") as out:
    for item in data:
        if item.get("pmid") in ["38575433", "37881130"]:
            out.write(f"PMID: {item.get('pmid')}\n")
            out.write(item.get("abstract") + "\n")
