# --- Fetch profile by username (for login integration) ---
# backend/app.py
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import load_data, save_data, convert_object_ids
# Robust import of city data
try:
    from backend.city_coords import CITY_COORDINATES  # type: ignore
except Exception:
    CITY_COORDINATES = None  # type: ignore
try:
    from backend.city_coords import get_all_display_cities_sorted  # type: ignore
except Exception:
    get_all_display_cities_sorted = None  # type: ignore

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Add secret key for sessions
CORS(app, supports_credentials=True)  # Enable credentials for CORS


BASE_DIR = os.path.dirname(__file__)                 # backend/
DATA_DIR = os.path.join(BASE_DIR, "..", "data")      # ../data
LOGIN_FILE = os.path.join(DATA_DIR, "login_info.json")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
INTERNSHIPS_FILE = os.path.join(DATA_DIR, "internships.json")
print(f"🔎 Data folder in use: {DATA_DIR}")  # debug print

@app.route("/api/profiles/by_username/<username>", methods=["GET"])
def get_profile_by_username(username):
    profiles = convert_object_ids(load_data("profiles"))
    # Case-insensitive match
    candidate = next((p for p in profiles if p.get("name", "").strip().lower() == username.strip().lower()), None)
    if not candidate:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify({"profile": candidate}), 200

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
    
    # Set session state for immediate login
    session['logged_in'] = True
    session['username'] = creds["username"]
    
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
                    # Set session state
                    session['logged_in'] = True
                    session['username'] = u["username"]
                    return jsonify({"message": "Login successful", "username": u["username"]}), 200
            else:  # plain text (legacy)
                if u["password"] == creds["password"]:
                    # Update to hashed password
                    u["password"] = generate_password_hash(creds["password"])
                    save_login_data(users)
                    # Set session state
                    session['logged_in'] = True
                    session['username'] = u["username"]
                    return jsonify({"message": "Login successful", "username": u["username"]}), 200

    return jsonify({"error": "Invalid username or password"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200


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
    Normalize profile fields to consistent candidate object.
    - Ensures candidate_id, name, skills_possessed (lowercased), location_preference.
    - Matches the structure in profiles.json exactly
    """
    candidate = {}
    candidate_id = raw.get("candidate_id") or f"CAND_{uuid.uuid4().hex[:8]}"
    candidate["candidate_id"] = candidate_id

    candidate["name"] = (raw.get("name") or "").strip()
    # --- Robustly flatten skills_possessed ---
    skills = raw.get("skills_possessed") or raw.get("skills") or []
    # Robustly flatten any nested lists (arbitrary depth)
    def _deep_flatten_skills(sk):
        if isinstance(sk, list):
            out = []
            for item in sk:
                out.extend(_deep_flatten_skills(item))
            return out
        elif isinstance(sk, str):
            return [sk]
        else:
            return []
    flat_skills = _deep_flatten_skills(skills)
    seen = set()
    norm_skills = []
    for s in flat_skills:
        if not isinstance(s, str):
            continue
        s2 = s.strip().lower()
        if s2 and s2 not in seen:
            seen.add(s2)
            norm_skills.append(s2)
    candidate["skills_possessed"] = norm_skills

    candidate["location_preference"] = (raw.get("location_preference") or raw.get("location") or "").strip()
    # Add all fields that exist in profiles.json structure
    for key in ("education_level", "field_of_study", "sector_interests", "created_at"):
        if raw.get(key) is not None:
            if key == "sector_interests":
                val = raw[key]
                if isinstance(val, str):
                    candidate[key] = [s.strip() for s in val.split(',') if s.strip()]
                elif isinstance(val, list):
                    # Flatten and clean
                    candidate[key] = [str(s).strip() for sub in val for s in (sub if isinstance(sub, list) else [sub]) if str(s).strip()]
                else:
                    candidate[key] = []
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



# ---------------- Routes ----------------
@app.route("/")
def home():
    return "✅ Internship Recommendation Backend is running!"



# Deprecated: /api/candidates endpoint removed. Use /api/profile endpoints instead.



@app.route("/api/profile", methods=["POST"])
def add_profile():
    profile_data = request.get_json()
    if not profile_data:
        return jsonify({"error": "No profile data received"}), 400

    profiles = convert_object_ids(load_data("profiles"))
    is_new = False
    if not profile_data.get("candidate_id"):
        profile_data["candidate_id"] = f"CAND_{uuid.uuid4().hex[:8]}"
        is_new = True
    # Add or update timestamp
    profile_data["created_at"] = str(uuid.uuid4().time_low)  # Simple timestamp

    # Always normalize before saving
    normalized_profile = normalize_profile(profile_data)

    # Check if candidate exists
    idx = find_candidate_index_by_id(profiles, normalized_profile["candidate_id"])
    if idx is not None:
        # Update existing profile
        profiles[idx] = normalized_profile
        message = "Profile updated."
    else:
        # Add new profile
        profiles.append(normalized_profile)
        message = "Profile created."
    save_data("profiles", profiles)
    return jsonify({"message": message, "candidate": normalized_profile}), 201



@app.route("/api/profile/<candidate_id>", methods=["GET"])
def get_profile(candidate_id):
    profiles = convert_object_ids(load_data("profiles"))
    candidate = next((p for p in profiles if p.get("candidate_id") == candidate_id), None)
    if not candidate:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify({"profile": candidate}), 200


@app.route("/api/internships", methods=["GET"])
def get_internships():
    internships = convert_object_ids(load_data("internships"))
    return jsonify({"internships": internships}), 200


# ------------- Cities API (static list from hardcoded coords) -------------
@app.route("/api/cities", methods=["GET"])
def list_cities():
    try:
        source = None
        # Try preferred helper
        if callable(get_all_display_cities_sorted):
            try:
                cities = get_all_display_cities_sorted()
                if isinstance(cities, list) and cities:
                    # Ensure uniqueness and stable ordering
                    names = sorted(set([str(c).strip() for c in cities if isinstance(c, str) and c.strip()]))
                    source = "display_names"
                    resp = jsonify({"cities": names, "count": len(names), "source": source})
                    resp.headers["X-Total-Count"] = str(len(names))
                    return resp, 200
            except Exception:
                pass
        # Fallback to keys from CITY_COORDINATES
        def _titleize(name: str) -> str:
            parts = []
            for token in name.split(' '):
                if '-' in token:
                    sub = '-'.join(s[:1].upper() + s[1:] if s else s for s in token.split('-'))
                    parts.append(sub)
                else:
                    parts.append(token[:1].upper() + token[1:] if token else token)
            return ' '.join(parts)
        names = []
        try:
            if CITY_COORDINATES:
                names = sorted({_titleize(k) for k in CITY_COORDINATES.keys() if isinstance(k, str)})
                source = "city_coordinates"
        except Exception:
            names = []
        if not names:
            # As another fallback, try reading data/cities.in.json
            try:
                data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cities.in.json')
                with open(data_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                for item in raw if isinstance(raw, list) else []:
                    city = (item.get('city') or '').strip()
                    if city:
                        names.append(_titleize(city.lower()))
                names = sorted(set(names))
                source = "data_file"
            except Exception:
                pass
        if names:
            resp = jsonify({"cities": names, "count": len(names), "source": source or "unknown"})
            resp.headers["X-Total-Count"] = str(len(names))
            return resp, 200
        # Last resort
        names = sorted(['Mumbai','Delhi','Bengaluru','Chennai','Kolkata','Pune','Jaipur','Chandigarh','Ahmedabad','Hyderabad'])
        resp = jsonify({"cities": names, "count": len(names), "source": "minimal_fallback"})
        resp.headers["X-Total-Count"] = str(len(names))
        return resp, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
                        "match_score": match_score
                    })
            
            # Sort by match score in descending order
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)
            return recommendations[:10]



@app.route("/api/recommendations/<candidate_id>", methods=["GET"])
def recommend_internships(candidate_id):
    profiles = convert_object_ids(load_data("profiles"))
    internships = convert_object_ids(load_data("internships"))
    candidate = next((p for p in profiles if p.get("candidate_id") == candidate_id), None)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    # Always robustly normalize before recommendations
    candidate_norm = normalize_profile(candidate)
    recommendations = get_recommendations(candidate_norm, internships)
    return jsonify({
        "candidate": candidate_norm.get("name"),
        "candidate_id": candidate_norm.get("candidate_id"),
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
        # Calculate match score as percentage of base internship skills (0-100)
        match_score = (len(common_skills) / len(base_skills) * 100) if base_skills else 0
        
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

    app.run(debug=True, port=3000)
