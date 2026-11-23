#!/usr/bin/env python3
"""One-off helper: looks up the current SLF avalanche bulletin (CAAML JSON) and prints what it says
for region CH-4124. It only prints; it changes nothing and uses no API key."""
import json
import urllib.request

REGION = "CH-4124"
HOST = "https://aws.slf.ch"


def get(url, limit=0):
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "grimentz-dashboard-probe"})
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read().decode("utf-8", "replace")
        print(f"--- {url} -> HTTP {r.status}, {len(body)} bytes")
        if limit:
            print(body[:limit])
        return body
    except Exception as e:
        print(f"--- {url} -> {type(e).__name__}: {e}")
        return None


def find_regions(node, found):
    """Collect every dict that looks like a region reference."""
    if isinstance(node, dict):
        rid = node.get("regionID") or node.get("id")
        if isinstance(rid, str) and rid.startswith("CH-"):
            found.append(rid)
        for v in node.values():
            find_regions(v, found)
    elif isinstance(node, list):
        for v in node:
            find_regions(v, found)


def main():
    # 1. API description, if there is one.
    for spec in ["/api/bulletin/caaml/openapi.json", "/api/bulletin/openapi.json", "/openapi.json"]:
        body = get(HOST + spec, limit=150)
        if body:
            try:
                print("API PATHS:", list(json.loads(body).get("paths", {})))
                break
            except Exception:
                pass
    # 2. The bulletin itself.
    for path in ["/api/bulletin/caaml/en/json", "/api/bulletin/caaml/en", "/api/bulletin/caaml"]:
        body = get(HOST + path, limit=300)
        if not body:
            continue
        try:
            data = json.loads(body)
        except Exception:
            print("(not JSON)")
            continue
        print("Top-level keys:", list(data)[:10] if isinstance(data, dict) else type(data))
        bulletins = data.get("bulletins", []) if isinstance(data, dict) else []
        print("Bulletins in file:", len(bulletins))
        for b in bulletins:
            ids = []
            find_regions(b.get("regions", []), ids)
            if REGION in ids:
                print(f"\n===== BULLETIN FOR {REGION} =====")
                print(json.dumps(b, ensure_ascii=False, indent=1)[:9000])
                return
        allids = []
        find_regions(bulletins, allids)
        print("No bulletin lists", REGION, "- regions seen:", sorted(set(allids))[:80])
        return


if __name__ == "__main__":
    main()
