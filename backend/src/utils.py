"""
Utility functions for the Interactive Story Game backend
"""

import os
import logging
from pathlib import Path
from functools import wraps
from flask import jsonify

def setup_logging(log_file, log_level='INFO'):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def create_directories(*directories):
    """Create directories if they don't exist"""
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    """Check if filename has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def handle_errors(f):
    """Decorator to handle API errors consistently"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logging.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except FileNotFoundError as e:
            logging.warning(f"Not found error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404
        except Exception as e:
            logging.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    return decorated_function

def validate_book_id(book_id):
    """Validate book ID format"""
    if not book_id or not isinstance(book_id, str):
        raise ValueError("Invalid book ID")
    
    if len(book_id) < 8 or len(book_id) > 32:
        raise ValueError("Book ID must be between 8 and 32 characters")
    
    if not book_id.replace('_', '').isalnum():
        raise ValueError("Book ID contains invalid characters")

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"