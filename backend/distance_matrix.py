# backend/distance_matrix.py
"""
Distance matrix for Indian cities using latitude/longitude and Haversine formula.

Behaviour:
- Use the hardcoded CITY_COORDINATES first.
- If a requested city is not present, fallback to geopy.Nominatim to fetch coordinates.
- Newly-fetched coordinates are appended to this script file (as CITY_COORDINATES entries)
  so future runs see the city in the hardcoded list.
"""

import os
import re
from math import radians, sin, cos, sqrt, atan2

# -------------------------
# Hardcoded coordinates (your original list — kept intact)
# -------------------------
CITY_COORDINATES = {
    "gurgaon": (28.4595, 77.0266),
    "bhubaneswar": (20.2961, 85.8245),
    "mysore": (12.2958, 76.6394),
    "trivandrum": (8.5241, 76.9366),  # Thiruvananthapuram
    "kochi": (9.9312, 76.2673),
    "guwahati": (26.1445, 91.7362),
    "jamshedpur": (22.8046, 86.2029),
    "dehradun": (30.3165, 78.0322),
    "mangalore": (12.9141, 74.8560),
    "siliguri": (26.7271, 88.3953),
    "gandhinagar": (23.2156, 72.6369),
    "pondicherry": (11.9416, 79.8083),
    "agra": (27.1767, 78.0081),
    "ahmedabad": (23.0225, 72.5714),
    "amritsar": (31.6340, 74.8723),
    "aurangabad": (19.8762, 75.3433),
    "bengaluru": (12.9716, 77.5946),
    "bhopal": (23.2599, 77.4126),
    "chandigarh": (30.7333, 76.7794),
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "delhi": (28.6139, 77.2090),
    "dhanbad": (23.7957, 86.4304),
    "faridabad": (28.4089, 77.3178),
    "ghaziabad": (28.6692, 77.4538),
    "gwalior": (26.2183, 78.1828),
    "howrah": (22.5958, 88.2636),
    "hyderabad": (17.3850, 78.4867),
    "indore": (22.7196, 75.8577),
    "jabalpur": (23.1815, 79.9864),
    "jaipur": (26.9124, 75.7873),
    "jodhpur": (26.2389, 73.0243),
    "kalyan-dombivli": (19.2403, 73.1305),
    "kanpur": (26.4499, 80.3319),
    "kolkata": (22.5726, 88.3639),
    "kota": (25.2138, 75.8648),
    "lucknow": (26.8467, 80.9462),
    "ludhiana": (30.9005, 75.8573),
    "madurai": (9.9252, 78.1198),
    "meerut": (28.9845, 77.7064),
    "mohali": (30.7046, 76.7179),
    "mumbai": (19.0760, 72.8777),
    "nagpur": (21.1458, 79.0882),
    "nashik": (19.9975, 73.7898),
    "navi mumbai": (19.0330, 73.0297),
    "patna": (25.5941, 85.1376),
    "pimpri-chinchwad": (18.6298, 73.7997),
    "prayagraj": (25.4358, 81.8463),
    "pune": (18.5204, 73.8567),
    "raipur": (21.2514, 81.6296),
    "rajkot": (22.3039, 70.8022),
    "ranchi": (23.3441, 85.3096),
    "srinagar": (34.0837, 74.7973),
    "surat": (21.1702, 72.8311),
    "thane": (19.2183, 72.9781),
    "vadodara": (22.3072, 73.1812),
    "varanasi": (25.3176, 82.9739),
    "vasai-virar": (19.3919, 72.8397),
    "vijayawada": (16.5062, 80.6480),
    "visakhapatnam": (17.6868, 83.2185),
}

# -------------------------
# Common city aliases
# -------------------------
CITY_ALIASES = {
    # Use canonical keys that exist in CITY_COORDINATES (left side)
    "mumbai": ["bombay", "mumbai"],
    "bengaluru": ["bengaluru", "bangalore"],  # canonical key exists in CITY_COORDINATES
    "kolkata": ["calcutta", "kolkata"],
    "chennai": ["madras", "chennai"],
    "hyderabad": ["hyderabad"],
    "pune": ["pune"],
    "ahmedabad": ["ahmedabad"],
    "jaipur": ["jaipur"],
    "delhi": ["new delhi", "delhi"],
    "lucknow": ["lucknow"],
    "kanpur": ["kanpur"],
    "agra": ["agra"],
    "varanasi": ["varanasi", "banaras", "benares"],
    "rajkot": ["rajkot"],
    "vijayawada": ["vijayawada"],
    "madurai": ["madurai"],
    # Additional helpful aliases
    "trivandrum": ["trivandrum", "thiruvananthapuram"],
    "gurgaon": ["gurgaon", "gurugram"],
    "vadodara": ["vadodara", "baroda"],
    "prayagraj": ["prayagraj", "allahabad"],
    "visakhapatnam": ["visakhapatnam", "vishakhapatnam", "vizag"],
    "navi mumbai": ["navi mumbai", "navi-mumbai"],
    "vasai-virar": ["vasai-virar", "vasai virar"],
    "kalyan-dombivli": ["kalyan-dombivli", "kalyan dombivli"],
    "pondicherry": ["pondicherry", "puducherry"],
    "coimbatore": ["coimbatore", "kovai"],
    "bhubaneswar": ["bhubaneswar", "bhubaneshwar"],
}

