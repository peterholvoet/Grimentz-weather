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

LAT, LON = 46.177, 7.577
# name -> elevation in metres (meteoblue adjusts temperature to this height)
LOCATIONS = {"village": 1570, "summit": 2900}
PACKAGES = "basic-1h_basic-day"
OUT = sys.argv[1] if len(sys.argv) > 1 else "site/data.json"


def fetch(asl, key):
    query = urllib.parse.urlencode({"lat": LAT, "lon": LON, "asl": asl, "apikey": key})
    url = f"https://my.meteoblue.com/packages/{PACKAGES}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"meteoblue returned HTTP {e.code} for elevation {asl} m")
    except Exception as e:  # network error, bad JSON, timeout
        sys.exit(f"Request failed for elevation {asl} m: {type(e).__name__}")
    if "data_1h" not in body or "data_day" not in body:
        sys.exit(f"Unexpected response for elevation {asl} m: keys {sorted(body)[:6]}")
    return body


def main():
    key = os.environ.get("METEOBLUE_API_KEY")
    if not key:
        sys.exit("METEOBLUE_API_KEY is not set")
    data = {name: fetch(asl, key) for name, asl in LOCATIONS.items()}
    out = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "locations": data,
    }
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {OUT} with {len(data)} elevations")


if __name__ == "__main__":
    main()
