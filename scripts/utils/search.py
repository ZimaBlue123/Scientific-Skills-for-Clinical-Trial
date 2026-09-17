import urllib.parse
import urllib.request


def search_ddg(query):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        html = urllib.request.urlopen(req).read().decode("utf-8")
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.in_snippet = False

            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    for k, v in attrs:
                        if k == "class" and "result__snippet" in v:
                            self.in_snippet = True

            def handle_data(self, data):
                if self.in_snippet:
                    self.results.append(data.strip())

            def handle_endtag(self, tag):
                if tag == "a" and self.in_snippet:
                    self.in_snippet = False

        p = DDGParser()
        p.feed(html)
        return "\n".join(p.results)
    except Exception as e:
        return str(e)


print(search_ddg('"6.3" "9.7" "5.8" "3.7" ECDC'))
