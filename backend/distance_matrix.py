# backend/distance_matrix.py
"""
Distance matrix for top 30 Indian cities using latitude/longitude and Haversine formula.
"""

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

from math import radians, sin, cos, sqrt, atan2

# Common city name mappings for better matching
CITY_ALIASES = {
	"mumbai": ["bombay", "mumbai"],
	"bangalore": ["bengaluru", "bangalore"],
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
