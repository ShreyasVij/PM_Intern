# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)                 # backend/
DATA_DIR = os.path.join(BASE_DIR, "..", "data")      # ../data
LOGIN_FILE = os.path.join(DATA_DIR, "login-info.json")

CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.json")
INTERNSHIPS_FILE = os.path.join(DATA_DIR, "internships.json")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")

print(f"🔎 Data folder in use: {DATA_DIR}")  # debug print

def load_login_data():
    try:
        with open(LOGIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_login_data(data):
    os.makedirs(os.path.dirname(LOGIN_FILE), exist_ok=True)
    with open(LOGIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/signup", methods=["POST"])
def signup():
    creds = request.get_json()
    if not creds or "username" not in creds or "password" not in creds:
        return jsonify({"error": "Invalid data"}), 400

    users = load_login_data()
    if any(u["username"] == creds["username"] for u in users):
        return jsonify({"error": "User already exists"}), 400

    users.append({"username": creds["username"], "password": creds["password"]})
    save_login_data(users)
    return jsonify({"message": "Signup successful"}), 201


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


@app.route("/login", methods=["POST"])
def login():
    creds = request.get_json()
    if not creds or "username" not in creds or "password" not in creds:
        return jsonify({"error": "Invalid data"}), 400

    users = load_login_data()
    for u in users:
        if u["username"] == creds["username"] and u["password"] == creds["password"]:
            return jsonify({"message": "Login successful"}), 200

    return jsonify({"error": "Invalid username or password"}), 401

def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def normalize_profile(raw):
    """
    Normalize profile/candidate fields to consistent candidate object.
    - Ensures candidate_id, name, skills_possessed (lowercased), location_preference.
    """
    candidate = {}
    # use provided candidate_id or create one
    candidate_id = raw.get("candidate_id") or f"CAND_{uuid.uuid4().hex[:8]}"
    candidate["candidate_id"] = candidate_id

    candidate["name"] = (raw.get("name") or "").strip()
    # some submissions may use 'skills' vs 'skills_possessed'
    skills = raw.get("skills_possessed") or raw.get("skills") or []
    # normalize skills: trim + lowercase + unique preserving order
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

    # location preference
    candidate["location_preference"] = (raw.get("location_preference") or raw.get("location") or "").strip()
    # optional other fields pass-through if present
    for key in ("education_level", "field_of_study", "sector_interests"):
        if raw.get(key) is not None:
            candidate[key] = raw.get(key)
    return candidate

def find_candidate_index_by_id(candidates, candidate_id):
    return next((i for i, c in enumerate(candidates) if c.get("candidate_id") == candidate_id), None)

def find_candidate_index_by_name_location(candidates, name, location):
    name_l = (name or "").strip().lower()
    loc_l = (location or "").strip().lower()
    return next((
        i for i, c in enumerate(candidates)
        if (c.get("name","").strip().lower() == name_l and (c.get("location_preference","").strip().lower() == loc_l))
    ), None)

def migrate_profiles_into_candidates():
    """
    Safe, idempotent migration:
    - For each profile in profiles.json that lacks candidate_id, assign one and save back to profiles.json.
    - Ensure there's a normalized candidate object in candidates.json for each profile (append or merge).
    """
    profiles = load_json(PROFILES_FILE)
    candidates = load_json(CANDIDATES_FILE)

    changed_profiles = False
    changed_candidates = False

    for idx, raw in enumerate(profiles):
        # assign candidate_id if missing
        if not raw.get("candidate_id"):
            new_id = f"CAND_{uuid.uuid4().hex[:8]}"
            profiles[idx]["candidate_id"] = new_id
            changed_profiles = True

        # create normalized candidate object from profile
        cand_obj = normalize_profile(profiles[idx])

        # try to find by candidate_id
        existing_idx = find_candidate_index_by_id(candidates, cand_obj["candidate_id"])
        if existing_idx is not None:
            # merge skills (add any new normalized skills)
            existing = candidates[existing_idx]
            existing_skills = [s.strip().lower() for s in existing.get("skills_possessed", []) if isinstance(s, str)]
            for s in cand_obj.get("skills_possessed", []):
                if s not in existing_skills:
                    existing_skills.append(s)
            existing["skills_possessed"] = existing_skills
            # ensure name/location exist
            if not existing.get("name") and cand_obj.get("name"):
                existing["name"] = cand_obj["name"]
            if not existing.get("location_preference") and cand_obj.get("location_preference"):
                existing["location_preference"] = cand_obj["location_preference"]
            candidates[existing_idx] = existing
            changed_candidates = True
        else:
            # attempt to find by name+location to avoid duplicates
            dup_idx = find_candidate_index_by_name_location(candidates, cand_obj.get("name"), cand_obj.get("location_preference"))
            if dup_idx is None:
                # new candidate: append normalized object
                candidates.append(cand_obj)
                changed_candidates = True
            else:
                # merge into existing duplicate
                existing = candidates[dup_idx]
                existing_skills = [s.strip().lower() for s in existing.get("skills_possessed", []) if isinstance(s, str)]
                for s in cand_obj.get("skills_possessed", []):
                    if s not in existing_skills:
                        existing_skills.append(s)
                existing["skills_possessed"] = existing_skills
                # ensure candidate_id exists (preserve existing id)
                if not existing.get("candidate_id"):
                    existing["candidate_id"] = cand_obj["candidate_id"]
                # ensure name/location set
                if not existing.get("name") and cand_obj.get("name"):
                    existing["name"] = cand_obj["name"]
                if not existing.get("location_preference") and cand_obj.get("location_preference"):
                    existing["location_preference"] = cand_obj["location_preference"]
                candidates[dup_idx] = existing
                changed_candidates = True

    # persist if changed
    if changed_profiles:
        save_json(PROFILES_FILE, profiles)
        print("Updated profiles.json with generated candidate_id(s).")
    if changed_candidates:
        save_json(CANDIDATES_FILE, candidates)
        print("Merged profiles into candidates.json (added/updated entries).")

# run migration at startup so legacy profiles won't break recommendations
migrate_profiles_into_candidates()

@app.route("/")
def home():
    return "✅ Internship Recommendation Backend is running!"

@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    candidates = load_json(CANDIDATES_FILE)
    # make sure we return a normalized view (skills array exists)
    normalized = []
    for c in candidates:
        norm = dict(c)  # shallow copy
        norm["skills_possessed"] = [s.strip().lower() for s in c.get("skills_possessed", []) if isinstance(s, str)]
        normalized.append(norm)
    return jsonify({"candidates": normalized}), 200

@app.route("/api/profile", methods=["POST"])
def add_profile():
    profile_data = request.get_json()
    if not profile_data:
        return jsonify({"error": "No profile data received"}), 400

    # Save raw submission to profiles.json (audit log)
    profiles = load_json(PROFILES_FILE)
    # if profile has no candidate_id, generate one now
    if not profile_data.get("candidate_id"):
        profile_data["candidate_id"] = f"CAND_{uuid.uuid4().hex[:8]}"
    profiles.append(profile_data)
    save_json(PROFILES_FILE, profiles)

    # Normalize and append/update candidates.json so recommendations work immediately
    candidate_obj = normalize_profile(profile_data)
    candidates = load_json(CANDIDATES_FILE)

    existing_idx = find_candidate_index_by_id(candidates, candidate_obj["candidate_id"])
    if existing_idx is None:
        # avoid adding duplicate by name+location
        dup_idx = find_candidate_index_by_name_location(candidates, candidate_obj.get("name"), candidate_obj.get("location_preference"))
        if dup_idx is None:
            candidates.append(candidate_obj)
            save_json(CANDIDATES_FILE, candidates)
            saved = candidate_obj
            message = "Profile saved and merged into candidates."
        else:
            # merge into existing
            existing = candidates[dup_idx]
            existing_skills = [s.strip().lower() for s in existing.get("skills_possessed", []) if isinstance(s, str)]
            for s in candidate_obj.get("skills_possessed", []):
                if s not in existing_skills:
                    existing_skills.append(s)
            existing["skills_possessed"] = existing_skills
            if not existing.get("candidate_id"):
                existing["candidate_id"] = candidate_obj["candidate_id"]
            candidates[dup_idx] = existing
            save_json(CANDIDATES_FILE, candidates)
            saved = existing
            message = "Profile saved and merged into an existing candidate record."
    else:
        # update/replace existing candidate record
        candidates[existing_idx] = candidate_obj
        save_json(CANDIDATES_FILE, candidates)
        saved = candidate_obj
        message = "Profile saved and candidates list updated."

    return jsonify({"message": message, "candidate": saved}), 201

@app.route("/api/internships", methods=["GET"])
def get_internships():
    internships = load_json(INTERNSHIPS_FILE)
    return jsonify({"internships": internships}), 200

# Import or implement your ML recommendation function here.
# Try both import styles so module works when run as package or script.
get_recommendations = None
try:
    # preferred when running as package: python -m backend.app
    from backend.ml_model import get_recommendations  # type: ignore
except Exception:
    try:
        # preferred when running as script from backend/: python app.py
        from ml_model import get_recommendations  # type: ignore
    except Exception:
        # fallback simple implementation if import fails
        def get_recommendations(candidate, internships):
            recommendations = []
            candidate_skills = set(candidate.get("skills_possessed", []))
            for internship in internships:
                internship_skills = set(internship.get("skills_required", []))
                # normalize both sides to lower-case to avoid case mismatch
                internship_skills = set([s.strip().lower() for s in internship_skills if isinstance(s, str)])
                score = len(set([s.strip().lower() for s in candidate_skills if isinstance(s, str)]) & internship_skills)
                recommendations.append({
                    "internship_id": internship.get("internship_id"),
                    "title": internship.get("title"),
                    "organization": internship.get("organization"),
                    "location": internship.get("location"),
                    "sector": internship.get("sector"),
                    "match_score": score
                })
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)
            return recommendations[:10]

@app.route("/api/recommendations/<candidate_id>", methods=["GET"])
def recommend_internships(candidate_id):
    # Load candidates and internships
    candidates = load_json(CANDIDATES_FILE)
    internships = load_json(INTERNSHIPS_FILE)

    # Normalize candidates for matching (create a map by id)
    cand_map = {}
    for c in candidates:
        cid = c.get("candidate_id")
        if not cid:
            continue
        # normalize skills to lowercase list
        skills = [s.strip().lower() for s in c.get("skills_possessed", []) if isinstance(s, str)]
        candidate_copy = dict(c)
        candidate_copy["skills_possessed"] = skills
        cand_map[cid] = candidate_copy

    candidate = cand_map.get(candidate_id)

    # If not found by id, try profiles.json and normalize
    if not candidate:
        profiles = load_json(PROFILES_FILE)
        # try to find exact id in profiles
        raw = next((p for p in profiles if p.get("candidate_id") == candidate_id), None)
        if raw:
            candidate = normalize_profile(raw)
        else:
            # fallback: try find by name match (case-insensitive) in candidates
            # this is best-effort; recommend calling endpoint with candidate_id whenever possible
            name_match = next((c for c in candidates if (c.get("name") or "").strip().lower() == candidate_id.strip().lower()), None)
            if name_match:
                candidate = normalize_profile(name_match)

    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404

    # call recommendation function
    recommendations = get_recommendations(candidate, internships)

    return jsonify({
        "candidate": candidate.get("name"),
        "candidate_id": candidate.get("candidate_id"),
        "recommendations": recommendations
    }), 200

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    # ensure files exist
    for fp in (CANDIDATES_FILE, INTERNSHIPS_FILE, PROFILES_FILE):
        if not os.path.exists(fp):
            save_json(fp, [])
    # run migration again right before starting (safe, idempotent)
    migrate_profiles_into_candidates()
    app.run(debug=True, port=3000)