def normalize_city_name(city: str) -> str:
    """
    Normalize city name to standard form for distance lookup.
    """
    if not city:
        return ""
    city_lower = city.strip().lower()
    for standard_name, aliases in CITY_ALIASES.items():
        if city_lower in aliases:
            return standard_name
    return city_lower

# -------------------------
# geopy lazy import
# -------------------------
_geopy_available = True
try:
    from geopy.geocoders import Nominatim
    _GEOLocator = Nominatim(user_agent="distance-matrix-app")
except Exception:
    _geopy_available = False
    _GEOLocator = None

def _normalize_for_compare(s: str) -> str:
    """Light normalization: lowercase, trim, unify hyphens/underscores to single spaces, collapse whitespace."""
    s = (s or "").strip().lower()
    # Normalize connectors and separators
    s = s.replace("&", " and ")
    s = s.replace("-", " ").replace("_", " ")
    # Remove most punctuation/symbols except spaces and alphanumerics
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

def fetch_coordinates_via_geopy(city: str, state: str | None = None):
    """
    Use geopy (Nominatim) to fetch (lat, lon) for a city string.
    Returns a (lat, lon) tuple or None. Strict mode: India-only and accept only exact city/town names
    (after applying alias normalization), to avoid partial/fuzzy matches.
    """
    if not city or not _geopy_available or _GEOLocator is None:
        return None
    try:
        expected_key = _normalize_for_compare(normalize_city_name(city))
        # Attempt 1: free text (include state if available)
        query = f"{city}, {state}, India" if state else f"{city}, India"
        location = _GEOLocator.geocode(
            query,
            exactly_one=True,
            timeout=10,
            country_codes='in',
            addressdetails=True,
            namedetails=True,
        )
        # Attempt 2: structured
        if not location:
            structured_query = {"city": city, "country": "India"}
            if state:
                structured_query["state"] = state
            location = _GEOLocator.geocode(
                structured_query,
                exactly_one=True,
                timeout=10,
                addressdetails=True,
                namedetails=True,
            )

        if location:
            raw = getattr(location, 'raw', {}) or {}
            address = raw.get('address') or {}
            country_code = (address.get('country_code') or '').lower()
            place_type = (raw.get('type') or '').lower()

            # Strict: India and only suitable place types
            # Include village-level to support smaller towns like Katra; keep checks tight via exact-name + state
            ALLOWED_TYPES = {
                'city', 'town', 'municipality', 'census_town', 'nagar_panchayat',
                'village', 'suburb', 'locality', 'hamlet'
            }
            if country_code != 'in' or place_type not in ALLOWED_TYPES:
                return None

            candidates = [
                raw.get('name') or '',
                address.get('city') or '',
                address.get('town') or '',
                address.get('village') or '',
                address.get('suburb') or '',
                address.get('locality') or '',
            ]
            # Compare after alias normalization
            cand_keys = {_normalize_for_compare(normalize_city_name(n)) for n in candidates if n}
            if expected_key not in cand_keys:
                return None

            # If state context provided, ensure match on state-like fields
            if state:
                state_norm = _normalize_for_compare(state)
                state_candidates = [
                    address.get('state') or '',
                    address.get('state_district') or '',
                    address.get('region') or '',
                ]
                state_keys = {_normalize_for_compare(s) for s in state_candidates if s}
                # Accept if any state key equals or contains the provided state (or vice versa)
                if state_norm:
                    if not any((state_norm == k) or (state_norm in k) or (k in state_norm) for k in state_keys):
                        return None

            return (round(location.latitude, 6), round(location.longitude, 6))
    except Exception:
        return None
    return None

