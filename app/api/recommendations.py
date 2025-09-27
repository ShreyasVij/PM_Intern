# app/api/recommendations.py
"""
Recommendations API endpoints
Direct implementation to replace legacy imports
"""

from flask import jsonify
from app.core.database import db_manager
from app.utils.logger import app_logger
from app.utils.response_helpers import success_response, error_response
try:
    # Prefer the improved ML logic
    from backend.ml_model import get_recommendations as ml_get_recommendations
except Exception as _e:
    ml_get_recommendations = None
    app_logger.error(f"Failed to import ML recommender: {__name__}: {_e}")

def get_candidate_recommendations(candidate_id):
    """Get recommendations for a specific candidate"""
    try:
        # Load candidate profile
        candidate = load_candidate_by_id(candidate_id)
        if not candidate:
            return error_response("Candidate not found", 404)
        
        # Load internships
        internships = load_all_internships()
        if not internships:
            return error_response("No internships available", 404)
        
        # Generate recommendations using improved ML logic
        recommendations = []
        if ml_get_recommendations is not None:
            ml_recs = ml_get_recommendations(candidate, internships, top_n=10)
            # Enrich with skills/description for UI compatibility
            by_id = {i.get("internship_id"): i for i in internships}
            for r in ml_recs:
                base = by_id.get(r.get("internship_id"), {})
                enriched = {
                    **r,
                    "skills_required": base.get("skills_required", r.get("skills_required", [])),
                    "description": base.get("description", r.get("description", "")),
                }
                recommendations.append(enriched)
        else:
            # Fallback to simple overlap if ML import failed
            recommendations = generate_recommendations(candidate, internships)
        
        return success_response({
            "candidate": candidate.get("name"),
            "candidate_id": candidate.get("candidate_id"),
            "recommendations": recommendations
        })
        
    except Exception as e:
        app_logger.error(f"Error generating recommendations for {candidate_id}: {e}")
        return error_response("Failed to generate recommendations", 500)


def get_internship_recommendations(internship_id):
    """Get similar internships for a given internship"""
    try:
        # Load all internships
        internships = load_all_internships()
        if not internships:
            return error_response("No internships available", 404)
        
        # Find the base internship
        base_internship = next((i for i in internships if i.get("internship_id") == internship_id), None)
        if not base_internship:
            return error_response("Internship not found", 404)
        
        # Generate similar internship recommendations using ML by creating a pseudo-candidate
        recommendations = []
        if ml_get_recommendations is not None:
            pseudo_candidate = {
                "skills_possessed": base_internship.get("skills_required", []),
                "sector_interests": [str(base_internship.get("sector", "")).lower()] if base_internship.get("sector") else [],
                "location_preference": base_internship.get("location", ""),
                # keep other fields empty; ML handles missing gracefully
            }
            pool = [i for i in internships if i.get("internship_id") != internship_id]
            # Slightly tilt weights towards skill/sector for "similarity" use-case
            ml_recs = ml_get_recommendations(
                pseudo_candidate,
                pool,
                top_n=10,
                skill_weight=0.6,
                loc_weight=0.15,
                sector_weight=0.2,
                misc_weight=0.05,
            )
            # Enrich with skills/description for UI compatibility
            by_id = {i.get("internship_id"): i for i in pool}
            for r in ml_recs:
                base = by_id.get(r.get("internship_id"), {})
                recommendations.append({
                    **r,
                    "skills_required": base.get("skills_required", r.get("skills_required", [])),
                    "description": base.get("description", r.get("description", "")),
                })
        else:
            recommendations = generate_similar_internships(base_internship, internships)
        
        return success_response({
            "base_internship": base_internship.get("title"),
            "recommendations": recommendations
        })
        
    except Exception as e:
        app_logger.error(f"Error generating internship recommendations for {internship_id}: {e}")
        return error_response("Failed to generate recommendations", 500)


def load_candidate_by_id(candidate_id):
    """Load candidate profile by ID"""
    try:
        # Try MongoDB first
        db = db_manager.get_db()
        if db is not None:
            try:
                candidate = db.profiles.find_one({"candidate_id": candidate_id})
                if candidate:
                    if '_id' in candidate:
                        candidate['_id'] = str(candidate['_id'])
                    return candidate
            except Exception as e:
                app_logger.warning(f"MongoDB query failed: {e}")
        
        # Strict Atlas mode: do not read JSON files
        return None
    except Exception as e:
        app_logger.error(f"Error loading candidate {candidate_id}: {e}")
        return None


def load_all_internships():
    """Load all internships"""
    try:
        # Try MongoDB first
        db = db_manager.get_db()
        if db is not None:
            try:
                internships = list(db.internships.find({}))
                # Convert ObjectId to string for JSON serialization
                for internship in internships:
                    if '_id' in internship:
                        internship['_id'] = str(internship['_id'])
                return internships
            except Exception as e:
                app_logger.warning(f"MongoDB query failed: {e}")
        
        # Strict Atlas mode: do not read JSON files
        return []
    except Exception as e:
        app_logger.error(f"Error loading internships: {e}")
        return []


def generate_recommendations(candidate, internships):
    """Generate recommendations for a candidate"""
    try:
        recommendations = []
        candidate_skills = set([s.strip().lower() for s in candidate.get("skills_possessed", []) if isinstance(s, str)])
        
        for internship in internships:
            internship_skills = set([s.strip().lower() for s in internship.get("skills_required", []) if isinstance(s, str)])
            common_skills = candidate_skills & internship_skills
            
            # Calculate match score as percentage (0-100)
            if len(internship_skills) > 0:
                match_score = (len(common_skills) / len(internship_skills)) * 100
            else:
                match_score = 0
            
            # Only include internships with some match
            if match_score > 0:
                recommendations.append({
                    "internship_id": internship.get("internship_id"),
                    "title": internship.get("title"),
                    "organization": internship.get("organization"),
                    "location": internship.get("location"),
                    "sector": internship.get("sector"),
                    "skills_required": internship.get("skills_required", []),
                    "description": internship.get("description", ""),
                    "match_score": round(match_score, 2)
                })
        
        # Sort by match score in descending order
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return recommendations[:10]  # Top 10 matches
        
    except Exception as e:
        app_logger.error(f"Error generating recommendations: {e}")
        return []


def generate_similar_internships(base_internship, internships):
    """Generate similar internship recommendations"""
    try:
        base_skills = set([s.strip().lower() for s in base_internship.get("skills_required", []) if isinstance(s, str)])
        recommendations = []
        
        for internship in internships:
            if internship.get("internship_id") == base_internship.get("internship_id"):
                continue
                
            intern_skills = set([s.strip().lower() for s in internship.get("skills_required", []) if isinstance(s, str)])
            common_skills = base_skills & intern_skills
            
            # Calculate match score as percentage of base internship skills (0-100)
            match_score = (len(common_skills) / len(base_skills) * 100) if base_skills else 0
            
            if match_score > 0:
                recommendations.append({
                    "internship_id": internship.get("internship_id"),
                    "title": internship.get("title"),
                    "organization": internship.get("organization"),
                    "location": internship.get("location"),
                    "sector": internship.get("sector"),
                    "skills_required": internship.get("skills_required", []),
                    "description": internship.get("description", "")[:200] + "..." if len(internship.get("description", "")) > 200 else internship.get("description", ""),
                    "match_score": round(match_score, 2)
                })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return recommendations[:10]  # Top 10 matches
        
    except Exception as e:
        app_logger.error(f"Error generating similar internships: {e}")
        return []