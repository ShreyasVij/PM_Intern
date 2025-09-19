# migrate_mongo_to_json.py
"""
Script to export collections from MongoDB to local JSON files in the data directory.
"""
import os
import json
from pymongo import MongoClient

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'internship_recommender'
COLLECTIONS = ["profiles", "login_info", "internships", "skills_synonyms"]

os.makedirs(DATA_DIR, exist_ok=True)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def export_collection_to_json(collection_name):
    print(f"Exporting '{collection_name}'...")
    data = list(db[collection_name].find({}))
    # Convert ObjectId to string and remove MongoDB-specific fields
    for doc in data:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    out_path = os.path.join(DATA_DIR, f"{collection_name}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {len(data)} records to {out_path}")

def main():
    for col in COLLECTIONS:
        export_collection_to_json(col)
    print("\n✅ All collections exported to JSON files.")

if __name__ == "__main__":
    main()
