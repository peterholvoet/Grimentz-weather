"""One-off probe: where does White Risk get its 'Snowfall level' chart from? Prints matches only."""
import json, re, urllib.request, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 grimentz-dashboard-probe"}

def get(url, limit=8_000_000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(limit).decode("utf-8", "replace")

PAGE = "https://whiterisk.ch/en/conditions/bulletin?regionId=CH-4124"
PATTERN = re.compile(r"snow[-_ ]?(fall)?[-_ ]?(level|line|limit)|snowfall_?level|freezing|schneefallgrenze", re.I)

print("=== page ===")
try:
    html = get(PAGE)
    print("html bytes:", len(html))
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', html) + re.findall(r'href="([^"]+\.js)"', html)
except Exception as e:
    print("page failed:", type(e).__name__, e)
    html, scripts = "", []

seen = set()
queue = [urllib.parse.urljoin(PAGE, s) for s in scripts]
print("scripts:", len(queue))
while queue and len(seen) < 40:
    u = queue.pop(0)
    if u in seen or "whiterisk" not in u and "slf" not in u:
        continue
    seen.add(u)
    try:
        js = get(u)
    except Exception as e:
        print("skip", u, type(e).__name__)
        continue
    hits = list(PATTERN.finditer(js))
    apis = set(re.findall(r'https?://[a-z0-9.\-]*(?:slf|whiterisk|wsl)[a-z0-9.\-]*/[A-Za-z0-9_\-./{}$]*', js))
    print(f"\n--- {u} ({len(js)} bytes, {len(hits)} matches)")
    for h in hits[:6]:
        print("   ..." + js[max(0, h.start() - 120):h.end() + 160].replace("\n", " ") + "...")
    for a in sorted(apis)[:25]:
        print("   url:", a)
    # follow chunk references
    for c in re.findall(r'["\'](/?[A-Za-z0-9_\-./]+\.js)["\']', js)[:30]:
        queue.append(urllib.parse.urljoin(u, c))

print("\n=== measurement-api docs ===")
for p in ["/public/api/docs", "/public/api/openapi.json", "/openapi.json", "/public/api/swagger.json", "/docs", "/public/api/"]:
    u = "https://measurement-api.slf.ch" + p
    try:
        t = get(u, 400000)
        print(u, "OK", len(t))
        for m in list(re.finditer(r'"(/[^"]*)"\s*:\s*\{', t))[:80]:
            print("   path", m.group(1))
        break
    except Exception as e:
        print(u, type(e).__name__)
