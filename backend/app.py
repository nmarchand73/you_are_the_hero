"""
Interactive Story Game - Flask Backend API

A clean, well-structured REST API server for interactive story games.
Uses Markdown-based human-in-the-loop workflow for reliable book processing.
"""

import logging
import argparse
import sys
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

class SSLHandshakeFilter(logging.Filter):
    """Filter out SSL handshake noise from logs"""
    def filter(self, record):
        # Filter out SSL handshake errors (they're just noise)
        message = record.getMessage()
        if any(pattern in message for pattern in [
            "\\x16\\x03\\x01",  # SSL/TLS handshake
            "Bad request version",
            "Invalid HTTP method",
            "Connection broken:",
            "[SSL: WRONG_VERSION_NUMBER]"
        ]):
            return False
        return True

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
    
    # Add SSL handshake filter to reduce log noise
    ssl_filter = SSLHandshakeFilter()
    logging.getLogger('werkzeug').addFilter(ssl_filter)
    
    create_directories(Config.DATA_FOLDER, Config.EPUB_FOLDER)
    
    # Initialize services
    services = {
        'epub_parser': EPUBParser(),
        'ink_converter': InkConverter(),
        'book_manager': BookManager(str(Config.DATA_FOLDER), str(Config.DATABASE_FOLDER))
    }
    
    # Register blueprints
    register_api_routes(app, services)
    register_error_handlers(app)
    
    # Use python app.py --index to manually index markdown reviews
    
    logger.info("Application initialized successfully")
    return app

def index_review_files(services, force=False, verbose=False):
    """
    Index markdown review files from the reviews directory
    
    New workflow:
    1. python scripts/epub_to_md.py book.epub    (Convert EPUB to reviewable Markdown) 
    2. Edit the .md file if needed to fix any issues
    3. python app.py --index                     (Index all reviews to database)
    
    This provides reliable results with the human-in-the-loop approach.
    """
    from pathlib import Path
    import re
    from datetime import datetime
    
    reviews_dir = Path(services['book_manager'].data_folder) / 'reviews'
    
    if not reviews_dir.exists():
        if verbose:
            print(f"Reviews directory not found: {reviews_dir}")
            print("Run scripts/epub_to_md.py first to generate review files.")
        return {
            "processed": 0,
            "errors": 0,
            "skipped": 0,
            "message": "No reviews directory found"
        }
    
    stats = {"processed": 0, "errors": 0, "skipped": 0, "books": []}
    
    # Find all markdown files
    md_files = list(reviews_dir.glob("*.md"))
    
    if verbose:
        print(f"Found {len(md_files)} markdown files to process...")
        print()
    
    for md_file in md_files:
        if verbose:
            print(f"Processing: {md_file.name}")
        
        try:
            # Parse markdown file
            book_data = parse_markdown_review(md_file)
            
            if not book_data:
                if verbose:
                    print(f"  ⚠️  Skipped (no valid content)")
                stats["skipped"] += 1
                continue
            
            # Check if book already exists - always override during indexation
            existing_book = services['book_manager'].get_book(book_data['id'])
            if existing_book:
                if verbose:
                    print(f"  🔄 Overriding existing book")
            elif verbose:
                print(f"  ➕ Adding new book")
            
            # Convert to Ink script
            ink_script = services['ink_converter'].convert_to_ink(book_data)
            
            # Save to database
            saved_book_id = services['book_manager'].save_book(book_data, ink_script)
            
            if verbose:
                print(f"  ✅ Indexed: {book_data['title']} ({book_data['total_sections']} sections)")
            
            stats["processed"] += 1
            stats["books"].append({
                "id": saved_book_id,
                "title": book_data['title'],
                "sections": book_data['total_sections']
            })
            
        except Exception as e:
            if verbose:
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
            stats["errors"] += 1
    
    return stats

