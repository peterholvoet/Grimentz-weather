"""One-off probe: which variables do the free-API packages return? Prints variable names only."""
import json, os, urllib.error, urllib.request

KEY = os.environ["METEOBLUE_API_KEY"]
LAT, LON, ASL = 46.17729798, 7.57090393, 1657
PACKAGES = ["clouds-3h_clouds-day", "air-3h_air-day", "wind-3h_wind-day", "agro-3h_agro-day"]

for pkg in PACKAGES:
    url = f"https://my.meteoblue.com/packages/{pkg}?lat={LAT}&lon={LON}&asl={ASL}&format=json&apikey={KEY}"
    print(f"\n=== {pkg} ===")
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read(300).decode("utf-8", "replace").replace(KEY, "***"))
        continue
    except Exception as e:
        print("Failed:", type(e).__name__)
        continue
    for block, content in data.items():
        if isinstance(content, dict) and "time" in content:
            print(f"[{block}] {len(content['time'])} steps, first time {content['time'][0]}")
            for name, vals in content.items():
                if name != "time" and isinstance(vals, list):
                    print(f"   {name}: {vals[:4]}")
