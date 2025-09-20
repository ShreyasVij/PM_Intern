# app/api/auth.py
"""
Authentication API endpoints
Handles user registration, login, and profile management
"""

from flask import request, jsonify, session
from app.core.database import db_manager
from app.utils.logger import app_logger
from app.utils.response_helpers import success_response, error_response
import hashlib
import json
import os

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return error_response("Username and password are required", 400)
        
        if len(username) < 3:
            return error_response("Username must be at least 3 characters", 400)
        
        if len(password) < 6:
            return error_response("Password must be at least 6 characters", 400)
        
        # Check if user already exists
        db = db_manager.get_db()
        if db is not None:
            try:
                existing_user = db.login_info.find_one({"username": username})
                if existing_user:
                    return error_response("Username already exists", 409)
            except Exception as e:
                app_logger.warning(f"MongoDB user check failed: {e}")
        
        # Also check JSON file for existing users
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        login_file = os.path.join(data_dir, 'login_info.json')
        
        existing_users = []
        if os.path.exists(login_file):
            try:
                with open(login_file, 'r') as f:
                    existing_users = json.load(f)
            except Exception as e:
                app_logger.warning(f"Failed to read login file: {e}")
                existing_users = []
        
        # Check if username exists in JSON
        for user in existing_users:
            if user.get('username') == username:
                return error_response("Username already exists", 409)
        
        # Create new user
        hashed_password = hash_password(password)
        new_user = {
            "username": username,
            "password": hashed_password
        }
        
        # Save to MongoDB if available
        if db is not None:
            try:
                db.login_info.insert_one(new_user.copy())
                app_logger.info(f"User {username} saved to MongoDB")
            except Exception as e:
                app_logger.warning(f"Failed to save user to MongoDB: {e}")
        
        # Save to JSON file as backup
        try:
            existing_users.append(new_user)
            with open(login_file, 'w') as f:
                json.dump(existing_users, f, indent=2)
            app_logger.info(f"User {username} saved to JSON file")
        except Exception as e:
            app_logger.error(f"Failed to save user to JSON: {e}")
            return error_response("Failed to create user", 500)
        
        return success_response(
            {"username": username, "message": "User created successfully"},
            "Registration successful"
        )
        
    except Exception as e:
        app_logger.error(f"Signup error: {e}")
        return error_response("Internal server error during registration", 500)

def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return error_response("Username and password are required", 400)
        
        hashed_password = hash_password(password)
        
        # Check MongoDB first
        user_found = False
        db = db_manager.get_db()
        if db is not None:
            try:
                user = db.login_info.find_one({"username": username, "password": hashed_password})
                if user:
                    user_found = True
            except Exception as e:
                app_logger.warning(f"MongoDB login check failed: {e}")
        
        # Check JSON file if not found in MongoDB
        if not user_found:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            login_file = os.path.join(data_dir, 'login_info.json')
            
            if os.path.exists(login_file):
                try:
                    with open(login_file, 'r') as f:
                        users = json.load(f)
                    
                    for user in users:
                        if user.get('username') == username and user.get('password') == hashed_password:
                            user_found = True
                            break
                except Exception as e:
                    app_logger.warning(f"Failed to read login file: {e}")
        
        if not user_found:
            return error_response("Invalid username or password", 401)
        
        # Set session
        session['username'] = username
        session['logged_in'] = True
        
        app_logger.info(f"User {username} logged in successfully")
        
        return success_response(
            {"username": username, "logged_in": True},
            "Login successful"
        )
        
    except Exception as e:
        app_logger.error(f"Login error: {e}")
        return error_response("Internal server error during login", 500)

def logout():
    """User logout endpoint"""
    try:
        username = session.get('username', 'Unknown')
        session.clear()
        
        app_logger.info(f"User {username} logged out")
        
        return success_response(
            {"message": "Logged out successfully"},
            "Logout successful"
        )
        
    except Exception as e:
        app_logger.error(f"Logout error: {e}")
        return error_response("Internal server error during logout", 500)

def check_login_status():
    """Check if user is logged in"""
    try:
        logged_in = session.get('logged_in', False)
        username = session.get('username', None)
        
        return success_response({
            "logged_in": logged_in,
            "username": username
        })
        
    except Exception as e:
        app_logger.error(f"Login status check error: {e}")
        return error_response("Failed to check login status", 500)