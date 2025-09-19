# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import load_data, save_data, convert_object_ids

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)                 # backend/
DATA_DIR = os.path.join(BASE_DIR, "..", "data")      # ../data
LOGIN_FILE = os.path.join(DATA_DIR, "login-info.json")

CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.json")
INTERNSHIPS_FILE = os.path.join(DATA_DIR, "internships.json")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")

print(f"🔎 Data folder in use: {DATA_DIR}")  # debug print


# ---------------- Login Info ----------------
def load_login_data():
    return convert_object_ids(load_data("login_info"))


def save_login_data(data):
    save_data("login_info", data)


@app.route("/signup", methods=["POST"])
def signup():
    creds = request.get_json()
    if not creds or "username" not in creds or "password" not in creds:
        return jsonify({"error": "Invalid data"}), 400

    if len(creds["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    users = load_login_data()
    if any(u["username"] == creds["username"] for u in users):
        return jsonify({"error": "User already exists"}), 400

    # Hash the password
    hashed_password = generate_password_hash(creds["password"])
    users.append({"username": creds["username"], "password": hashed_password})
    save_login_data(users)
    return jsonify({"message": "Signup successful"}), 201


@app.route("/login", methods=["POST"])
def login():
    creds = request.get_json()
    if not creds or "username" not in creds or "password" not in creds:
        return jsonify({"error": "Invalid data"}), 400

    users = load_login_data()
    for u in users:
        if u["username"] == creds["username"]:
            # Check if password is hashed or plain text (for backward compatibility)
            if u["password"].startswith("scrypt:") or u["password"].startswith("$2b$"):  # hashed password
                if check_password_hash(u["password"], creds["password"]):
                    return jsonify({"message": "Login successful", "username": u["username"]}), 200
            else:  # plain text (legacy)
                if u["password"] == creds["password"]:
                    # Update to hashed password
                    u["password"] = generate_password_hash(creds["password"])
                    save_login_data(users)
                    return jsonify({"message": "Login successful", "username": u["username"]}), 200

    return jsonify({"error": "Invalid username or password"}), 401


# ---------------- Data Helpers ----------------
def load_json(file_path):
    """Fallback JSON loader for compatibility"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(file_path, data):
    """Fallback JSON saver for compatibility"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------- Normalization Helpers ----------------
def normalize_profile(raw):
    """
    Normalize profile/candidate fields to consistent candidate object.
    - Ensures candidate_id, name, skills_possessed (lowercased), location_preference.
    - Matches the structure in candidates.json exactly
    """
    candidate = {}
    candidate_id = raw.get("candidate_id") or f"CAND_{uuid.uuid4().hex[:8]}"
    candidate["candidate_id"] = candidate_id

    candidate["name"] = (raw.get("name") or "").strip()
    skills = raw.get("skills_possessed") or raw.get("skills") or []
    seen = set()
    norm_skills = []
    for s in skills:
        if not isinstance(s, str):
            continue
        s2 = s.strip().lower()
        if s2 and s2 not in seen:
            seen.add(s2)
            norm_skills.append(s2)
    candidate["skills_possessed"] = norm_skills

    candidate["location_preference"] = (raw.get("location_preference") or raw.get("location") or "").strip()
    
    # Add all fields that exist in candidates.json structure
    for key in ("education_level", "field_of_study", "sector_interests"):
        if raw.get(key) is not None:
            if key == "sector_interests" and isinstance(raw[key], str):
                # Convert comma-separated string to list
                candidate[key] = [s.strip() for s in raw[key].split(',') if s.strip()]
            else:
                candidate[key] = raw[key]
    
    return candidate


def find_candidate_index_by_id(candidates, candidate_id):
    return next((i for i, c in enumerate(candidates) if c.get("candidate_id") == candidate_id), None)


def find_candidate_index_by_name_location(candidates, name, location):
    name_l = (name or "").strip().lower()
    loc_l = (location or "").strip().lower()
    return next((
        i for i, c in enumerate(candidates)
        if (c.get("name", "").strip().lower() == name_l and c.get("location_preference", "").strip().lower() == loc_l)
    ), None)


# ---------------- Migration ----------------
def migrate_profiles_into_candidates():
    """Migrate profiles to candidates in MongoDB"""
    profiles = convert_object_ids(load_data("profiles"))
    candidates = convert_object_ids(load_data("candidates"))

    changed_profiles = False
    changed_candidates = False

    for idx, raw in enumerate(profiles):
        if not raw.get("candidate_id"):
            new_id = f"CAND_{uuid.uuid4().hex[:8]}"
            profiles[idx]["candidate_id"] = new_id
            changed_profiles = True

        cand_obj = normalize_profile(profiles[idx])

        existing_idx = find_candidate_index_by_id(candidates, cand_obj["candidate_id"])
        if existing_idx is not None:
            existing = candidates[existing_idx]
            existing_skills = [s.strip().lower() for s in existing.get("skills_possessed", []) if isinstance(s, str)]
            for s in cand_obj.get("skills_possessed", []):
                if s not in existing_skills:
                    existing_skills.append(s)
            existing["skills_possessed"] = existing_skills
            if not existing.get("name") and cand_obj.get("name"):
                existing["name"] = cand_obj["name"]
            if not existing.get("location_preference") and cand_obj.get("location_preference"):
                existing["location_preference"] = cand_obj["location_preference"]
            # Update education and interests fields
            for field in ["education_level", "field_of_study", "sector_interests"]:
                if cand_obj.get(field) and not existing.get(field):
                    existing[field] = cand_obj[field]
            candidates[existing_idx] = existing
            changed_candidates = True
        else:
            dup_idx = find_candidate_index_by_name_location(candidates, cand_obj.get("name"), cand_obj.get("location_preference"))
            if dup_idx is None:
                candidates.append(cand_obj)
                changed_candidates = True
            else:
                existing = candidates[dup_idx]
                existing_skills = [s.strip().lower() for s in existing.get("skills_possessed", []) if isinstance(s, str)]
                for s in cand_obj.get("skills_possessed", []):
                    if s not in existing_skills:
                        existing_skills.append(s)
                existing["skills_possessed"] = existing_skills
                if not existing.get("candidate_id"):
                    existing["candidate_id"] = cand_obj["candidate_id"]
                if not existing.get("name") and cand_obj.get("name"):
                    existing["name"] = cand_obj["name"]
                if not existing.get("location_preference") and cand_obj.get("location_preference"):
                    existing["location_preference"] = cand_obj["location_preference"]
                # Update education and interests fields
                for field in ["education_level", "field_of_study", "sector_interests"]:
                    if cand_obj.get(field) and not existing.get(field):
                        existing[field] = cand_obj[field]
                candidates[dup_idx] = existing
                changed_candidates = True

    if changed_profiles:
        save_data("profiles", profiles)
        print("Updated profiles in MongoDB with generated candidate_id(s).")
    if changed_candidates:
        save_data("candidates", candidates)
        print("Merged profiles into candidates in MongoDB (added/updated entries).")


migrate_profiles_into_candidates()


# ---------------- Routes ----------------
@app.route("/")
def home():
    return "✅ Internship Recommendation Backend is running!"


@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    candidates = convert_object_ids(load_data("candidates"))
    normalized = []
    for c in candidates:
        norm = dict(c)
        norm["skills_possessed"] = [s.strip().lower() for s in c.get("skills_possessed", []) if isinstance(s, str)]
        normalized.append(norm)
    return jsonify({"candidates": normalized}), 200


@app.route("/api/profile", methods=["POST"])
def add_profile():
    profile_data = request.get_json()
    if not profile_data:
        return jsonify({"error": "No profile data received"}), 400

    profiles = convert_object_ids(load_data("profiles"))
    if not profile_data.get("candidate_id"):
        profile_data["candidate_id"] = f"CAND_{uuid.uuid4().hex[:8]}"
    
    # Add timestamp
    profile_data["created_at"] = str(uuid.uuid4().time_low)  # Simple timestamp
    profiles.append(profile_data)
    save_data("profiles", profiles)

    candidate_obj = normalize_profile(profile_data)
    candidates = convert_object_ids(load_data("candidates"))

    existing_idx = find_candidate_index_by_id(candidates, candidate_obj["candidate_id"])
    if existing_idx is None:
        dup_idx = find_candidate_index_by_name_location(candidates, candidate_obj.get("name"), candidate_obj.get("location_preference"))
        if dup_idx is None:
            candidates.append(candidate_obj)
            save_data("candidates", candidates)
            saved = candidate_obj
            message = "Profile saved and merged into candidates."
        else:
            existing = candidates[dup_idx]
            existing_skills = [s.strip().lower() for s in existing.get("skills_possessed", []) if isinstance(s, str)]
            for s in candidate_obj.get("skills_possessed", []):
                if s not in existing_skills:
                    existing_skills.append(s)
            existing["skills_possessed"] = existing_skills
            if not existing.get("candidate_id"):
                existing["candidate_id"] = candidate_obj["candidate_id"]
            # Update education and interests fields
            for field in ["education_level", "field_of_study", "sector_interests"]:
                if candidate_obj.get(field) and not existing.get(field):
                    existing[field] = candidate_obj[field]
            candidates[dup_idx] = existing
            save_data("candidates", candidates)
            saved = existing
            message = "Profile saved and merged into an existing candidate record."
    else:
        candidates[existing_idx] = candidate_obj
        save_data("candidates", candidates)
        saved = candidate_obj
        message = "Profile saved and candidates list updated."

    return jsonify({"message": message, "candidate": saved}), 201


@app.route("/api/profile/<candidate_id>", methods=["GET"])
def get_profile(candidate_id):
    candidates = convert_object_ids(load_data("candidates"))
    candidate = next((c for c in candidates if c.get("candidate_id") == candidate_id), None)
    
    if not candidate:
        profiles = convert_object_ids(load_data("profiles"))
        candidate = next((p for p in profiles if p.get("candidate_id") == candidate_id), None)
    
    if not candidate:
        return jsonify({"error": "Profile not found"}), 404
    
    return jsonify({"profile": candidate}), 200


@app.route("/api/internships", methods=["GET"])
def get_internships():
    internships = convert_object_ids(load_data("internships"))
    return jsonify({"internships": internships}), 200


# ---------------- Recommendations ----------------
get_recommendations = None
try:
    from backend.ml_model import get_recommendations  # type: ignore
except Exception:
    try:
        from ml_model import get_recommendations  # type: ignore
    except Exception:
        def get_recommendations(candidate, internships):
            recommendations = []
            candidate_skills = set([s.strip().lower() for s in candidate.get("skills_possessed", []) if isinstance(s, str)])
            
            for internship in internships:
                internship_skills = set([s.strip().lower() for s in internship.get("skills_required", []) if isinstance(s, str)])
                common_skills = candidate_skills & internship_skills
                
                # Calculate match score as percentage
                if len(internship_skills) > 0:
                    match_score = len(common_skills) / len(internship_skills)
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
                        "match_score": match_score
                    })
            
            # Sort by match score in descending order
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)
            return recommendations[:10]


