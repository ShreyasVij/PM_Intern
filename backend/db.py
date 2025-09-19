# backend/db.py
import json
import os
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- Configuration for Database ---
# Get the base directory to locate the data folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# Try to connect to MongoDB
client = None
db = None
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    db = client.internship_recommender
    client.admin.command('ismaster')
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    print("⚠️ Falling back to local JSON file persistence.")

# --- Data Access Functions ---
def load_data(collection_name):
    """Loads data from a MongoDB collection or a local JSON file."""
    if db is not None:
        return list(db[collection_name].find({}))
    else:
        file_path = os.path.join(DATA_DIR, f"{collection_name}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

def save_data(collection_name, data):
    """Saves data to a MongoDB collection or a local JSON file."""
    if db is not None:
        db[collection_name].delete_many({})
        if data:
            db[collection_name].insert_many(data)
    else:
        file_path = os.path.join(DATA_DIR, f"{collection_name}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def convert_object_ids(data):
    """Recursively converts MongoDB ObjectId to string for JSON serialization."""
    if isinstance(data, list):
        return [convert_object_ids(item) for item in data]
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, (dict, list)):
                data[key] = convert_object_ids(value)
    return data