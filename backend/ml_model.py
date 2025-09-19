# backend/ml_model.py
import json
import os
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
    Enhanced recommendation scoring system:
    - Skills matched = +3 each (increased from +2)
    - Rare skill bonus = +2 (increased from +1)
    - Sector match = +4 (increased from +3)
    - Location match = +3 (exact) or +2 (within 50km) or +1 (within 200km)
    - Field of study relevance = +2 (increased from +1)
    - Education level bonus = +1 (for matching education requirements)
    - Skill diversity bonus = +1 (for internships requiring diverse skills)
    """

    recommendations = []
    candidate_skills = _normalize_skill_list(candidate.get("skills_possessed", []))
    candidate_skill_set = set(candidate_skills)

    sector_interests = [s.lower() for s in candidate.get("sector_interests", [])]
    location_pref = (candidate.get("location_preference") or "").strip().lower()
    field_of_study = (candidate.get("field_of_study") or "").strip().lower()
    education_level = (candidate.get("education_level") or "").strip().lower()

    # 🔹 Pre-calc skill frequencies for rarity scoring
    skill_freq = {}
    total_internships = len(internships or [])
    for internship in internships or []:
        for s in _normalize_skill_list(internship.get("skills_required", [])):
            skill_freq[s] = skill_freq.get(s, 0) + 1

    # 🔹 Candidate location for distance calculations
    candidate_location = location_pref

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

        # --- Enhanced Scoring System ---
        score = 0
        
        # Base skill matching (increased weight)
        score += 3 * len(matched)

        # Rare skill bonus (increased weight)
        for skill in matched:
            freq = skill_freq.get(skill, 1)
            rarity = (total_internships / freq)
            if rarity > 5:
                score += 2  # Increased from 1

        # Sector interest matching (increased weight)
        if sector in sector_interests:
            score += 4  # Increased from 3

        # Location matching (enhanced with distance tiers)
        if location and location_pref:
            if location.lower() == location_pref.lower():
                score += 3  # Increased from 2
            else:
                try:
                    distance = _get_distance_between_cities(location_pref, location)
                    if distance <= 50:
                        score += 2  # Increased from 1
                    elif distance <= 200:
                        score += 1  # New tier for nearby cities
                except Exception:
                    pass

        # Field of study relevance (increased weight)
        if field_of_study and field_of_study in sector:
            score += 2  # Increased from 1

        # Education level bonus (new)
        if education_level and education_level in title.lower():
            score += 1

        # Skill diversity bonus (new)
        internship_skills_count = len(internship_skills)
        if internship_skills_count >= 5:  # Diverse skill requirements
            score += 1

        # Convert score to percentage (0-100)
        # Normalize score to percentage based on maximum possible score
        max_possible_score = 20  # Approximate maximum score for normalization
        match_percentage = min(100, max(0, (score / max_possible_score) * 100))
        
        recommendations.append({
            "internship_id": internship_id,
            "title": title,
            "organization": organization,
            "location": internship.get("location", ""),
            "sector": internship.get("sector", ""),
            "match_score": match_percentage,  # Now a percentage
            "matched_skills": matched
        })

    recommendations.sort(key=lambda x: (-x["match_score"], str(x.get("internship_id") or "")))
    return recommendations[:top_n]