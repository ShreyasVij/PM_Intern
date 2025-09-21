# backend/distance_matrix.py
"""
Distance calculation using a static hardcoded city coordinates dictionary.
This module imports CITY_COORDINATES from backend.city_coords.
"""

from backend.city_coords import CITY_COORDINATES

from math import radians, sin, cos, sqrt, atan2

# Common city name mappings for better matching
CITY_ALIASES = {
	# Must map to keys that exist in CITY_COORDINATES
	"mumbai": ["bombay", "mumbai"],
	"bengaluru": ["bengaluru", "bangalore", "blr"],
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
	"varanasi": ["varanasi", "banaras", "benares", "benaras"],
	"rajkot": ["rajkot"],
	"vijayawada": ["vijayawada"],
	"madurai": ["madurai"],
	"visakhapatnam": ["visakhapatnam", "vizag"],
	"pondicherry": ["pondicherry", "puducherry"],
	"trivandrum": ["trivandrum", "thiruvananthapuram"],
	"prayagraj": ["prayagraj", "allahabad"],
	"gurgaon": ["gurgaon", "gurugram"],
	"navi mumbai": ["navi mumbai", "navimumbai"],
	"pimpri-chinchwad": ["pimpri-chinchwad", "pimpri chinchwad"],
	"kalyan-dombivli": ["kalyan-dombivli", "kalyan dombivli"],
}

def _basic_normalize(city: str) -> str:
    if not city:
        return ""
    s = city.strip().lower()
    # collapse runs of spaces and remove leading/trailing punctuation-like chars
    s = " ".join(s.split())
    return s

def normalize_city_name(city: str) -> str:
	"""
	Normalize city name to standard form for distance lookup.
	"""
	if not city:
		return ""
	city_lower = _basic_normalize(city)
	for standard_name, aliases in CITY_ALIASES.items():
		if city_lower in aliases:
			return standard_name
	return city_lower

def get_distance(city1: str, city2: str) -> float:
	"""
	Get distance between two cities in kilometers using Haversine formula.
	Returns 0 if cities are the same, or a large number if city not found.
	"""
	if not city1 or not city2:
		return float('inf')
	city1_norm = normalize_city_name(city1)
	city2_norm = normalize_city_name(city2)
	if city1_norm == city2_norm:
		return 0.0
	coord1 = CITY_COORDINATES.get(city1_norm)
	coord2 = CITY_COORDINATES.get(city2_norm)
	if not coord1 or not coord2:
		return 1000.0
	# Haversine formula
	lat1, lon1 = radians(coord1[0]), radians(coord1[1])
	lat2, lon2 = radians(coord2[0]), radians(coord2[1])
	dlat = lat2 - lat1
	dlon = lon2 - lon1
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * atan2(sqrt(a), sqrt(1-a))
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
		return []
	nearby = []
	for other_city, coord in CITY_COORDINATES.items():
		if other_city == city_norm:
			continue
		dist = get_distance(city_norm, other_city)
		if dist <= max_distance:
			nearby.append((other_city, dist))
	return sorted(nearby, key=lambda x: x[1])