@app.route("/api/recommendations/<candidate_id>", methods=["GET"])
def recommend_internships(candidate_id):
    candidates = convert_object_ids(load_data("candidates"))
    internships = convert_object_ids(load_data("internships"))

    cand_map = {}
    for c in candidates:
        cid = c.get("candidate_id")
        if not cid:
            continue
        skills = [s.strip().lower() for s in c.get("skills_possessed", []) if isinstance(s, str)]
        candidate_copy = dict(c)
        candidate_copy["skills_possessed"] = skills
        cand_map[cid] = candidate_copy

    candidate = cand_map.get(candidate_id)

    if not candidate:
        profiles = convert_object_ids(load_data("profiles"))
        raw = next((p for p in profiles if p.get("candidate_id") == candidate_id), None)
        if raw:
            candidate = normalize_profile(raw)
        else:
            name_match = next((c for c in candidates if (c.get("name") or "").strip().lower() == candidate_id.strip().lower()), None)
            if name_match:
                candidate = normalize_profile(name_match)

    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    recommendations = get_recommendations(candidate, internships)

    return jsonify({
        "candidate": candidate.get("name"),
        "candidate_id": candidate.get("candidate_id"),
        "recommendations": recommendations
    }), 200


@app.route("/api/recommendations/by_internship/<internship_id>", methods=["GET"])
def recommend_by_internship(internship_id):
    internships = convert_object_ids(load_data("internships"))
    base_internship = next((i for i in internships if i.get("internship_id") == internship_id), None)
    
    if not base_internship:
        return jsonify({"error": "Internship not found"}), 404
    
    # Find similar internships based on skills
    base_skills = set([s.strip().lower() for s in base_internship.get("skills_required", []) if isinstance(s, str)])
    recommendations = []
    
    for internship in internships:
        if internship.get("internship_id") == internship_id:
            continue
            
        intern_skills = set([s.strip().lower() for s in internship.get("skills_required", []) if isinstance(s, str)])
        common_skills = base_skills & intern_skills
        # Calculate match score as percentage of base internship skills
        match_score = len(common_skills) / len(base_skills) if base_skills else 0
        
        if match_score > 0:
            recommendations.append({
                "internship_id": internship.get("internship_id"),
                "title": internship.get("title"),
                "organization": internship.get("organization"),
                "location": internship.get("location"),
                "sector": internship.get("sector"),
                "description": internship.get("description"),
                "match_score": match_score
            })
    
    # Sort by match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    return jsonify({
        "base_internship": base_internship.get("title"),
        "recommendations": recommendations[:10]  # Top 10 matches
    }), 200


@app.route("/api/recommendations/current_user", methods=["GET"])
def get_current_user_recommendations():
    """Get recommendations for the current logged-in user based on their profile"""
    # This would typically get the user from session/token, but for now we'll use a simple approach
    # In a real app, you'd get the user ID from the session or JWT token
    username = request.headers.get('X-Username')  # Simple header-based approach
    
    if not username:
        return jsonify({"error": "User not identified"}), 401
    
    # Find user's profile in candidates
    candidates = convert_object_ids(load_data("candidates"))
    user_profile = None
    
    # Try to find by exact username match in name field
    for candidate in candidates:
        if candidate.get("name") and candidate.get("name").lower() == username.lower():
            user_profile = candidate
            break
    
    if not user_profile:
        return jsonify({"error": "User profile not found. Please create a profile first."}), 404
    
    # Get recommendations
    internships = convert_object_ids(load_data("internships"))
    recommendations = get_recommendations(user_profile, internships)
    
    return jsonify({
        "candidate": user_profile.get("name"),
        "candidate_id": user_profile.get("candidate_id"),
        "recommendations": recommendations
    }), 200


if __name__ == "__main__":
    # Initialize MongoDB collections if needed
    migrate_profiles_into_candidates()
    app.run(debug=True, port=3000)
