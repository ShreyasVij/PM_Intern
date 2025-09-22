# app/main.py
"""
Main application entry point
Replaces the old backend/app.py with better structure
"""

from flask import Flask
from flask_cors import CORS
from flask import request
import os

# Import configuration
from app.config import get_config

# Import utilities
from app.utils.logger import setup_logger, app_logger
from app.utils.error_handler import handle_api_error, handle_generic_error, APIError

# Import core components
from app.core.database import db_manager

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config = get_config()
    app.config.from_object(config)
    
    # Setup CORS with credentials support for sessions
    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)
    
    # Setup logging
    logger = setup_logger(level=config.LOG_LEVEL)
    app_logger.info(f"Starting PM Intern Recommender in {config_name} mode")
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {
            "error": "Not Found",
            "message": "The requested resource was not found.",
            "status_code": 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app_logger.error(f"Internal server error: {error}")
        return {
            "error": "Internal Server Error", 
            "message": "An internal server error occurred. Please try again later.",
            "status_code": 500
        }, 500
    
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(Exception, handle_generic_error)
    
    # Register API blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp)
    
    # Register legacy routes for backward compatibility (simplified)
    register_legacy_routes(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        db_healthy = db_manager.health_check()
        
        # Test new API endpoints
        api_status = "healthy"
        try:
            # Test if we can load internships
            from app.api.internships import get_internships
            result = get_internships()
            if result[1] != 200:
                api_status = "error"
        except Exception as e:
            app_logger.warning(f"API endpoint test failed: {e}")
            api_status = "error"
        
        status = "healthy" if db_healthy and api_status == "healthy" else "unhealthy"
        return {
            "status": status,
            "database": "connected" if db_healthy else "disconnected", 
            "api_endpoints": api_status,
            "version": "1.0.0"
        }, 200 if status == "healthy" else 503
    
    @app.route('/')
    def home():
        """Redirect root to the frontend UI"""
        from flask import redirect
        return redirect('/frontend/pages/index.html')
    
    # Static file serving for frontend
    @app.route('/frontend/<path:filename>')
    def serve_frontend(filename):
        """Serve frontend static files"""
        import os
        from flask import send_from_directory
        
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_dir, filename)
    
    # Redirect root to main page
    @app.route('/index.html')
    @app.route('/main')
    def index():
        """Redirect to main frontend page"""
        from flask import redirect
        return redirect('/frontend/pages/index.html')
    
    app_logger.info("Application initialized successfully")
    return app

def register_legacy_routes(app):
    """Register legacy routes for backward compatibility (redirects to new API)"""
    
    # Legacy authentication routes - redirect to new API
    @app.route('/signup', methods=['POST'])
    def legacy_signup():
        from app.api.auth import signup
        return signup()
    
    @app.route('/login', methods=['POST'])
    def legacy_login():
        from app.api.auth import login
        return login()
    
    @app.route('/logout', methods=['POST'])
    def legacy_logout():
        from app.api.auth import logout
        return logout()
    
    # Legacy profile routes - redirect to new API
    @app.route('/api/profile', methods=['POST', 'OPTIONS'])
    def legacy_create_profile():
        if request.method == 'OPTIONS':
            return '', 200
        from app.api.profiles import create_or_update_profile
        return create_or_update_profile()
    
    @app.route('/api/profiles/by_username/<username>', methods=['GET', 'OPTIONS'])
    def legacy_get_profile_by_username(username):
        if request.method == 'OPTIONS':
            return '', 200
        from app.api.profiles import get_profile_by_username
        return get_profile_by_username(username)
    
    @app.route('/api/profile/<candidate_id>', methods=['GET', 'OPTIONS'])
    def legacy_get_profile_by_candidate_id(candidate_id):
        if request.method == 'OPTIONS':
            return '', 200
        from app.api.profiles import get_profile_by_candidate_id
        return get_profile_by_candidate_id(candidate_id)
    
    app_logger.info("Simplified legacy routes registered for backward compatibility")

def run_app():
    """Run the application"""
    config = get_config()
    app = create_app()
    
    app_logger.info(f"Data folder in use: {config.DATA_DIR}")
    
    app.run(
        host='127.0.0.1',
        port=config.API_PORT,
        debug=config.FLASK_DEBUG
    )

if __name__ == '__main__':
    run_app()