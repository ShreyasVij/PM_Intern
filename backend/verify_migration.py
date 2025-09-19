# backend/verify_migration.py
import json
import os
from pymongo import MongoClient

# --- Configuration ---
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'internship_recommender'

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

def verify_migration():
    """Verifies that all data was properly migrated to MongoDB."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        client.admin.command('ismaster')
        print("✅ Successfully connected to MongoDB.")

        print("\n" + "="*60)
        print("MIGRATION VERIFICATION")
        print("="*60)

        # Check each collection
        collections = {
            'candidates': 'candidates.json',
            'internships': 'internships.json', 
            'profiles': 'profiles.json',
            'login_info': 'login-info.json',
            'skills_synonyms': 'skills_synonyms.json'
        }

        for collection_name, json_file in collections.items():
            # Count documents in MongoDB
            mongo_count = db[collection_name].count_documents({})
            
            # Count documents in JSON file
            json_path = os.path.join(DATA_DIR, json_file)
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    if collection_name == 'skills_synonyms':
                        # Skills synonyms is stored as an object, not array
                        json_count = len(json_data)
                    else:
                        json_count = len(json_data) if isinstance(json_data, list) else 1
            except Exception as e:
                json_count = 0
                print(f"❌ Could not read {json_file}: {e}")

            # Compare counts
            if mongo_count == json_count:
                print(f"✅ {collection_name}: {mongo_count} records (matches {json_file})")
            else:
                print(f"❌ {collection_name}: {mongo_count} in MongoDB vs {json_count} in {json_file}")

        print("="*60)
        print("Verification complete.")

    except Exception as e:
        print(f"❌ Verification failed. Error: {e}")

if __name__ == "__main__":
    verify_migration()
