import json

with open(
    r"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\ct_cpg_has_results.json",
    encoding="utf-8",
) as f:
    data = json.load(f)

with open(
    r"C:\Users\Administrator\.gemini\antigravity\brain\055f4f97-3ebf-4469-983d-3cf006f715a1\scratch\ct_cpg_summary.txt",
    "w",
    encoding="utf-8",
) as out:
    for study in data.get("studies", []):
        proto = study.get("protocolSection", {})
        nct_id = proto.get("identificationModule", {}).get("nctId")
        title = proto.get("identificationModule", {}).get("briefTitle")
        conditions = proto.get("conditionsModule", {}).get("conditions", [])

        # Check if it's cancer/tumor/melanoma
        cond_text = " ".join(conditions).lower()
        if any(
            c in cond_text
            for c in [
                "cancer",
                "melanoma",
                "carcinoma",
                "tumor",
                "lymphoma",
                "leukemia",
            ]
        ):
            continue  # skip cancer therapeutic

        interventions = []
        for arm in proto.get("armsInterventionsModule", {}).get("interventions", []):
            interventions.append(arm.get("name", ""))

        interv_text = " ".join(interventions).lower()

        # We want vaccines
        if (
            "vaccin" not in title.lower()
            and "vaccin" not in interv_text
            and "vaccin" not in cond_text
        ):
            # might not be a vaccine, but CpG is used for allergy too
            pass

        out.write(f"NCT: {nct_id}\n")
        out.write(f"Title: {title}\n")
        out.write(f"Conditions: {', '.join(conditions)}\n")
        out.write(f"Interventions: {', '.join(interventions)}\n")
        out.write("-" * 80 + "\n")
