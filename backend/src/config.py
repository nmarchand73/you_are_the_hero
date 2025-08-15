"""
Configuration settings for the Interactive Story Game backend
"""

import os
from pathlib import Path

class Config:
    """Application configuration"""
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # File handling
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'epub'}
    
    # Directories
    BASE_DIR = Path(__file__).parent.parent
    DATA_FOLDER = BASE_DIR / 'data'
    DATABASE_FOLDER = BASE_DIR / 'database'
    EPUB_FOLDER = DATA_FOLDER / 'epubs'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'app.log'
    
    @classmethod
    def init_app(cls, app):
        """Initialize Flask app with config"""
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH
        app.config['DATA_FOLDER'] = str(cls.DATA_FOLDER)
        app.config['EPUB_FOLDER'] = str(cls.EPUB_FOLDER)