# backend/ml_model.py
import json
import os
from rapidfuzz import fuzz
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import difflib

_geolocator = Nominatim(user_agent="internship_locator")

# ----------------- City Helpers -----------------
def _normalize_city(name: str) -> str:
    return (name or "").strip().lower()

def _get_coordinates(city_name: str):
    """Geocode a city name into (lat, lon)."""
    if not city_name:
        return None
    try:
        loc = _geolocator.geocode(city_name)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception as e:
        print(f"Geocoding error for {city_name}: {e}")
        return None
    return None

def find_nearest_city(input_city: str, cities: list[dict]):
    """
    Given input city string and list of cities from internships.json,
    return the best matching city (string match or geodesic nearest).
    """
    print(f"🔍 Finding nearest city for: '{input_city}'")
    db_city_names = [c.get("name") for c in cities if c.get("name")]

    if not db_city_names:
        return None, None

    # --- Step 1: Exact/Fuzzy match ---
    input_norm = _normalize_city(input_city)
    norm_db = [_normalize_city(c) for c in db_city_names]

    # Try exact
    if input_norm in norm_db:
        idx = norm_db.index(input_norm)
        return db_city_names[idx], 0.0

    # Try fuzzy (difflib, cutoff=0.8)
    match = difflib.get_close_matches(input_norm, norm_db, n=1, cutoff=0.8)
    if match:
        idx = norm_db.index(match[0])
        return db_city_names[idx], 0.0

    # --- Step 2: Distance-based ---
    input_coords = _get_coordinates(input_city)
    if not input_coords:
        return None, None

    nearest_city = None
    min_dist = float("inf")

    for city in db_city_names:
        coords = _get_coordinates(city)
        if not coords:
            continue
        try:
            dist = geodesic(input_coords, coords).km
            if dist < min_dist:
                min_dist = dist
                nearest_city = city
        except Exception as e:
            print(f"❌ Error calculating distance to {city}: {e}")
            continue

    if nearest_city:
        return nearest_city, round(min_dist, 2)
    return None, None

# ----------------- Skill Helpers -----------------
def _load_synonyms():
    base_dir = os.path.dirname(os.path.dirname(__file__))  # go up from backend/
    path = os.path.join(base_dir, "data", "skills_synonyms.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_SKILL_SYNONYMS = _load_synonyms()

def _normalize_skill(skill: str) -> str:
    """Lowercase, strip, and map synonyms."""
    if not isinstance(skill, str):
        return ""
    s = skill.strip().lower()
    return _SKILL_SYNONYMS.get(s, s)

def _normalize_skill_list(skills):
    """Return a list of cleaned, lowercase skill strings (unique, ordered)."""
    if not skills:
        return []
    seen = set()
    out = []
    for s in skills:
        norm = _normalize_skill(s)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out

# ----------------- Recommendations -----------------
def get_recommendations(candidate, internships, top_n: int = 10):
    """
    Recommendation scoring system:
    - Skills matched = +2 each
    - Rare skill bonus = +1
    - Sector match = +3
    - Location match = +2 (exact) or +1 (within 50km)
    - Field of study relevance = +1
    """

    recommendations = []
    candidate_skills = _normalize_skill_list(candidate.get("skills_possessed", []))
    candidate_skill_set = set(candidate_skills)

    sector_interests = [s.lower() for s in candidate.get("sector_interests", [])]
    location_pref = (candidate.get("location_preference") or "").strip().lower()
    field_of_study = (candidate.get("field_of_study") or "").strip().lower()

    # 🔹 Pre-calc skill frequencies
    skill_freq = {}
    total_internships = len(internships or [])
    for internship in internships or []:
        for s in _normalize_skill_list(internship.get("skills_required", [])):
            skill_freq[s] = skill_freq.get(s, 0) + 1

    # 🔹 Candidate coords
    candidate_coords = None
    if location_pref:
        candidate_coords = _get_coordinates(location_pref)

    for internship in internships or []:
        internship_id = internship.get("internship_id") or internship.get("id") or None
        title = internship.get("title", "")
        organization = internship.get("organization", "")
        location = (internship.get("location", "")).strip().lower()
        sector = (internship.get("sector", "")).strip().lower()
        internship_skills = _normalize_skill_list(internship.get("skills_required", []))
        internship_skills_set = set(internship_skills)

        # --- Skill Matching (with fuzzy) ---
        matched = []
        for cand_skill in candidate_skill_set:
            if cand_skill in internship_skills_set:
                matched.append(cand_skill)
            else:
                if any(fuzz.ratio(cand_skill, s) >= 80 for s in internship_skills_set):
                    matched.append(cand_skill)

        # --- Score ---
        score = 0
        score += 2 * len(matched)

        for skill in matched:
            freq = skill_freq.get(skill, 1)
            rarity = (total_internships / freq)
            if rarity > 5:
                score += 1

        if sector in sector_interests:
            score += 3

        if location and location_pref:
            if location == location_pref:
                score += 2
            elif candidate_coords:
                internship_coords = _get_coordinates(location)
                if internship_coords:
                    try:
                        distance = geodesic(candidate_coords, internship_coords).km
                        if distance <= 50:
                            score += 1
                    except Exception:
                        pass

        if field_of_study and field_of_study in sector:
            score += 1

        recommendations.append({
            "internship_id": internship_id,
            "title": title,
            "organization": organization,
            "location": internship.get("location", ""),
            "sector": internship.get("sector", ""),
            "match_score": score,
            "matched_skills": matched
        })

    recommendations.sort(key=lambda x: (-x["match_score"], str(x.get("internship_id") or "")))
    return recommendations[:top_n]