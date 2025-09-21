# backend/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Database
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'internship_recommender')
    MONGODB_POOL_SIZE = int(os.getenv('MONGODB_POOL_SIZE', 10))
    # When true, the app will NOT read/write JSON fallbacks and will rely solely on MongoDB
    DISABLE_JSON_FALLBACK = os.getenv('DISABLE_JSON_FALLBACK', 'False').lower() == 'true'
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    API_PORT = int(os.getenv('API_PORT', 3000))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://127.0.0.1:5500,http://localhost:5500').split(',')
    
    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    PASSWORD_SALT_ROUNDS = int(os.getenv('PASSWORD_SALT_ROUNDS', 12))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    
    # Performance
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', 100))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Override with production-safe defaults
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    if not SECRET_KEY or SECRET_KEY == 'dev-secret-key-change-in-production':
        raise ValueError("SECRET_KEY must be set in production")
    
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
        raise ValueError("JWT_SECRET_KEY must be set in production")

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    DB_NAME = 'test_internship_recommender'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])