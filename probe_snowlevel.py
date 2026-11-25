"""One-off probe 2: find the data address behind White Risk's 'Snowfall level' chart."""
import hashlib, re, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 grimentz-dashboard-probe"}

def get(url, limit=12_000_000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(limit).decode("utf-8", "replace")

PAGE = "https://whiterisk.ch/en/conditions/bulletin?regionId=CH-4124"
html = get(PAGE)
print("html bytes:", len(html))
tags = re.findall(r'<(?:script|link)[^>]+>', html)
srcs = []
for t in tags:
    m = re.search(r'(?:src|href)="([^"]+\.(?:js|mjs))"', t)
    if m:
        srcs.append(m.group(1))
print("script/js references in html:")
for s in srcs:
    print("  ", s)
# inline hints
for m in list(re.finditer(r'snow[^"<>\s]{0,30}(?:level|line|limit)|schneefallgrenze', html, re.I))[:10]:
    print("html hint:", html[max(0, m.start()-80):m.end()+80].replace("\n", " "))

PATTERN = re.compile(r"snow[-_ ]?(?:fall)?[-_ ]?(?:level|line|limit)|schneefallgrenze|snowlevel|snowfalllevel|freezing", re.I)
seen_hash, seen_url, queue = set(), set(), []
for s in srcs:
    queue.append(urllib.parse.urljoin("https://whiterisk.ch/", s))
    queue.append(urllib.parse.urljoin(PAGE, s))
n = 0
while queue and n < 60:
    u = queue.pop(0)
    if u in seen_url:
        continue
    seen_url.add(u)
    try:
        js = get(u)
    except Exception as e:
        print("skip", u, type(e).__name__)
        continue
    h = hashlib.md5(js.encode()).hexdigest()
    if h in seen_hash or js.lstrip().startswith("<!"):
        print("same-as-shell/duplicate:", u)
        continue
    seen_hash.add(h)
    n += 1
    hits = list(PATTERN.finditer(js))
    print(f"\n--- {u} ({len(js)} bytes, {len(hits)} matches)")
    for m in hits[:8]:
        print("   ..." + js[max(0, m.start()-200):m.end()+260].replace("\n", " ") + "...")
    for m in list(re.finditer(r'(?:api/v2|reply/public/api/v2|aws\.slf\.ch/api)[A-Za-z0-9_\-./{}$`\'"+ ]{0,80}', js))[:25]:
        print("   api:", m.group(0))
    base = u.rsplit("/", 1)[0] + "/"
    for c in set(re.findall(r'["\'`]\.?/?((?:chunk|main|polyfills)-[A-Za-z0-9_]+\.js)["\'`]', js)):
        queue.append(base + c)
        queue.append("https://whiterisk.ch/" + c)

print("\n=== candidate API roots ===")
for u in ["https://whiterisk.ch/api/v2", "https://whiterisk.ch/api/v2/openapi.json", "https://whiterisk.ch/api/v2/docs",
          "https://pro.slf.ch/reply/public/api/v2", "https://pro.slf.ch/reply/public/api/v2/openapi.json",
          "https://aws.slf.ch/api/bulletin", "https://whiterisk.ch/api/current-avalanches"]:
    try:
        t = get(u, 300000)
        print("OK ", u, len(t), t[:300].replace("\n", " "))
    except Exception as e:
        print("ERR", u, type(e).__name__, getattr(e, "code", ""))
