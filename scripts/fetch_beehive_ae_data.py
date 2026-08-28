"""
BEe-HIVe (NCT04193189) 完整 AE 数据提取
从 ClinicalTrials.gov API v2 下载 JSON，解析 adverseEventsModule
输出：SAE 明细 + 非严重 AE（otherEvents）明细，按组别分开
"""

import json
import sys
import urllib.request

URL = "https://clinicaltrials.gov/api/v2/studies/NCT04193189?format=json"
OUT = r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\_tmp_beehive.json"


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def main():
    data = json.loads(fetch())
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("saved raw json to", OUT)

    ae = data.get("resultsSection", {}).get("adverseEventsModule", {})
    print("=" * 80)
    print("adverseEventsModule keys:", list(ae.keys()))
    print("=" * 80)

    # event groups
    print("\n### EVENT GROUPS (风险人数/死亡/SAE/其他AE)")
    for g in ae.get("eventGroups", []):
        print(json.dumps(g, ensure_ascii=False))

    # serious events
    print("\n### SERIOUS EVENTS (SAE 明细)")
    for ev in ae.get("seriousEvents", []):
        stats = {}
        for s in ev.get("stats", []):
            stats[s.get("groupId")] = {
                "affected": s.get("numAffected"),
                "atRisk": s.get("numAtRisk"),
            }
        print(
            "- SOC:",
            ev.get("organSystem"),
            "| PT:",
            ev.get("event"),
            "| 严重度:",
            ev.get("severity"),
            "| 死亡:",
            ev.get("deathsNumAffected"),
        )
        for gid, st in stats.items():
            print("    ", gid, "->", st)

    # other events (非严重)
    print("\n### OTHER EVENTS (非严重 AE 明细)")
    for ev in ae.get("otherEvents", []):
        stats = {}
        for s in ev.get("stats", []):
            stats[s.get("groupId")] = {
                "affected": s.get("numAffected"),
                "atRisk": s.get("numAtRisk"),
            }
        print(
            "- SOC:",
            ev.get("organSystem"),
            "| PT:",
            ev.get("event"),
            "| 严重度:",
            ev.get("severity"),
        )
        for gid, st in stats.items():
            print("    ", gid, "->", st)

    print("\n### 总数统计")
    print("SAE 条目数:", len(ae.get("seriousEvents", [])))
    print("其他AE条目数:", len(ae.get("otherEvents", [])))


if __name__ == "__main__":
    sys.exit(main())
