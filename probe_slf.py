#!/usr/bin/env python3
"""One-off helper: finds out how SLF's open measurement API serves manual station 4GR0 (Grimentz).
It only prints what it finds; it changes nothing and uses no API key."""
import json
import re
import urllib.request

BASE = "https://measurement-api.slf.ch"
STATION = "4GR0"


def get(path, limit=1500):
    url = BASE + path
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "grimentz-dashboard-probe"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            print(f"--- {path} -> HTTP {r.status}, {len(body)} bytes")
            print(body[:limit])
            return body
    except Exception as e:
        print(f"--- {path} -> {type(e).__name__}: {e}")
        return None


def main():
    # 1. Look for the API description (OpenAPI) and print every path that looks relevant.
    for spec in ["/public/api/openapi.json", "/public/api/v3/api-docs", "/v3/api-docs", "/openapi.json",
                 "/public/api/swagger.json", "/swagger.json", "/public/api/docs/openapi.json"]:
        body = get(spec, limit=200)
        if body:
            try:
                paths = list(json.loads(body).get("paths", {}))
                print("API PATHS:")
                for p in paths:
                    print("  ", p)
                break
            except Exception:
                pass
    # 2. The landing page often names the spec file.
    page = get("/", limit=1200)
    if page:
        print("Spec hints:", re.findall(r'["\'(]([^"\'()\s]+\.(?:json|yaml|yml))', page)[:10])
    # 3. Guess the manual-station endpoints for 4GR0.
    for p in [f"/public/api/study-plot/station/{STATION}/measurements?period_in_days=7",
              f"/public/api/study-plots/{STATION}/measurements?period_in_days=7",
              f"/public/api/study-plot/{STATION}/measurements?period_in_days=7",
              "/public/api/study-plot/stations", "/public/api/study-plots",
              "/public/api/manual/stations", f"/public/api/manual/station/{STATION}/measurements?period_in_days=7"]:
        get(p)


if __name__ == "__main__":
    main()
