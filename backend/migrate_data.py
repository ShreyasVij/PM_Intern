# backend/migrate_data.py
import json
import os
from pymongo import MongoClient

# --- Configuration ---
# Adjust the MongoDB connection string if needed
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'internship_recommender'

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

# --- Helper Functions ---
def load_json_file(file_name):
    """Loads data from a local JSON file."""
    file_path = os.path.join(DATA_DIR, file_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Successfully loaded {file_name}")
            return data
    except FileNotFoundError:
        print(f"❌ File not found: {file_name}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_name}: {e}")
        return []
    except Exception as e:
        print(f"❌ Error loading {file_name}: {e}")
        return []

def migrate_to_mongodb():
    """Connects to MongoDB and migrates data from JSON files."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        client.admin.command('ismaster')  # Check if connection is successful
        print("✅ Successfully connected to MongoDB.")


        # Load data from local JSON files
        internships_data = load_json_file("internships.json")
        profiles_data = load_json_file("profiles.json")
        login_info_data = load_json_file("login_info.json")
        skills_synonyms_data = load_json_file("skills_synonyms.json")

        # Migrate data to MongoDB collections
        print("Migrating data to MongoDB...")

        # Insert internships
        if internships_data:
            db.internships.delete_many({})
            db.internships.insert_many(internships_data)
            print(f"-> Migrated {len(internships_data)} internships.")

        # Insert profiles (canonical candidate data)
        if profiles_data:
            db.profiles.delete_many({})
            db.profiles.insert_many(profiles_data)
            print(f"-> Migrated {len(profiles_data)} profiles.")

        # Insert login information
        if login_info_data:
            db.login_info.delete_many({})
            db.login_info.insert_many(login_info_data)
            print(f"-> Migrated {len(login_info_data)} login records.")

        # Insert skills synonyms mapping
        if skills_synonyms_data:
            db.skills_synonyms.delete_many({})
            if isinstance(skills_synonyms_data, dict):
                # Convert dict to array of key-value pairs
                skills_array = [{"skill": key, "synonyms": value} for key, value in skills_synonyms_data.items()]
                db.skills_synonyms.insert_many(skills_array)
                print(f"-> Migrated {len(skills_array)} skill synonym mappings.")
            elif isinstance(skills_synonyms_data, list):
                db.skills_synonyms.insert_many(skills_synonyms_data)
                print(f"-> Migrated {len(skills_synonyms_data)} skill synonym mappings (list format).")
            else:
                print("❌ skills_synonyms.json is neither a dict nor a list. Skipping.")

        print("\n" + "="*50)
        print("MIGRATION SUMMARY")
        print("="*50)
        print(f"✅ Internships: {len(internships_data) if internships_data else 0} records")
        print(f"✅ Profiles: {len(profiles_data) if profiles_data else 0} records")
        print(f"✅ Login Info: {len(login_info_data) if login_info_data else 0} records")
        print(f"✅ Skills Synonyms: {len(skills_synonyms_data) if skills_synonyms_data else 0} mappings")
        print("="*50)
        print("Migration complete. The database is now seeded with data from your JSON files.")

    except Exception as e:
        print(f"❌ Migration failed. Ensure MongoDB is running. Error: {e}")

if __name__ == "__main__":
    migrate_to_mongodb()
    