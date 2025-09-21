# backend/ml_model.py
from rapidfuzz import fuzz
import difflib
try:
    from .distance_matrix import get_distance, normalize_city_name
except ImportError:
    from distance_matrix import get_distance, normalize_city_name

# ----------------- City Helpers -----------------
def _normalize_city(name: str) -> str:
    return (name or "").strip().lower()

def _get_distance_between_cities(city1: str, city2: str) -> float:
    """Get distance between two cities using hardcoded distance matrix."""
    if not city1 or not city2:
        return float('inf')
    
    # Normalize city names
    city1_norm = normalize_city_name(city1)
    city2_norm = normalize_city_name(city2)
    
    return get_distance(city1_norm, city2_norm)

def find_nearest_city(input_city: str, cities: list[dict]):
    """
    Given input city string and list of cities from internships.json,
    return the best matching city (string match or distance-based nearest).
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

    # --- Step 2: Distance-based using hardcoded distances ---
    nearest_city = None
    min_dist = float("inf")

    for city in db_city_names:
        try:
            dist = _get_distance_between_cities(input_city, city)
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
    """Load skill synonyms strictly from MongoDB (Atlas). No JSON fallback."""
    try:
        from backend.db import load_data
        syn_rows = load_data('skills_synonyms') or []
        mapping = {}
        for row in syn_rows:
            alias = str(row.get('alias', '')).strip().lower()
            canonical = str(row.get('canonical', '')).strip().lower()
            if alias and canonical:
                mapping[alias] = canonical
        return mapping
    except Exception as e:
        print(f"[ERROR] DB load for skills_synonyms failed: {e}")
        return {}

_SKILL_SYNONYMS = _load_synonyms()

def _normalize_skill(skill: str) -> str:
    """Lowercase, strip, and map synonyms."""
    if not isinstance(skill, str):
        print(f"[DEBUG] Non-string skill passed to _normalize_skill: {repr(skill)} (type: {type(skill)})")
        return ""
    s = skill.strip().lower()
    return _SKILL_SYNONYMS.get(s, s)

def _normalize_skill_list(skills):
    """Return a list of cleaned, lowercase skill strings (unique, ordered)."""
    if not skills:
        return []
    # Deeply flatten skills (arbitrary depth)
    def _deep_flatten(sk):
        if isinstance(sk, list):
            out = []
            for item in sk:
                out.extend(_deep_flatten(item))
            return out
        elif isinstance(sk, str):
            return [sk]
        else:
            return []
    flat_skills = _deep_flatten(skills)
    seen = set()
    out = []
    for s in flat_skills:
        if not isinstance(s, str):
            print(f"[DEBUG] Non-string skill found in skills_possessed: {repr(s)} (type: {type(s)})")
            continue
        norm = _normalize_skill(s)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out

# ----------------- Recommendations -----------------
def get_recommendations(candidate, internships, top_n: int = 10):
    """
    Modern scoring system:
    - Skills matched: up to 50 points (proportional to % matched)
    - Location proximity: up to 25 points (same city: 25, ≤50km: 20, ≤200km: 10, else 0)
    - Sector match: 15 points
    - Field of study: 5 points
    - Education level: 5 points
    Max score: 100
    """

    recommendations = []
    candidate_skills = _normalize_skill_list(candidate.get("skills_possessed", []))
    candidate_skill_set = set(candidate_skills)
    sector_interests = [s.lower() for s in candidate.get("sector_interests", [])]
    location_pref = (candidate.get("location_preference") or "").strip().lower()
    field_of_study = (candidate.get("field_of_study") or "").strip().lower()
    education_level = (candidate.get("education_level") or "").strip().lower()

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

        # --- New Scoring System ---
        score = 0

        # Skill match: up to 50 points
        skill_score = 0
        if internship_skills:
            skill_score = (len(matched) / len(internship_skills)) * 50
        score += skill_score

        # Location proximity: up to 25 points
        loc_score = 0
        if location and location_pref:
            if location == location_pref:
                loc_score = 25
            else:
                try:
                    distance = _get_distance_between_cities(location_pref, location)
                    if distance <= 50:
                        loc_score = 20
                    elif distance <= 200:
                        loc_score = 10
                except Exception:
                    pass
        score += loc_score

        # Sector match: 15 points
        sector_score = 15 if sector in sector_interests else 0
        score += sector_score

        # Field of study: 5 points
        field_score = 5 if field_of_study and field_of_study in sector else 0
        score += field_score

        # Education level: 5 points
        edu_score = 5 if education_level and education_level in title.lower() else 0
        score += edu_score

        match_percentage = min(100, max(0, round(score, 1)))
        recommendations.append({
            "internship_id": internship_id,
            "title": title,
            "organization": organization,
            "location": internship.get("location", ""),
            "sector": internship.get("sector", ""),
            "match_score": match_percentage,
            "matched_skills": matched
        })

    recommendations.sort(key=lambda x: (-x["match_score"], str(x.get("internship_id") or "")))
    return recommendations[:top_n]