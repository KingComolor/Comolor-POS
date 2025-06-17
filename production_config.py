# Production Configuration for Comolor POS
import os
from urllib.parse import urlparse

class ProductionConfig:
    """Production database configuration"""
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/comolor_pos_production'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30,
        'pool_timeout': 30,
        'echo': False  # Set to True for SQL debugging
    }
    
    # Security Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-change-this'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # MPesa Configuration
    MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'production')
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY')
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/comolor-pos/app.log'
    
    # Performance Settings
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = '/var/uploads/comolor-pos'
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'MPESA_CONSUMER_KEY',
            'MPESA_CONSUMER_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Database Connection String Examples
DATABASE_EXAMPLES = {
    'digitalocean': 'postgresql://username:password@db-postgresql-sgp1-12345-do-user-123456-0.b.db.ondigitalocean.com:25060/comolor_pos?sslmode=require',
    'aws_rds': 'postgresql://admin:password@comolor-pos.abc123.us-east-1.rds.amazonaws.com:5432/comolor_pos',
    'google_cloud': 'postgresql://postgres:password@35.123.456.789:5432/comolor_pos',
    'heroku': 'postgres://user:password@ec2-123-456-789.compute-1.amazonaws.com:5432/database_name',
    'local': 'postgresql://postgres:password@localhost:5432/comolor_pos_production'
}