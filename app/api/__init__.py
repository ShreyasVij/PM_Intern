# app/api/__init__.py
"""
API Blueprint Package
Contains all API endpoint modules
"""

from flask import Blueprint
from app.api.internships import get_internships
from app.api.recommendations import get_candidate_recommendations, get_internship_recommendations
from app.api.auth import signup, login, logout, check_login_status
from app.api.profiles import create_or_update_profile, get_profile_by_username, get_profile_by_candidate_id
from app.api.cities import list_cities
from app.api.admin import db_stats

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register internship routes
@api_bp.route('/internships', methods=['GET'])
def internships_endpoint():
    """Get all internships"""
    return get_internships()

# Register cities route
@api_bp.route('/cities', methods=['GET'])
def cities_endpoint():
    """Get list of cities for dropdown"""
    return list_cities()

# Register recommendation routes
@api_bp.route('/recommendations/<candidate_id>', methods=['GET'])
def candidate_recommendations_endpoint(candidate_id):
    """Get recommendations for a candidate"""
    return get_candidate_recommendations(candidate_id)

@api_bp.route('/recommendations/by_internship/<internship_id>', methods=['GET'])
def internship_recommendations_endpoint(internship_id):
    """Get similar internships"""
    return get_internship_recommendations(internship_id)

# Register authentication routes
@api_bp.route('/auth/signup', methods=['POST'])
def signup_endpoint():
    """User registration"""
    return signup()

@api_bp.route('/auth/login', methods=['POST'])
def login_endpoint():
    """User login"""
    return login()

@api_bp.route('/auth/logout', methods=['POST'])
def logout_endpoint():
    """User logout"""
    return logout()

@api_bp.route('/auth/status', methods=['GET'])
def login_status_endpoint():
    """Check login status"""
    return check_login_status()

# Register profile management routes
@api_bp.route('/profile', methods=['POST'])
def create_profile_endpoint():
    """Create or update user profile"""
    return create_or_update_profile()

@api_bp.route('/profiles/by_username/<username>', methods=['GET'])
def get_profile_by_username_endpoint(username):
    """Get profile by username"""
    return get_profile_by_username(username)

@api_bp.route('/profile/<candidate_id>', methods=['GET'])
def get_profile_by_candidate_id_endpoint(candidate_id):
    """Get profile by candidate ID"""
    return get_profile_by_candidate_id(candidate_id)

# Admin/diagnostics routes
@api_bp.route('/admin/db-stats', methods=['GET'])
def admin_db_stats_endpoint():
    """Basic DB stats for quick verification"""
    return db_stats()