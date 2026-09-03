import re
import urllib.request

url = "https://www.fda.gov/vaccines-blood-biologics/vaccines/heplisav-b"
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as res:
        html = res.read().decode("utf-8")
        for m in re.finditer(r"<a[^>]+href=[\'\"]([^\'\"]+)[\'\"][^>]*>([^<]+)</a>", html, re.I):
            href = m.group(1)
            text = m.group(2).strip()
            if "Review" in text or "Action" in text or "Memo" in text or "Statistical" in text:
                if href.startswith("/"):
                    href = "https://www.fda.gov" + href
                print(f"{text}: {href}")
except Exception as e:
    print(e)
