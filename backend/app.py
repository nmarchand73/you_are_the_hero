"""
Interactive Story Game - Flask Backend API

A clean, well-structured REST API server for processing EPUB gamebooks.
"""

import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.epub_parser import EPUBParser
from src.ink_converter import InkConverter
from src.book_manager import BookManager
from src.config import Config
from src.utils import (
    setup_logging, 
    create_directories, 
    handle_errors, 
    allowed_file, 
    validate_book_id
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    # Configure app
    Config.init_app(app)
    setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
    create_directories(Config.UPLOAD_FOLDER, Config.DATA_FOLDER)
    
    # Initialize services
    services = {
        'epub_parser': EPUBParser(),
        'ink_converter': InkConverter(),
        'book_manager': BookManager(str(Config.DATA_FOLDER))
    }
    
    # Register blueprints
    register_api_routes(app, services)
    register_error_handlers(app)
    
    logger.info("Application initialized successfully")
    return app

def register_api_routes(app, services):
    """Register all API routes"""
    
    @app.route('/api/health')
    @handle_errors
    def health_check():
        """System health check"""
        return jsonify({
            'status': 'ok',
            'message': 'Interactive Story Game Backend',
            'timestamp': datetime.now().isoformat()
        })

    @app.route('/api/books')
    @handle_errors
    def get_books():
        """Get all books"""
        books = services['book_manager'].get_all_books()
        return jsonify({
            'success': True,
            'books': books,
            'count': len(books)
        })

    @app.route('/api/books/<book_id>')
    @handle_errors
    def get_book(book_id):
        """Get specific book"""
        validate_book_id(book_id)
        book = services['book_manager'].get_book(book_id)
        
        if not book:
            return jsonify({
                'success': False,
                'error': 'Book not found'
            }), 404
        
        return jsonify({
            'success': True,
            'book': book
        })

    @app.route('/api/books/<book_id>/ink')
    @handle_errors
    def get_ink_script(book_id):
        """Get book's ink script"""
        validate_book_id(book_id)
        ink_script = services['book_manager'].get_ink_script(book_id)
        
        if not ink_script:
            return jsonify({
                'success': False,
                'error': 'Ink script not found'
            }), 404
        
        return jsonify({
            'success': True,
            'ink_script': ink_script
        })

    @app.route('/api/books/<book_id>', methods=['DELETE'])
    @handle_errors
    def delete_book(book_id):
        """Delete a book"""
        validate_book_id(book_id)
        success = services['book_manager'].delete_book(book_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Book not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Book deleted successfully'
        })

    @app.route('/api/upload', methods=['POST'])
    @handle_errors
    def upload_epub():
        """Upload and process EPUB file"""
        # Validate request
        if 'file' not in request.files:
            raise ValueError('No file provided')
        
        file = request.files['file']
        if not file.filename:
            raise ValueError('No file selected')
        
        if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
            raise ValueError('Only EPUB files are allowed')
        
        # Process file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = Config.UPLOAD_FOLDER / unique_filename
        
        try:
            # Save uploaded file
            file.save(str(file_path))
            logger.info(f"Processing EPUB: {filename}")
            
            # Parse and convert
            book_data = services['epub_parser'].parse_epub(str(file_path))
            ink_script = services['ink_converter'].convert_to_ink(book_data)
            
            # Validate
            validation = services['ink_converter'].validate_ink_script(ink_script)
            if not validation['is_valid']:
                raise ValueError(f"Ink conversion failed: {', '.join(validation['errors'])}")
            
            # Save book
            book_id = services['book_manager'].save_book(book_data, ink_script)
            
            return jsonify({
                'success': True,
                'message': f'Book "{book_data["title"]}" processed successfully',
                'book_id': book_id,
                'book': {
                    'id': book_id,
                    'title': book_data['title'],
                    'author': book_data['author'],
                    'total_sections': book_data['total_sections'],
                    'created_at': book_data['created_at']
                },
                'validation': validation
            })
            
        finally:
            # Cleanup
            if file_path.exists():
                file_path.unlink()

    @app.route('/api/saves/<book_id>')
    @handle_errors
    def get_save(book_id):
        """Get save data"""
        validate_book_id(book_id)
        save_data = services['book_manager'].get_save_data(book_id)
        return jsonify({
            'success': True,
            'save_data': save_data
        })

    @app.route('/api/saves/<book_id>', methods=['POST'])
    @handle_errors
    def save_game(book_id):
        """Save game state"""
        validate_book_id(book_id)
        save_data = request.get_json()
        
        if not save_data:
            raise ValueError('No save data provided')
        
        success = services['book_manager'].save_game_state(book_id, save_data)
        if not success:
            raise RuntimeError('Failed to save game state')
        
        return jsonify({
            'success': True,
            'message': 'Game saved successfully'
        })

    @app.route('/api/saves/<book_id>', methods=['DELETE'])
    @handle_errors
    def delete_save(book_id):
        """Delete save data"""
        validate_book_id(book_id)
        success = services['book_manager'].delete_save_data(book_id)
        return jsonify({
            'success': True,
            'message': 'Save data deleted' if success else 'No save data found'
        })

    @app.route('/api/test/simple-book', methods=['POST'])
    @handle_errors
    def create_test_book():
        """Create test book for development"""
        from src.test_data import create_simple_test_book
        
        book_data = create_simple_test_book()
        ink_script = services['ink_converter'].convert_to_ink(book_data)
        book_id = services['book_manager'].save_book(book_data, ink_script)
        
        return jsonify({
            'success': True,
            'message': 'Test book created successfully',
            'book_id': book_id,
            'book': {
                'id': book_id,
                'title': book_data['title'],
                'author': book_data['author'],
                'total_sections': book_data['total_sections'],
                'created_at': book_data['created_at']
            }
        })

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            'success': False,
            'error': f'File too large. Maximum size is {Config.MAX_CONTENT_LENGTH // (1024*1024)}MB.'
        }), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def main():
    """Main entry point"""
    app = create_app()
    
    print("Interactive Story Game Backend")
    print(f"Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"Data folder: {Config.DATA_FOLDER}")
    print(f"Server starting on http://{Config.HOST}:{Config.PORT}")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )

if __name__ == '__main__':
    main()