# backend/ml_model.py
from rapidfuzz import fuzz
import difflib
import math
import re

# ----------------- distance imports (robust) -----------------
try:
    from .distance_matrix import get_distance, normalize_city_name
except Exception:
    try:
        from distance_matrix import get_distance, normalize_city_name
    except Exception:
        # If distance_matrix missing, provide safe fallbacks
        def normalize_city_name(x):
            return (x or "").strip().lower()

        def get_distance(a, b):
            # fallback: unknown distance
            return float('inf')

# ----------------- City Helpers (kept from original) -----------------
def _normalize_city(name: str) -> str:
    return (name or "").strip().lower()

def _get_distance_between_cities(city1: str, city2: str) -> float:
    """Get distance between two cities using hardcoded distance matrix (via get_distance)."""
    if not city1 or not city2:
        return float('inf')

    # Normalize city names using provided helper
    city1_norm = normalize_city_name(city1)
    city2_norm = normalize_city_name(city2)

    try:
        return get_distance(city1_norm, city2_norm)
    except Exception:
        return float('inf')

def find_nearest_city(input_city: str, cities: list[dict]):
    """
    Given input city string and list of cities from internships.json,
    return the best matching city (string match or distance-based nearest).
    Returns (city_name_or_None, distance_or_None)
    """
    print(f"Finding nearest city for: '{input_city}'")
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

# ----------------- Skill Helpers (from your original file) -----------------
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

# ----------------- New similarity helpers (improved) -----------------
def _tokenize(s: str):
    if not s:
        return set()
    tokens = [t for t in re.split(r'[^a-z0-9]+', s.lower()) if len(t) > 1]
    return set(tokens)

def _jaccard(a_tokens: set, b_tokens: set):
    if not a_tokens or not b_tokens:
        return 0.0
    inter = a_tokens & b_tokens
    uni = a_tokens | b_tokens
    return len(inter) / len(uni)

def skill_similarity(candidate_skills, internship_skills, fuzzy_threshold=85):
    """
    Returns a normalized score 0..1 combining:
     - exact/synonym matches (primary)
     - token overlap (Jaccard on skill phrases)
     - fuzzy matches on skill strings
    """
    if not internship_skills:
        return 0.0
    # candidate_skills expected as iterable of normalized strings
    cand = list(candidate_skills)
    intern = list(internship_skills)
    matched = set()

    # exact / synonyms
    for cs in cand:
        if cs in intern:
            matched.add(cs)

    # fuzzy + token overlap for remaining
    for cs in cand:
        if cs in matched:
            continue
        # fuzzy against any internship skill
        if any(fuzz.partial_ratio(cs, s) >= fuzzy_threshold for s in intern):
            matched.add(cs)
            continue
        # token overlap with any internship skill
        cs_tokens = _tokenize(cs)
        if any(_jaccard(cs_tokens, _tokenize(s)) >= 0.5 for s in intern):
            matched.add(cs)

    coverage = min(1.0, len(matched) / max(1, len(intern)))
    return coverage

def location_similarity(candidate_loc, intern_loc):
    """
    Return (score 0..1, distance_km or None, reason_str)
    Tiering: same city -> 1.0, <=50km -> 0.9, <=200km -> 0.6, else 0.0
    """
    if not candidate_loc or not intern_loc:
        return 0.0, None, "no location info"
    try:
        c_norm = normalize_city_name(candidate_loc)
        i_norm = normalize_city_name(intern_loc)
    except Exception:
        c_norm = (candidate_loc or "").strip().lower()
        i_norm = (intern_loc or "").strip().lower()

    if c_norm == i_norm:
        return 1.0, 0.0, "same city"

    try:
        dist = get_distance(c_norm, i_norm)
        if dist is None:
            dist = float('inf')
    except Exception:
        dist = float('inf')

    if dist <= 0:
        return 1.0, 0.0, "same place"
    if dist <= 50:
        return 0.9, dist, f"{int(dist)} km away"
    if dist <= 200:
        return 0.6, dist, f"{int(dist)} km away"
    return 0.0, dist if math.isfinite(dist) else None, f"{int(dist)} km away" if math.isfinite(dist) else "far"

