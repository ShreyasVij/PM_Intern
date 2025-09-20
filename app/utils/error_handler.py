# app/utils/error_handler.py
from flask import jsonify, request
from functools import wraps
import traceback

# Try to import logger, fallback to print
try:
    from app.utils.logger import app_logger
    log_warning = app_logger.warning
    log_error = app_logger.error
except ImportError:
    log_warning = print
    log_error = print

class APIError(Exception):
    """Custom API exception class."""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv

def handle_api_error(error):
    """Handle APIError exceptions."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    log_warning(f"API Error: {error.message} - Status: {error.status_code}")
    return response

def handle_generic_error(error):
    """Handle generic exceptions."""
    log_error(f"Unhandled error: {str(error)}\n{traceback.format_exc()}")
    response = jsonify({
        'error': 'Internal server error',
        'status_code': 500
    })
    response.status_code = 500
    return response

def validate_json(required_fields=None):
    """Decorator to validate JSON request data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                raise APIError('Request must be JSON', 400)
            
            data = request.get_json()
            if not data:
                raise APIError('Request body cannot be empty', 400)
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise APIError(f'Missing required fields: {", ".join(missing_fields)}', 400)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def handle_database_error(operation):
    """Decorator to handle database operations."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                log_error(f"Database error in {operation}: {str(e)}")
                raise APIError(f'Database operation failed: {operation}', 500)
        return decorated_function
    return decorator