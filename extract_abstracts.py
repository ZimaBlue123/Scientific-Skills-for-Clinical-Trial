import json

with open(
    r"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\pubmed_abstracts.json",
    encoding="utf-8",
) as f:
    data = json.load(f)

with open(
    r"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\abstract_summary.txt",
    "w",
    encoding="utf-8",
) as out:
    for item in data:
        title = item.get("title", "")
        abstract = item.get("abstract", "")
        if not abstract:
            continue

        text = (title + " " + abstract).lower()
        if "cpg" in text and (
            "safety" in text or "safe" in text or "adverse" in text or "tolerat" in text
        ):
            out.write(f"PMID: {item.get('pmid')}\n")
            out.write(f"Title: {title}\n")
            out.write(f"DOI: {item.get('doi')}\n")
            out.write(f"Abstract Snippet: {abstract}\n")
            out.write("-" * 80 + "\n")
