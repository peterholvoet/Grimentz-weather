#!/usr/bin/env python3
"""Fetch the Grimentz forecast from the meteoblue API and write one JSON file.

The API key is read from the METEOBLUE_API_KEY environment variable and is
never written to the output file or printed.

Usage: python3 fetch_meteoblue.py [output_path]
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# name -> coordinates and elevation in metres ("asl": meteoblue adjusts temperature to this height).
# If "asl" is left out, meteoblue uses its own terrain height for the coordinates.
# The names "village" and "summit" are the keys the web page looks up; only their labels change there.
LOCATIONS = {
    "village": {"lat": 46.17729798, "lon": 7.57090393, "asl": 1657},  # Taillis chalet
    "summit": {"lat": 46.18407500, "lon": 7.53244822, "asl": 2595},  # Orzival
}
PACKAGES = "basic-1h_basic-day"

# SLF manual measuring station at Grimentz: snow read by hand each morning (open data, no key, CC BY 4.0).
SLF_STATION = {"code": "4GR0", "name": "Grimentz", "elevation": 1560}
OUT = sys.argv[1] if len(sys.argv) > 1 else "site/data.json"


def fetch(name, loc, key):
    params = {"lat": loc["lat"], "lon": loc["lon"], "apikey": key}
    if "asl" in loc:
        params["asl"] = loc["asl"]
    query = urllib.parse.urlencode(params)
    url = f"https://my.meteoblue.com/packages/{PACKAGES}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"meteoblue returned HTTP {e.code} for {name}")
    except Exception as e:  # network error, bad JSON, timeout
        sys.exit(f"Request failed for {name}: {type(e).__name__}")
    if "data_1h" not in body or "data_day" not in body:
        sys.exit(f"Unexpected response for {name}: keys {sorted(body)[:6]}")
    return body


def fetch_manual_station():
    """Daily hand measurements (snow depth, new snow in 24 h) from the SLF observer.
    Never stops the forecast update: returns None if SLF cannot be reached."""
    code = SLF_STATION["code"]
    url = f"https://measurement-api.slf.ch/public/api/study-plot/station/{code}/measurements?period_in_days=7"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "grimentz-dashboard"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.load(resp)
        rows = [{"date": r["measure_date"][:10], "hs": r.get("HS"), "hn": r.get("HN_1D")}
                for r in raw if r.get("measure_date")]
        rows.sort(key=lambda r: r["date"])
        if not rows:
            raise ValueError("no rows")
    except Exception as e:
        print(f"SLF station data not available: {type(e).__name__}")
        return None
    return {**SLF_STATION, "rows": rows}


def main():
    key = os.environ.get("METEOBLUE_API_KEY")
    if not key:
        sys.exit("METEOBLUE_API_KEY is not set")
    data = {name: fetch(name, loc, key) for name, loc in LOCATIONS.items()}
    out = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "locations": data,
    }
    observation = fetch_manual_station()
    if observation:
        out["observation"] = observation
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {OUT} with {len(data)} locations")


if __name__ == "__main__":
    main()