# ----------------- Recommendations (keeps the original function name) -----------------
def get_recommendations(candidate, internships, top_n=10,
                        skill_weight=0.5, loc_weight=0.25,
                        sector_weight=0.15, misc_weight=0.10):
    """
    Lightweight, explainable recommendation function that is compatible with
    existing callers in your codebase.
    Returns a list of up to top_n internship dicts with match_score and reason.
    """
    cand_skills = _normalize_skill_list(candidate.get("skills_possessed", []))
    cand_skill_set = set(cand_skills)
    sector_interests = [s.lower() for s in candidate.get("sector_interests", []) or []]
    location_pref = (candidate.get("location_preference") or "").strip().lower()
    field_of_study = (candidate.get("field_of_study") or "").strip().lower()
    education_level = (candidate.get("education_level") or "").strip().lower()
    is_first_gen = bool(candidate.get("first_generation") or candidate.get("no_experience"))

    scored = []
    for internship in internships or []:
        internship_skills = _normalize_skill_list(internship.get("skills_required", []))

        skill_sim = skill_similarity(cand_skill_set, internship_skills)
        loc_sim, dist_km, loc_reason = location_similarity(location_pref, internship.get("location", ""))
        sector = (internship.get("sector") or "").strip().lower()
        sector_sim = 1.0 if sector in sector_interests else 0.0
        field_sim = 1.0 if field_of_study and field_of_study in sector else 0.0
        edu_sim = 1.0 if education_level and education_level in (internship.get("title") or "").lower() else 0.0
        fg_boost = 0.08 if is_first_gen and internship.get("is_beginner_friendly") else 0.0

        base_score = (
            skill_weight * skill_sim +
            loc_weight * loc_sim +
            sector_weight * sector_sim +
            misc_weight * (0.5 * field_sim + 0.5 * edu_sim)
        )
        score = min(1.0, base_score + fg_boost)
        score_pct = round(score * 100, 1)

        scored.append({
            "internship": internship,
            "score": score_pct,
            "components": {
                "skill_sim": round(skill_sim, 2),
                "loc_sim": round(loc_sim, 2),
                "loc_reason": loc_reason,
                "sector_sim": sector_sim,
                "field_sim": field_sim,
                "edu_sim": edu_sim,
                "fg_boost": fg_boost
            }
        })

    scored.sort(key=lambda x: (-x["score"], x["internship"].get("internship_id") or ""))
    results = []
    seen_orgs = set()
    for item in scored:
        org = (item["internship"].get("organization") or "").strip().lower()
        if org and org in seen_orgs:
            continue
        comps = item["components"]
        reason = []
        if comps["skill_sim"] >= 0.6:
            reason.append(f"Strong skill fit ({int(comps['skill_sim']*100)}%)")
        elif comps["skill_sim"] > 0:
            reason.append(f"Some skill match ({int(comps['skill_sim']*100)}%)")
        if comps["loc_sim"] >= 0.9:
            reason.append("Close to you")
        elif comps["loc_sim"] >= 0.6:
            reason.append("Within reasonable distance")
        if comps["sector_sim"]:
            reason.append("Sector match")
        if comps["fg_boost"]:
            reason.append("Good for beginners")

        results.append({
            "internship_id": item["internship"].get("internship_id") or item["internship"].get("id"),
            "title": item["internship"].get("title"),
            "organization": item["internship"].get("organization"),
            "location": item["internship"].get("location"),
            "sector": item["internship"].get("sector"),
            "match_score": item["score"],
            "reason": ", ".join(reason) if reason else "Relevant",
            "components": comps
        })
        if org:
            seen_orgs.add(org)
        if len(results) >= top_n:
            break

    return results

# compatibility aliases (if other files import old helpers directly)
location_tier_score = location_similarity
_get_distance_between_cities = _get_distance_between_cities
