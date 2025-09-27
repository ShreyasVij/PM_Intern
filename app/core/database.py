# app/core/database.py
"""
Database manager with improved structure
Refactored from backend/db.py
"""

import json
import os
from pymongo import MongoClient, errors
from bson import ObjectId
import time

# Try to import config and logger, fallback to environment variables
try:
    from app.config import get_config
    config = get_config()
    MONGO_URI = config.MONGO_URI
    DB_NAME = config.DB_NAME
    DATA_DIR = config.DATA_DIR
    POOL_SIZE = config.MONGODB_POOL_SIZE
except ImportError:
    import os
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'internship_recommender')
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    POOL_SIZE = int(os.getenv('MONGODB_POOL_SIZE', 10))

try:
    from app.utils.logger import db_logger
    log = db_logger.info
    log_error = db_logger.error
    log_warning = db_logger.warning
except ImportError:
    log = print
    log_error = print
    log_warning = print

class DatabaseManager:
    """Singleton database manager with connection pooling and health checks."""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize database connection."""
        try:
            self._client = MongoClient(
                MONGO_URI,
                maxPoolSize=POOL_SIZE,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=10000,
                connectTimeoutMS=10000
            )
            self._db = self._client[DB_NAME]
            
            # Test connection
            self._client.admin.command('ping')
            log(f"Successfully connected to MongoDB: {DB_NAME}")
            
        except errors.ServerSelectionTimeoutError:
            log_error("MongoDB connection timeout. Is MongoDB running?")
            self._client = None
            self._db = None
        except Exception as e:
            log_error(f"MongoDB connection failed: {e}")
            self._client = None
            self._db = None
    
    def get_db(self):
        """Get database instance with health check."""
        if self._db is None:
            self._initialize()
        return self._db
    
    def health_check(self):
        """Check database health."""
        try:
            if self._client is None:
                return False
            self._client.admin.command('ping')
            return True
        except Exception as e:
            log_error(f"Database health check failed: {e}")
            return False
    
    def close_connection(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            log("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_database():
    """Get database instance."""
    return db_manager.get_db()

def convert_object_ids(data):
    """Convert MongoDB ObjectId to string for JSON serialization."""
    if isinstance(data, list):
        return [convert_object_ids(item) for item in data]
    elif isinstance(data, dict):
        converted = {}
        for key, value in data.items():
            if isinstance(value, ObjectId):
                converted[key] = str(value)
            elif isinstance(value, (dict, list)):
                converted[key] = convert_object_ids(value)
            else:
                converted[key] = value
        return converted
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

def load_data(collection_name, use_cache=True):
    """Load data strictly from MongoDB (Atlas). No JSON fallback."""
    start_time = time.time()
    
    try:
        # Try MongoDB first
        if db_manager.health_check():
            db = get_database()
            collection = db[collection_name]
            
            # Add basic indexing for common queries
            if collection_name == "profiles":
                collection.create_index("candidate_id")
                collection.create_index("name")
            elif collection_name == "internships":
                collection.create_index("internship_id")
                collection.create_index("skills_required")
            
            data = list(collection.find())
            log(f"[DB] Fetched '{collection_name}' from MongoDB ({len(data)} records) in {time.time() - start_time:.3f}s")
            return convert_object_ids(data)
            
    except Exception as e:
        log_warning(f"[DB] MongoDB fetch failed for '{collection_name}': {e}")
    
    # Strict Atlas mode: no JSON fallback
    return []

def save_data(collection_name, data):
    """Save data to MongoDB only (Atlas). No JSON writes."""
    start_time = time.time()
    mongo_success = False
    json_success = False
    
    # Save to MongoDB
    try:
        if db_manager.health_check():
            db = get_database()
            collection = db[collection_name]
            
            # Clear and insert new data
            collection.delete_many({})
            if data:
                # Convert string IDs back to ObjectId for MongoDB
                mongo_data = []
                for item in data:
                    mongo_item = item.copy()
                    if '_id' in mongo_item and isinstance(mongo_item['_id'], str):
                        try:
                            mongo_item['_id'] = ObjectId(mongo_item['_id'])
                        except:
                            # Remove invalid ObjectId
                            del mongo_item['_id']
                    mongo_data.append(mongo_item)
                
                collection.insert_many(mongo_data)
            
            mongo_success = True
            log(f"[DB] Saved '{collection_name}' to MongoDB ({len(data)} records) in {time.time() - start_time:.3f}s")
            
    except Exception as e:
        log_error(f"[DB] MongoDB save failed for '{collection_name}': {e}")
    
    # Strict Atlas mode: no JSON writes
    
    if not mongo_success and not json_success:
        raise Exception(f"Failed to save data to both MongoDB and JSON for collection: {collection_name}")
    
    return {"mongodb": mongo_success, "json": json_success}