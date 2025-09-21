City data workflow

Overview
- data/cities.in.json: Master curated list of Indian cities with lat/lon used to generate a static Python module.
- scripts/build_city_coords.py: Converts the JSON into backend/city_coords.py for fast, offline lookups.
- backend/city_coords.py: Static dictionary of CITY_COORDINATES and DISPLAY_NAMES consumed by the backend and frontend.

Input JSON format
- Array of objects. Required fields: city (display name), lat, lon. Optional: aliases (array)
[
  {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "aliases": ["Bombay"]},
  {"city": "Navi Mumbai", "lat": 19.0330, "lon": 73.0297}
]

How to regenerate backend/city_coords.py
1) Place/Update cities.in.json with the desired list (~3000 rows)
2) Run the builder:
   - Windows (cmd):
     python scripts\build_city_coords.py
   - PowerShell:
     python scripts/build_city_coords.py
3) Restart the backend to pick up the new module

Notes
- Keys are normalized to lowercase and spaces collapsed.
- Duplicates by normalized name are skipped (first occurrence wins).
- The frontend dropdown pulls its list from the module to guarantee distance lookups work.