def parse_markdown_review(md_file_path):
    """Parse a markdown review file into book data"""
    import re
    from datetime import datetime
    from pathlib import Path
    
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse frontmatter
    frontmatter = {}
    if content.startswith('---'):
        lines = content.split('\n')
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                content = '\n'.join(lines[i+1:])
                break
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                if value.isdigit():
                    value = int(value)
                frontmatter[key] = value
    
    # Parse sections
    sections = {}
    current_section = None
    current_content = []
    current_choices = []
    
    lines = content.split('\n')
    in_choices = False
    in_html_comment = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Handle HTML comments (multi-line)
        if '<!--' in line:
            in_html_comment = True
        if '-->' in line:
            in_html_comment = False
            continue  # Skip the line with closing -->
        if in_html_comment:
            continue  # Skip content inside HTML comments
        
        # Detect section headers
        section_match = re.match(r'^## (.+)$', line)
        if section_match:
            # Save previous section
            if current_section is not None:
                sections[current_section['id']] = {
                    'paragraph_number': current_section['id'],
                    'text': '\n'.join(current_content).strip(),
                    'choices': current_choices.copy(),
                    'combat': None
                }
            
            # Start new section
            section_title = section_match.group(1)
            
            # Extract section ID from title - keep everything as string
            id_match = re.search(r'Section (\d+)', section_title)
            if id_match:
                section_id = id_match.group(1)  # Keep as string
            else:
                # Handle special sections with manual tags
                if section_title in ['Title', 'Title page']:
                    section_id = 'title'
                elif section_title == 'Introduction':
                    section_id = 'intro'
                elif 'Rules' in section_title or 'Règles' in section_title:
                    section_id = 'rules'
                else:
                    # Generic special section, assign sequential ID as string
                    current_count = len([k for k in sections.keys() if isinstance(k, (int, str))])
                    section_id = str(current_count + 1)
            
            current_section = {'id': section_id, 'title': section_title}
            current_content = []
            current_choices = []
            in_choices = False
            continue
        
        # Detect choices section
        if line_stripped == '**Choices:**':
            in_choices = True
            continue
        
        # Detect section separator
        if line_stripped == '---':
            in_choices = False
            continue
        
        # Parse choices
        if in_choices and line_stripped.startswith('- ['):
            choice_match = re.match(r'- \[([^\]]+)\]\((#[^)]+)\)', line_stripped)
            if choice_match:
                choice_text = choice_match.group(1)
                choice_anchor = choice_match.group(2)
                
                # Extract destination from anchor
                dest_match = re.search(r'section-(\d+)', choice_anchor)
                if dest_match:
                    destination = dest_match.group(1)  # Keep as string
                    current_choices.append({
                        'text': choice_text,
                        'destination': destination
                    })
            continue
        
        # Add content - exclude review markers
        if current_section is not None and not in_choices:
            if (line_stripped and 
                not line_stripped.startswith('*No choices') and 
                not line_stripped.startswith('**Status:**') and
                not line_stripped.startswith('**ID:**') and
                not line_stripped.startswith('**Source:**')):
                current_content.append(line)
    
    # Save final section
    if current_section is not None:
        sections[current_section['id']] = {
            'paragraph_number': current_section['id'],
            'text': '\n'.join(current_content).strip(),
            'choices': current_choices.copy(),
            'combat': None
        }
    
    if not sections:
        return None
    
    # Generate book data
    book_title = frontmatter.get('title', Path(md_file_path).stem.replace('_review', ''))
    
    # Clean up title if it's from filename
    if book_title == Path(md_file_path).stem.replace('_review', ''):
        book_title = book_title.replace('_', ' ').replace('-', ' ').title()
    
    # Remove quotes and clean corrupted titles
    book_title = book_title.strip('"\'')
    if book_title.startswith('[CORRUPTED]') or book_title.startswith('Section inconnue'):
        # Try to get a better title from the filename
        filename_base = Path(md_file_path).stem.replace('_review', '')
        book_title = filename_base.replace('_', ' ').replace('-', ' ').title()
    
    book_id = re.sub(r'[^a-zA-Z0-9_-]', '_', book_title.lower().replace(' ', '_'))
    
    # Convert sections to proper format with numeric keys for numbered sections
    final_content = {}
    for section_id, section_data in sections.items():
        # Try to convert numeric section IDs to integers for compatibility
        if section_id.isdigit():
            final_key = int(section_id)
        else:
            # Keep special sections as strings (title, intro, rules)
            final_key = section_id
        
        # Also convert destination in choices to int if numeric
        final_choices = []
        for choice in section_data.get('choices', []):
            final_choice = choice.copy()
            dest = choice.get('destination')
            if isinstance(dest, str) and dest.isdigit():
                final_choice['destination'] = int(dest)
            final_choices.append(final_choice)
        
        final_content[final_key] = {
            'paragraph_number': final_key,
            'text': section_data['text'],
            'choices': final_choices,
            'combat': section_data.get('combat')
        }
    
    return {
        'id': book_id,
        'title': book_title,
        'author': 'Unknown Author',
        'content': final_content,
        'total_sections': len(final_content),
        'created_at': datetime.now().isoformat(),
        'original_filename': Path(md_file_path).name,
        'review_status': frontmatter.get('review_status', 'indexed'),
        'sections_found': frontmatter.get('sections_found', len(final_content))
    }


