# app/config.py
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass

class Config:
    """Base configuration class."""
    
    # Database
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'internship_recommender')
    MONGODB_POOL_SIZE = int(os.getenv('MONGODB_POOL_SIZE', 10))
    # Atlas-only toggle (no JSON fallbacks)
    DISABLE_JSON_FALLBACK = os.getenv('DISABLE_JSON_FALLBACK', 'False').lower() == 'true'
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    API_PORT = int(os.getenv('API_PORT', 3000))
    
    # CORS
    # Include common localhost ports by default; can be overridden via env
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500'
    ).split(',')
    
    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    PASSWORD_SALT_ROUNDS = int(os.getenv('PASSWORD_SALT_ROUNDS', 12))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))

    # Flask session cookie settings (tuned for local dev)
    SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'pm_session')
    SESSION_COOKIE_HTTPONLY = True
    # Use Lax for same-site requests; for cross-site you would need 'None' + HTTPS
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT
    
    # Performance
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', 100))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Paths (updated for new structure)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to project root
    DATA_DIR = os.path.join(BASE_DIR, "data")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Override with production-safe defaults (validated in get_config)
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

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
    """Get configuration based on environment.

    We defer production-only validation to runtime when selecting ProductionConfig,
    so importing this module in development/testing won't fail.
    """
    env = os.getenv('FLASK_ENV', 'development')
    cfg = config.get(env, config['default'])
    if env == 'production':
        secret_key = os.getenv('SECRET_KEY')
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not secret_key or secret_key == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production")
        if not jwt_secret or jwt_secret == 'jwt-secret-key-change-in-production':
            raise ValueError("JWT_SECRET_KEY must be set in production")
    return cfg