# app/api/internships.py
"""
Internships API endpoints
Direct implementation to replace legacy imports
"""

from flask import jsonify
from app.core.database import db_manager
from app.utils.logger import app_logger
from app.utils.response_helpers import success_response, error_response

def get_internships():
    """Get all internships"""
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
                
                app_logger.info(f"Retrieved {len(internships)} internships from MongoDB")
                return success_response({"internships": internships})
            except Exception as e:
                app_logger.warning(f"MongoDB query failed: {e}")
        
        # Fall back to JSON file
        import json
        import os
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        internships_file = os.path.join(data_dir, 'internships.json')
        
        if os.path.exists(internships_file):
            with open(internships_file, 'r') as f:
                internships = json.load(f)
            
            app_logger.info(f"Retrieved {len(internships)} internships from JSON file")
            return success_response({"internships": internships})
        else:
            app_logger.error("No internships data found")
            return error_response("No internships data available", 404)
            
    except Exception as e:
        app_logger.error(f"Error retrieving internships: {e}")
        return error_response("Failed to retrieve internships", 500)


def get_internship_by_id(internship_id):
    """Get specific internship by ID"""
    try:
        # Try MongoDB first
        db = db_manager.get_db()
        if db is not None:
            try:
                internship = db.internships.find_one({"internship_id": internship_id})
                if internship:
                    if '_id' in internship:
                        internship['_id'] = str(internship['_id'])
                    return success_response({"internship": internship})
            except Exception as e:
                app_logger.warning(f"MongoDB query failed: {e}")
        
        # Fall back to JSON file
        import json
        import os
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        internships_file = os.path.join(data_dir, 'internships.json')
        
        if os.path.exists(internships_file):
            with open(internships_file, 'r') as f:
                internships = json.load(f)
            
            internship = next((i for i in internships if i.get("internship_id") == internship_id), None)
            if internship:
                return success_response({"internship": internship})
        
        return error_response("Internship not found", 404)
            
    except Exception as e:
        app_logger.error(f"Error retrieving internship {internship_id}: {e}")
        return error_response("Failed to retrieve internship", 500)