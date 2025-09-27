#!/usr/bin/env python3
"""
Fetch ~3000 Indian cities with coordinates from GeoNames and write data/cities.in.json

Data source: GeoNames cities500 (CC-BY 4.0)
Download: https://download.geonames.org/export/dump/cities500.zip
Docs:     https://download.geonames.org/export/dump/

License attribution required by GeoNames (CC-BY 4.0):
  Contains information from GeoNames (https://www.geonames.org/), which is
  made available here under the Open Data Commons Open Database License (ODbL)
  and Creative Commons Attribution 4.0 License.

This script:
  - Downloads cities500.zip
  - Filters to India (country code IN), feature class 'P' (populated place)
  - Sorts by population (desc), keeps top N (default 3000)
  - Deduplicates by normalized city name (keep highest population)
  - Emits data/cities.in.json with {city, lat, lon, aliases?}
  - Does NOT include states to keep parity with the app’s design

Run:
  python scripts/fetch_india_cities.py --limit 3000
  python scripts\\fetch_india_cities.py --limit 3000  # Windows cmd

Then build:
  python scripts/build_city_coords.py
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import os
import sys
import zipfile
from urllib.request import urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
TMP_DIR = os.path.join(DATA_DIR, 'tmp')
OUT_JSON = os.path.join(DATA_DIR, 'cities.in.json')

GEONAMES_URL = 'https://download.geonames.org/export/dump/cities500.zip'

# Columns for cities500 per GeoNames docs
# 0 geonameid, 1 name, 2 asciiname, 3 alternatenames, 4 latitude, 5 longitude,
# 6 feature class, 7 feature code, 8 country code, 9 cc2, 10 admin1, 11 admin2,
# 12 admin3, 13 admin4, 14 population, 15 elevation, 16 dem, 17 timezone, 18 mod date

CURATED_ALIAS_WHITELIST = {
    'bombay', 'bangalore', 'blr', 'calcutta', 'madras', 'puducherry', 'allahabad',
    'banaras', 'benares', 'benaras', 'gurugram', 'vizag', 'thiruvananthapuram'
}


def normalize_key(name: str) -> str:
    return ' '.join((name or '').strip().lower().split())


def fetch_zip(url: str) -> bytes:
    with urlopen(url) as resp:
        return resp.read()


def parse_cities500(zbytes: bytes, limit: int) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
        # cities500.zip contains cities500.txt
        txt_name = next((n for n in zf.namelist() if n.endswith('.txt')), None)
        if not txt_name:
            raise RuntimeError('cities500.txt not found in zip')
        with zf.open(txt_name) as f:
            text = io.TextIOWrapper(f, encoding='utf-8')
            reader = csv.reader(text, delimiter='\t')
            rows = []
            for cols in reader:
                if len(cols) < 19:
                    continue
                country = cols[8]
                if country != 'IN':
                    continue
                fclass = cols[6]
                if fclass != 'P':
                    continue
                name = cols[1].strip()
                asciiname = cols[2].strip() or name
                try:
                    lat = float(cols[4])
                    lon = float(cols[5])
                except Exception:
                    continue
                try:
                    population = int(cols[14]) if cols[14] else 0
                except Exception:
                    population = 0
                alt = cols[3].strip()
                alt_names = [a.strip() for a in alt.split(',') if a.strip()] if alt else []

                rows.append({
                    'name': name,
                    'asciiname': asciiname,
                    'lat': lat,
                    'lon': lon,
                    'population': population,
                    'alternatenames': alt_names,
                })

    # Deduplicate by normalized asciiname, keeping the highest population
    by_key: dict[str, dict] = {}
    for r in rows:
        key = normalize_key(r['asciiname'])
        prev = by_key.get(key)
        if (prev is None) or (r['population'] > prev['population']):
            by_key[key] = r

    # Sort by population desc, take top limit
    selected = sorted(by_key.values(), key=lambda x: x['population'], reverse=True)[:limit]

    # Build JSON records; include only curated alternates if present
    out = []
    for r in selected:
        aliases = []
        for a in r['alternatenames']:
            al = a.strip()
            if not al:
                continue
            if normalize_key(al) in CURATED_ALIAS_WHITELIST:
                if al not in aliases:
                    aliases.append(al)
        item = {
            'city': r['name'],
            'lat': round(r['lat'], 6),
            'lon': round(r['lon'], 6),
        }
        if aliases:
            item['aliases'] = aliases
        out.append(item)

    return out


def main():
    parser = argparse.ArgumentParser(description='Fetch ~N Indian cities')
    parser.add_argument('--limit', type=int, default=3000, help='Max cities to keep (by population)')
    args = parser.parse_args()

    os.makedirs(TMP_DIR, exist_ok=True)
    try:
        print(f'Downloading {GEONAMES_URL} ...')
        data = fetch_zip(GEONAMES_URL)
        print(f'Downloaded {len(data)//1024} KB')
    except Exception as e:
        print('Download failed:', e)
        sys.exit(2)

    try:
        cities = parse_cities500(data, limit=args.limit)
        print(f'Parsed {len(cities)} cities (top {args.limit})')
    except Exception as e:
        print('Parse failed:', e)
        sys.exit(3)

    try:
        with open(OUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(cities, f, ensure_ascii=False, indent=2)
        print(f'Wrote {len(cities)} rows to {OUT_JSON}')
    except Exception as e:
        print('Write failed:', e)
        sys.exit(4)

    print('\nNext: build the Python module:')
    print('  python scripts\\build_city_coords.py')


if __name__ == '__main__':
    main()
