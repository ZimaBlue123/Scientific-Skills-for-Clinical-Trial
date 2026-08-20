import json

for pmid in ["34655522", "36868877", "37908361"]:
    path = rf"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\full_{pmid}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    text = data.get("full_text", "")
    # Find safety-related paragraphs
    paras = text.split("\n")
    out_path = rf"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\safety_{pmid}.txt"
    with open(out_path, "w", encoding="utf-8") as out:
        for p in paras:
            pl = p.lower()
            if any(
                kw in pl
                for kw in [
                    "adverse",
                    "safety",
                    "reactogenicity",
                    "injection site",
                    "pain",
                    "fatigue",
                    "fever",
                    "myalgia",
                    "headache",
                    "solicited",
                    "sae",
                    "serious",
                ]
            ):
                out.write(p + "\n")
