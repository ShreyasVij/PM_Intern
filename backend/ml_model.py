# backend/ml_model.py
import json
import os
from rapidfuzz import fuzz

# 🔹 Load synonyms from data/ folder
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
    """Return a list of cleaned, lowercase skill strings (preserve order, unique)."""
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

def get_recommendations(candidate, internships, top_n: int = 10):
    """
    Recommendation scoring system:
    - Skills matched = +2 each
    - Rare skill bonus = +1
    - Sector match = +3
    - Location match = +2
    - Field of study relevance = +1
    """

    recommendations = []
    candidate_skills = _normalize_skill_list(candidate.get("skills_possessed", []))
    candidate_skill_set = set(candidate_skills)

    sector_interests = [s.lower() for s in candidate.get("sector_interests", [])]
    location_pref = (candidate.get("location_preference") or "").strip().lower()
    field_of_study = (candidate.get("field_of_study") or "").strip().lower()

    # 🔹 Pre-calc skill frequencies across all internships
    skill_freq = {}
    total_internships = len(internships or [])
    for internship in internships or []:
        for s in _normalize_skill_list(internship.get("skills_required", [])):
            skill_freq[s] = skill_freq.get(s, 0) + 1

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

        # --- Score Calculation ---
        score = 0

        # Skill overlap (2 points each)
        score += 2 * len(matched)

        # Rare skill bonus (+1 if uncommon across internships)
        for skill in matched:
            freq = skill_freq.get(skill, 1)
            rarity = (total_internships / freq)
            if rarity > 5:
                score += 1

        # Sector match (+3)
        if sector in sector_interests:
            score += 3

        # Location match (+2)
        if location and location == location_pref:
            score += 2

        # Education/field relevance (+1 if field in sector string)
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

    # Sort by score desc, then ID for deterministic order
    recommendations.sort(key=lambda x: (-x["match_score"], str(x.get("internship_id") or "")))

    return recommendations[:top_n]