def register_api_routes(app, services):
    """Register all API routes"""
    
    # Static file serving routes
    @app.route('/')
    def serve_index():
        """Serve the main index.html file"""
        return send_file('../index.html')
    
    @app.route('/src/<path:filename>')
    def serve_static_src(filename):
        """Serve static files from src directory"""
        return send_from_directory('../src', filename)
    
    @app.route('/src/css/<path:filename>')
    def serve_css(filename):
        """Serve CSS files"""
        return send_from_directory('../src/css', filename)
    
    @app.route('/src/js/<path:filename>')
    def serve_js(filename):
        """Serve JavaScript files"""
        response = send_from_directory('../src/js', filename)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # API routes
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

    # Note: Book indexing is now CLI-only:
    # 1. python scripts/epub_to_md.py book.epub    (EPUB → Markdown)
    # 2. Edit the .md file in any editor  
    # 3. python app.py --index                     (Index reviews to database)
    
    @app.route('/api/reviews/scan')
    @handle_errors  
    def scan_reviews():
        """Scan review directory for Markdown files"""
        review_dir = os.path.join(services['config'].get('data_folder'), 'reviews')
        
        if not os.path.exists(review_dir):
            return jsonify({
                'success': True,
                'reviews': [],
                'message': f'Review directory not found: {review_dir}'
            })
        
        reviews = []
        for filename in os.listdir(review_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(review_dir, filename)
                
                try:
                    # Read status from file
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse basic info
                    status = 'unknown'
                    title = 'Unknown'
                    
                    if 'review_status: "completed"' in content:
                        status = 'completed'
                    elif 'review_status: "pending"' in content:
                        status = 'pending'
                    
                    # Extract title from frontmatter
                    if 'title: "' in content:
                        title_start = content.find('title: "') + 8
                        title_end = content.find('"', title_start)
                        if title_end > title_start:
                            title = content[title_start:title_end]
                    
                    reviews.append({
                        'filename': filename,
                        'filepath': filepath,
                        'title': title,
                        'status': status,
                        'size': os.path.getsize(filepath)
                    })
                    
                except Exception as e:
                    reviews.append({
                        'filename': filename,
                        'filepath': filepath,
                        'title': 'Error reading file',
                        'status': 'error',
                        'error': str(e)
                    })
        
        return jsonify({
            'success': True,
            'reviews': reviews,
            'message': f'Found {len(reviews)} review files'
        })

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
        from datetime import datetime
        
        # Create test book data directly
        test_book = {
            'id': 'test_adventure_001',
            'title': 'Test Adventure',
            'author': 'System Generator',
            'content': {
                1: {
                    'paragraph_number': 1,
                    'text': 'Vous vous réveillez dans une chambre inconnue. La lumière du matin filtre à travers les rideaux. Que faites-vous ?',
                    'choices': [
                        {'text': 'Sortir du lit et explorer', 'destination': 2},
                        {'text': 'Rester couché et réfléchir', 'destination': 3}
                    ],
                    'combat': None
                },
                2: {
                    'paragraph_number': 2,
                    'text': 'Vous sortez du lit. En explorant la pièce, vous découvrez une clé sur la table de nuit.',
                    'choices': [
                        {'text': 'Prendre la clé et ouvrir la porte', 'destination': 4},
                        {'text': 'Regarder par la fenêtre', 'destination': 5}
                    ],
                    'combat': None
                },
                3: {
                    'paragraph_number': 3,
                    'text': 'Vous restez allongé. Soudain, vous entendez des pas dans le couloir.',
                    'choices': [
                        {'text': 'Se lever rapidement', 'destination': 2},
                        {'text': 'Faire semblant de dormir', 'destination': 6}
                    ],
                    'combat': None
                },
                4: {
                    'paragraph_number': 4,
                    'text': 'La clé ouvre la porte. Vous vous trouvez dans un couloir sombre avec deux directions possibles.',
                    'choices': [
                        {'text': 'Aller à gauche', 'destination': 7},
                        {'text': 'Aller à droite', 'destination': 8}
                    ],
                    'combat': None
                },
                5: {
                    'paragraph_number': 5,
                    'text': 'Par la fenêtre, vous voyez un magnifique jardin. Vous avez trouvé un endroit paisible.',
                    'choices': [],
                    'combat': None
                },
                6: {
                    'paragraph_number': 6,
                    'text': 'Une personne entre et vous explique gentiment où vous êtes. Fin de votre aventure.',
                    'choices': [],
                    'combat': None
                },
                7: {
                    'paragraph_number': 7,
                    'text': 'Une bibliothèque remplie de livres anciens. Trésor de connaissances découvert !',
                    'choices': [],
                    'combat': None
                },
                8: {
                    'paragraph_number': 8,
                    'text': 'La cuisine avec un délicieux petit-déjeuner qui vous attend. Quelle belle découverte !',
                    'choices': [],
                    'combat': None
                }
            },
            'total_sections': 8,
            'created_at': datetime.now().isoformat(),
            'original_filename': 'test_generated.epub'
        }
        
        ink_script = services['ink_converter'].convert_to_ink(test_book)
        book_id = services['book_manager'].save_book(test_book, ink_script)
        
        return jsonify({
            'success': True,
            'message': 'Test book created successfully',
            'book_id': book_id,
            'book': {
                'id': book_id,
                'title': test_book['title'],
                'author': test_book['author'],
                'total_sections': test_book['total_sections'],
                'created_at': test_book['created_at']
            }
        })

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad requests including SSL handshake attempts"""
        # Don't log SSL handshake errors in detail (they're just noise)
        logger.debug(f"Bad request (possibly SSL handshake): {type(error).__name__}")
        return jsonify({
            'success': False,
            'error': 'Bad request'
        }), 400

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

def run_indexation_mode(force=False):
    """Run indexation mode to process markdown reviews"""
    print("REVIEW INDEXATION MODE")
    print("=" * 50)
    print("This will index all markdown files from backend/data/reviews/")
    print()
    print("Workflow:")
    print("1. python scripts/epub_to_md.py book.epub    (Convert EPUB to Markdown)")
    print("2. Edit the .md file if needed to fix issues")
    print("3. python app.py --index                     (Index reviews to database)")
    print("=" * 50)
    
    # Initialize services without Flask app
    setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
    create_directories(Config.DATA_FOLDER, Config.EPUB_FOLDER)
    
    services = {
        'epub_parser': EPUBParser(),
        'ink_converter': InkConverter(),
        'book_manager': BookManager(str(Config.DATA_FOLDER), str(Config.DATABASE_FOLDER))
    }
    
    print(f"Data folder: {Config.DATA_FOLDER}")
    print(f"Reviews folder: {Config.DATA_FOLDER}/reviews")
    print("")
    
    # Run indexation with force and verbose
    stats = index_review_files(services, force=force, verbose=True)
    
    print("")
    print("INDEXATION COMPLETE")
    print("=" * 50)
    print(f"Processed: {stats['processed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    
    if stats['processed'] > 0:
        print("")
        print("📚 Successfully indexed books:")
        for book_info in stats['books']:
            print(f"  - {book_info['title']} ({book_info['sections']} sections)")
    
    # Show total library stats
    all_books = services['book_manager'].get_all_books()
    print(f"")
    print(f"Total books in library: {len(all_books)}")
    
    if len(all_books) > len(stats['books']):
        print("")
        print("📖 All books in library:")
        for book in all_books:
            print(f"  - {book['title']} by {book['author']} ({book['total_sections']} sections)")

def run_test_mode():
    """Create a test book for development"""
    print("TEST BOOK CREATION MODE")
    print("=" * 50)
    
    # Initialize services without Flask app
    setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
    create_directories(Config.DATA_FOLDER, Config.EPUB_FOLDER)
    
    services = {
        'epub_parser': EPUBParser(),
        'ink_converter': InkConverter(),
        'book_manager': BookManager(str(Config.DATA_FOLDER), str(Config.DATABASE_FOLDER))
    }
    
    from datetime import datetime
    
    # Create test book data directly
    test_book = {
        'id': 'test_adventure_001',
        'title': 'Test Adventure',
        'author': 'System Generator',
        'content': {
            1: {
                'paragraph_number': 1,
                'text': 'Vous vous réveillez dans une chambre inconnue. La lumière du matin filtre à travers les rideaux. Que faites-vous ?',
                'choices': [
                    {'text': 'Sortir du lit et explorer', 'destination': 2},
                    {'text': 'Rester couché et réfléchir', 'destination': 3}
                ],
                'combat': None
            },
            2: {
                'paragraph_number': 2,
                'text': 'Vous sortez du lit. En explorant la pièce, vous découvrez une clé sur la table de nuit.',
                'choices': [
                    {'text': 'Prendre la clé et ouvrir la porte', 'destination': 4},
                    {'text': 'Regarder par la fenêtre', 'destination': 5}
                ],
                'combat': None
            },
            3: {
                'paragraph_number': 3,
                'text': 'Vous restez allongé. Soudain, vous entendez des pas dans le couloir.',
                'choices': [
                    {'text': 'Se lever rapidement', 'destination': 2},
                    {'text': 'Faire semblant de dormir', 'destination': 6}
                ],
                'combat': None
            },
            4: {
                'paragraph_number': 4,
                'text': 'La clé ouvre la porte. Vous vous trouvez dans un couloir sombre avec deux directions possibles.',
                'choices': [
                    {'text': 'Aller à gauche', 'destination': 7},
                    {'text': 'Aller à droite', 'destination': 8}
                ],
                'combat': None
            },
            5: {
                'paragraph_number': 5,
                'text': 'Par la fenêtre, vous voyez un magnifique jardin. Vous avez trouvé un endroit paisible.',
                'choices': [],
                'combat': None
            },
            6: {
                'paragraph_number': 6,
                'text': 'Une personne entre et vous explique gentiment où vous êtes. Fin de votre aventure.',
                'choices': [],
                'combat': None
            },
            7: {
                'paragraph_number': 7,
                'text': 'Une bibliothèque remplie de livres anciens. Trésor de connaissances découvert !',
                'choices': [],
                'combat': None
            },
            8: {
                'paragraph_number': 8,
                'text': 'La cuisine avec un délicieux petit-déjeuner qui vous attend. Quelle belle découverte !',
                'choices': [],
                'combat': None
            }
        },
        'total_sections': 8,
        'created_at': datetime.now().isoformat(),
        'original_filename': 'test_generated.epub'
    }
    
    print("Creating test book...")
    
    try:
        ink_script = services['ink_converter'].convert_to_ink(test_book)
        book_id = services['book_manager'].save_book(test_book, ink_script)
        
        print(f"SUCCESS: Test book created with ID: {book_id}")
        print(f"Title: {test_book['title']}")
        print(f"Author: {test_book['author']}")
        print(f"Sections: {test_book['total_sections']}")
        
    except Exception as e:
        print(f"ERROR: Failed to create test book: {e}")
        import traceback
        traceback.print_exc()

def run_clean_mode(auto_confirm=False):
    """Run database cleanup mode"""
    print("DATABASE CLEANUP MODE")
    print("=" * 50)
    print("⚠️  WARNING: This will permanently delete ALL books, saves, and ink scripts!")
    print("=" * 50)
    
    # Initialize services without Flask app
    setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
    create_directories(Config.DATA_FOLDER, Config.EPUB_FOLDER)
    
    book_manager = BookManager(str(Config.DATA_FOLDER), str(Config.DATABASE_FOLDER))
    
    # Show current stats
    stats = book_manager.get_storage_stats()
    print(f"Current database status:")
    print(f"  - Total books: {stats['total_books']}")
    print(f"  - Total saves: {stats['total_saves']}")
    print(f"  - Storage used: {stats['storage_used_mb']} MB")
    print("")
    
    if stats['total_books'] == 0:
        print("✅ Database is already empty!")
        return
    
    # Confirmation
    if not auto_confirm:
        print("Are you sure you want to delete ALL data? This cannot be undone!")
        response = input("Type 'YES' to confirm (case sensitive): ")
        if response != 'YES':
            print("❌ Cleanup cancelled")
            return
    else:
        print("🤖 Auto-confirm enabled, proceeding with cleanup...")
    
    print("")
    print("🗑️  Starting database cleanup...")
    
    try:
        cleanup_stats = book_manager.clean_database(confirm=True)
        
        print("")
        print("✅ DATABASE CLEANUP COMPLETED")
        print("=" * 50)
        print(f"Books deleted: {cleanup_stats['books_deleted']}")
        print(f"Saves deleted: {cleanup_stats['saves_deleted']}")
        print(f"Ink scripts deleted: {cleanup_stats['ink_scripts_deleted']}")
        print(f"Data files deleted: {cleanup_stats['data_files_deleted']}")
        
        if cleanup_stats['errors']:
            print(f"⚠️  Errors encountered: {len(cleanup_stats['errors'])}")
            for error in cleanup_stats['errors']:
                print(f"  - {error}")
        
        # Show final stats
        final_stats = book_manager.get_storage_stats()
        print(f"")
        print(f"Final status:")
        print(f"  - Remaining books: {final_stats['total_books']}")
        print(f"  - Remaining saves: {final_stats['total_saves']}")
        print(f"  - Storage used: {final_stats['storage_used_mb']} MB")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()

def run_verify_mode():
    """Run database integrity verification"""
    print("DATABASE INTEGRITY VERIFICATION")
    print("=" * 50)
    
    # Initialize services without Flask app
    setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
    create_directories(Config.DATA_FOLDER, Config.EPUB_FOLDER)
    
    book_manager = BookManager(str(Config.DATA_FOLDER), str(Config.DATABASE_FOLDER))
    
    print("🔍 Checking database integrity...")
    print("")
    
    try:
        report = book_manager.verify_database_integrity()
        
        print("📊 INTEGRITY REPORT")
        print("=" * 50)
        print(f"Total books in index: {report['total_books']}")
        print(f"Valid books: {report['valid_books']}")
        print("")
        
        # Issues found
        issues_found = False
        
        if report['missing_data_files']:
            issues_found = True
            print(f"❌ Missing data files ({len(report['missing_data_files'])}):")
            for book_id in report['missing_data_files']:
                print(f"  - {book_id}")
            print("")
        
        if report['missing_ink_scripts']:
            issues_found = True
            print(f"❌ Missing ink scripts ({len(report['missing_ink_scripts'])}):")
            for book_id in report['missing_ink_scripts']:
                print(f"  - {book_id}")
            print("")
        
        if report['corrupted_books']:
            issues_found = True
            print(f"❌ Corrupted books ({len(report['corrupted_books'])}):")
            for book_info in report['corrupted_books']:
                print(f"  - {book_info}")
            print("")
        
        if report['orphaned_saves']:
            issues_found = True
            print(f"⚠️  Orphaned save files ({len(report['orphaned_saves'])}):")
            for filename in report['orphaned_saves']:
                print(f"  - {filename}")
            print("")
        
        if report['orphaned_ink_scripts']:
            issues_found = True
            print(f"⚠️  Orphaned ink scripts ({len(report['orphaned_ink_scripts'])}):")
            for filename in report['orphaned_ink_scripts']:
                print(f"  - {filename}")
            print("")
        
        if report['orphaned_data_files']:
            issues_found = True
            print(f"⚠️  Orphaned data files ({len(report['orphaned_data_files'])}):")
            for filename in report['orphaned_data_files']:
                print(f"  - {filename}")
            print("")
        
        if not issues_found:
            print("✅ Database integrity is PERFECT!")
            print("All books have valid data files and ink scripts.")
            print("No orphaned files found.")
        else:
            print("💡 Suggestions:")
            print("  - Use --clean to remove all data and start fresh")
            print("  - Use --index to re-process EPUBs and fix missing files")
        
        # Storage stats
        stats = book_manager.get_storage_stats()
        print("")
        print("📈 STORAGE STATISTICS")
        print("=" * 30)
        print(f"Total books: {stats['total_books']}")
        print(f"Total saves: {stats['total_saves']}")
        print(f"Storage used: {stats['storage_used_mb']} MB")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Interactive Story Game Backend')
    parser.add_argument('--index', '-i', action='store_true', 
                        help='Run indexation mode to process all EPUBs')
    parser.add_argument('--test', '-t', action='store_true',
                        help='Create a test book for development')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force re-indexation of already processed EPUBs')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean database (remove all books, saves, and ink scripts)')
    parser.add_argument('--verify', '-v', action='store_true',
                        help='Verify database integrity')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Auto-confirm dangerous operations (use with caution)')
    
    args = parser.parse_args()
    
    if args.index:
        run_indexation_mode(force=args.force)
        return
        
    if args.test:
        run_test_mode()
        return
        
    if args.clean:
        run_clean_mode(auto_confirm=args.yes)
        return
        
    if args.verify:
        run_verify_mode()
        return
    
    # Normal server mode
    app = create_app()
    
    print("Interactive Story Game Backend")
    print(f"EPUB folder: {Config.EPUB_FOLDER}")
    print(f"Data folder: {Config.DATA_FOLDER}")
    print(f"Server starting on http://{Config.HOST}:{Config.PORT}")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )

if __name__ == '__main__':
    main()