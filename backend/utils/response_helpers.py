# backend/utils/response_helpers.py
from flask import jsonify
from datetime import datetime
import json

class APIResponse:
    """Standardized API response helper."""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200, meta=None):
        """Create a successful response."""
        response_data = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code
        }
        
        if data is not None:
            response_data["data"] = data
            
        if meta is not None:
            response_data["meta"] = meta
            
        response = jsonify(response_data)
        response.status_code = status_code
        return response
    
    @staticmethod
    def error(message="An error occurred", status_code=400, errors=None, error_code=None):
        """Create an error response."""
        response_data = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code
        }
        
        if errors is not None:
            response_data["errors"] = errors
            
        if error_code is not None:
            response_data["error_code"] = error_code
            
        response = jsonify(response_data)
        response.status_code = status_code
        return response
    
    @staticmethod
    def paginated(data, page=1, per_page=10, total=0, message="Success"):
        """Create a paginated response."""
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        meta = {
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        return APIResponse.success(data=data, message=message, meta=meta)

class DataEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB ObjectId and other types."""
    
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)