"""One-off probe 3: find 'snowfallLimit' in the SLF bulletin data and show how White Risk reads it."""
import json, re, urllib.request

UA = {"User-Agent": "Mozilla/5.0 grimentz-dashboard-probe", "Accept": "application/json, text/plain, */*"}

def get(url, limit=30_000_000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(limit).decode("utf-8", "replace")

REGION = "CH-4124"
KEY = re.compile(r"snowfall|snowline|timeseries|weather|temperatures|newsnow|wind", re.I)

def walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}"
            if KEY.search(k):
                out.append((p, v))
            walk(v, p, out)
    elif isinstance(o, list):
        for i, v in enumerate(o[:3]):
            walk(v, f"{path}[{i}]", out)

print("=== CAAML bulletin: weather-like keys for", REGION, "===")
for lang_url in ["https://aws.slf.ch/api/bulletin/caaml/en/json"]:
    try:
        data = json.loads(get(lang_url))
    except Exception as e:
        print("failed", lang_url, type(e).__name__, e)
        continue
    bl = data.get("bulletins", [])
    mine = [b for b in bl if any(r.get("regionID") == REGION for r in b.get("regions", []))]
    print("bulletins:", len(bl), "for region:", len(mine))
    for b in mine[:1]:
        print("top-level keys:", sorted(b.keys()))
        out = []
        walk(b, "bulletin", out)
        seen = set()
        for p, v in out:
            base = re.sub(r"\[\d+\]", "[]", p)
            if base in seen:
                continue
            seen.add(base)
            txt = json.dumps(v)
            print(p, "->", txt[:500])
    raw = json.dumps(data)
    print("'snowfallLimit' anywhere in file:", "snowfallLimit" in raw, "| 'timeSeries':", "timeSeries" in raw)

print("\n=== how the page loads it ===")
CHUNKS = ["chunk-3OZH54GI.js", "chunk-275B2EXN.js", "main-2C3OG2HY.js"]
for c in CHUNKS:
    try:
        js = get("https://whiterisk.ch/" + c)
    except Exception as e:
        print("skip", c, type(e).__name__)
        continue
    print(f"\n--- {c} ({len(js)} bytes)")
    for m in list(re.finditer(r"Hn=|aws\.slf\.ch|/bulletin|api/bulletin|bulletin/caaml|weatherForecasts|weather_?[Ff]orecast", js))[:14]:
        print("   ..." + js[max(0, m.start()-150):m.end()+300].replace("\n", " ") + "...")
