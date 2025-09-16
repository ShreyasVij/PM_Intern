# backend/ml_model.py

def _normalize_skill_list(skills):
    """Return a list of cleaned, lowercase skill strings (preserve order, unique)."""
    if not skills:
        return []
    seen = set()
    out = []
    for s in skills:
        if not isinstance(s, str):
            continue
        s2 = s.strip().lower()
        if s2 and s2 not in seen:
            seen.add(s2)
            out.append(s2)
    return out


def get_recommendations(candidate, internships, top_n: int = 5):
    """
    Simple recommendation: count normalized skill overlap between candidate and each internship.

    Returns a list of recommendation dicts with fields:
      - internship_id, title, organization, location, sector, match_score, matched_skills (list)

    This function is intentionally defensive: it normalizes strings and handles missing keys.
    """
    recommendations = []

    # normalize candidate skills
    candidate_skills = set(_normalize_skill_list(candidate.get("skills_possessed", [])))

    for internship in internships or []:
        # defensive fetch of internship fields
        internship_id = internship.get("internship_id") or internship.get("id") or None
        title = internship.get("title", "")
        organization = internship.get("organization", "")
        location = internship.get("location", "")
        sector = internship.get("sector", "")

        internship_skills = _normalize_skill_list(internship.get("skills_required", []))
        internship_skills_set = set(internship_skills)

        # compute overlap
        matched = sorted(list(candidate_skills.intersection(internship_skills_set)))
        score = len(matched)

        recommendations.append({
            "internship_id": internship_id,
            "title": title,
            "organization": organization,
            "location": location,
            "sector": sector,
            "match_score": score,
            "matched_skills": matched,   # helpful for UI; frontend can ignore if not used
        })

    # sort by score desc, then by internship_id to have deterministic output
    recommendations.sort(key=lambda x: (-x["match_score"], str(x.get("internship_id") or "")))

    return recommendations[:top_n]