def _sanitize_key(key: str) -> str:
    """
    Make a safe dict-key string for appending to the source file.
    Keep lowercase, replace spaces with single space, and allow letters, numbers, hyphen, underscore.
    """
    if not key:
        return ""
    k = key.strip().lower()
    # replace multiple spaces with single dash for consistency
    k = re.sub(r"\s+", " ", k)
    # allow only letters, numbers, space, hyphen and underscore — then replace spaces with hyphen
    k = re.sub(r"[^a-z0-9 _-]", "", k)
    k = k.replace(" ", "-")
    return k

def _append_city_to_this_script(city_key: str, coord: tuple):
    """
    Append an assignment line to this script to persist the new city into CITY_COORDINATES.
    Example appended lines:
    # added by geopy on 2025-09-20
    CITY_COORDINATES['shimla'] = (31.1048, 77.1734)
    """
    try:
        script_path = os.path.realpath(__file__)
        # double-check file is writable
        if not os.access(script_path, os.W_OK):
            return False
        lat, lon = float(coord[0]), float(coord[1])
        # we append at the end of file
        with open(script_path, "a", encoding="utf-8") as f:
            f.write("\n\n# ---- added by geopy fallback ----\n")
            f.write(f"# city: {city_key}\n")
            f.write(f"CITY_COORDINATES[{repr(city_key)}] = ({lat:.6f}, {lon:.6f})\n")
        return True
    except Exception:
        return False

def get_coordinates(city: str, state: str | None = None):
    """
    Return (lat, lon) for a city from CITY_COORDINATES if present,
    otherwise try geopy and append the result to this script for future runs.
    """
    if not city:
        return None

    city_norm = normalize_city_name(city)
    # direct lookup first
    coord = CITY_COORDINATES.get(city_norm)
    if coord:
        return coord

    # try fetching via geopy using the original input (helps when user passes "Shimla" vs "shimla")
    fetched = fetch_coordinates_via_geopy(city, state=state)
    if not fetched:
        # last attempt with normalized form
        fetched = fetch_coordinates_via_geopy(city_norm, state=state)

    if fetched:
        # normalize key to use for dictionary storage (sanitized)
        safe_key = _sanitize_key(city_norm)
        if not safe_key:
            safe_key = city_norm  # fallback
        # save in-memory for current run
        CITY_COORDINATES[safe_key] = fetched
        # append to source file so future runs have it
        _append_city_to_this_script(safe_key, fetched)
        return fetched

    return None

# -------------------------
# Haversine formula and helpers
# -------------------------
def get_distance(city1: str, city2: str) -> float:
    """
    Get distance between two cities in kilometers using Haversine formula.
    Returns 0 if cities are the same, or 1000.0 if a city is not found.
    """
    if not city1 or not city2:
        return float('inf')

    city1_norm = normalize_city_name(city1)
    city2_norm = normalize_city_name(city2)

    if city1_norm == city2_norm:
        return 0.0

    coord1 = get_coordinates(city1)
    coord2 = get_coordinates(city2)

    if not coord1 or not coord2:
        return 1000.0

    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    R = 6371  # Earth radius in km
    return round(R * c, 1)

def get_nearby_cities(city: str, max_distance: float = 100.0) -> list:
    """
    Get list of cities within max_distance km of the given city.
    """
    if not city:
        return []
    city_norm = normalize_city_name(city)
    if city_norm not in CITY_COORDINATES:
        # try to fetch coordinates to allow nearby search for unknown city
        coord = get_coordinates(city)
        if not coord:
            return []
    nearby = []
    for other_city, coord in CITY_COORDINATES.items():
        if other_city == city_norm:
            continue
        dist = get_distance(city_norm, other_city)
        if dist <= max_distance:
            nearby.append((other_city, dist))
    return sorted(nearby, key=lambda x: x[1])

# -------------------------
# Run examples when executed directly
# -------------------------
if __name__ == "__main__":
    print("Distance examples (may fall back to geopy if needed):")
    print("delhi -> agra:", get_distance("delhi", "agra"))              # both in hardcoded
    print("delhi -> shimla:", get_distance("delhi", "shimla"))          # shimla likely fetched via geopy and appended
    print("mumbai -> pune:", get_distance("mumbai", "pune"))            # both in hardcoded
    print("unknowncity -> unknowncity2:", get_distance("foo", "bar"))   # both missing, returns 1000.0
    print("Nearby cities around 'pune' within 150 km:", get_nearby_cities("pune", 150))



# ---- added by geopy fallback ----
# city: cuttack
CITY_COORDINATES['cuttack'] = (20.468600, 85.879200)


# ---- added by geopy fallback ----
# city: leh
CITY_COORDINATES['leh'] = (34.164203, 77.584813)


# ---- added by geopy fallback ----
# city: kharar
CITY_COORDINATES['kharar'] = (30.748844, 76.642899)
