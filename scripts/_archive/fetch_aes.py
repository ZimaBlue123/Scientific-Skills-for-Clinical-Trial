import json
import urllib.request

url = "https://clinicaltrials.gov/api/v2/studies/NCT03572062"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req).read()
d = json.loads(resp)
aes = d.get("resultsSection", {}).get("adverseEventsModule", {})

terms = [
    "Injection site pain (PAIN AT INJECTION SITE)",
    "Injection site erythema (REDNESS)",
    "Injection site swelling (SWELLING)",
    "Fatigue (FATIGUE)",
    "Headache (HEADACHE)",
    "Myalgia (MUSCLE PAIN)",
    "Arthralgia (JOINT PAIN)",
    "Pyrexia (FEVER)",
]

groups = {
    "EG004": "RSVpreF 240mcg + Al(OH)3",
    "EG005": "RSVpreF 240mcg + CpG/Al(OH)3",
    "EG006": "RSVpreF 240mcg (Unadjuvanted)",
    "EG007": "Placebo",
}

print("AE Incidence for selected groups (N~30 per group):")
for evt in aes.get("otherEvents", []):
    term = evt.get("term", "")
    if term in terms:
        print(f"\n{term}:")
        for st in evt.get("stats", []):
            if st["groupId"] in groups:
                print(f"  {groups[st['groupId']]}: {st.get('numAffected', 0)}")
