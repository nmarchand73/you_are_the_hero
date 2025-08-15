"""
Book Manager for Interactive Story Game
Handles book storage, retrieval, and save game management
"""

import os
import json
import uuid
from datetime import datetime
# Human review tools removed - using direct markdown workflow

class BookManager:
    def __init__(self, data_folder, database_folder=None):
        self.data_folder = data_folder
        
        # Separate database and working files
        if database_folder is None:
            database_folder = os.path.join(os.path.dirname(data_folder), 'database')
        self.database_folder = database_folder
        
        # Database files (sensitive data)
        self.books_file = os.path.join(database_folder, 'books.json')
        self.saves_folder = os.path.join(database_folder, 'saves')
        self.ink_folder = os.path.join(database_folder, 'ink_scripts')
        
        # Working files (non-sensitive)
        self.review_folder = os.path.join(data_folder, 'reviews')
        
        # Ensure directories exist
        os.makedirs(database_folder, exist_ok=True)
        os.makedirs(self.saves_folder, exist_ok=True)
        os.makedirs(self.ink_folder, exist_ok=True)
        os.makedirs(self.review_folder, exist_ok=True)
        
        # Human review tools removed - using direct markdown workflow
        
        # Initialize books index if it doesn't exist
        if not os.path.exists(self.books_file):
            self._save_books_index({})

# Removed old EPUB parsing stats - no longer needed with MD workflow
    
    def save_book(self, book_data, ink_script):
        """
        Save book data and ink script
        
        Args:
            book_data (dict): Book data
            ink_script (str): Generated ink script
            
        Returns:
            str: Book ID
        """
        book_id = book_data['id']
        
        # Load existing books
        books_index = self._load_books_index()
        
        # Create book entry
        book_entry = {
            'id': book_id,
            'title': book_data['title'],
            'author': book_data['author'],
            'total_sections': book_data['total_sections'],
            'created_at': book_data['created_at'],
            'original_filename': book_data.get('original_filename', 'unknown.epub'),
            'cover': book_data.get('cover'),
            'last_played': None,
            'last_section': None
        }
        
        # Add parsing method (now always human-reviewed from MD files)
        book_entry['parsing_method'] = book_data.get('parsing_method', 'human_reviewed_markdown')
        
        # Save book metadata to index
        books_index[book_id] = book_entry
        self._save_books_index(books_index)
        
        # Save full book data
        book_file = os.path.join(self.database_folder, f'book_{book_id}.json')
        with open(book_file, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)
        
        # Save ink script
        ink_file = os.path.join(self.ink_folder, f'{book_id}.ink')
        with open(ink_file, 'w', encoding='utf-8') as f:
            f.write(ink_script)
        
        print(f"Saved book: {book_data['title']} (ID: {book_id})")
        return book_id
    
    def get_all_books(self):
        """Get list of all books"""
        books_index = self._load_books_index()
        return list(books_index.values())
    
    def get_book(self, book_id):
        """
        Get book data by ID
        
        Args:
            book_id (str): Book ID
            
        Returns:
            dict: Book data or None
        """
        books_index = self._load_books_index()
        
        if book_id not in books_index:
            return None
        
        # Load full book data
        book_file = os.path.join(self.database_folder, f'book_{book_id}.json')
        
        if not os.path.exists(book_file):
            return None
        
        try:
            with open(book_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            return book_data
        except Exception as e:
            print(f"Error loading book {book_id}: {e}")
            return None
    
    def get_ink_script(self, book_id):
        """
        Get ink script for a book
        
        Args:
            book_id (str): Book ID
            
        Returns:
            str: Ink script or None
        """
        ink_file = os.path.join(self.ink_folder, f'{book_id}.ink')
        
        if not os.path.exists(ink_file):
            return None
        
        try:
            with open(ink_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading ink script for book {book_id}: {e}")
            return None
    
    def delete_book(self, book_id):
        """
        Delete a book and all associated data
        
        Args:
            book_id (str): Book ID
            
        Returns:
            bool: Success status
        """
        try:
            # Load books index
            books_index = self._load_books_index()
            
            if book_id not in books_index:
                return False
            
            # Remove from index
            del books_index[book_id]
            self._save_books_index(books_index)
            
            # Delete book data file
            book_file = os.path.join(self.database_folder, f'book_{book_id}.json')
            if os.path.exists(book_file):
                os.remove(book_file)
            
            # Delete ink script
            ink_file = os.path.join(self.ink_folder, f'{book_id}.ink')
            if os.path.exists(ink_file):
                os.remove(ink_file)
            
            # Delete save data
            self.delete_save_data(book_id)
            
            print(f"Deleted book: {book_id}")
            return True
            
        except Exception as e:
            print(f"Error deleting book {book_id}: {e}")
            return False
    
    def save_game_state(self, book_id, save_data):
        """
        Save game state for a book
        
        Args:
            book_id (str): Book ID
            save_data (dict): Save data
            
        Returns:
            bool: Success status
        """
        try:
            # Add timestamp
            save_data['timestamp'] = datetime.now().isoformat()
            save_data['book_id'] = book_id
            
            # Save to file
            save_file = os.path.join(self.saves_folder, f'{book_id}.json')
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            # Update book index with last played info
            books_index = self._load_books_index()
            if book_id in books_index:
                books_index[book_id]['last_played'] = save_data['timestamp']
                books_index[book_id]['last_section'] = save_data.get('current_section', 'unknown')
                self._save_books_index(books_index)
            
            return True
            
        except Exception as e:
            print(f"Error saving game state for book {book_id}: {e}")
            return False
    
    def get_save_data(self, book_id):
        """
        Get save data for a book
        
        Args:
            book_id (str): Book ID
            
        Returns:
            dict: Save data or None
        """
        save_file = os.path.join(self.saves_folder, f'{book_id}.json')
        
        if not os.path.exists(save_file):
            return None
        
        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading save data for book {book_id}: {e}")
            return None
    
    def delete_save_data(self, book_id):
        """
        Delete save data for a book
        
        Args:
            book_id (str): Book ID
            
        Returns:
            bool: Success status
        """
        save_file = os.path.join(self.saves_folder, f'{book_id}.json')
        
        try:
            if os.path.exists(save_file):
                os.remove(save_file)
                
                # Update book index
                books_index = self._load_books_index()
                if book_id in books_index:
                    books_index[book_id]['last_played'] = None
                    books_index[book_id]['last_section'] = None
                    self._save_books_index(books_index)
                
                return True
            return True  # No save data to delete
            
        except Exception as e:
            print(f"Error deleting save data for book {book_id}: {e}")
            return False
    
    def _load_books_index(self):
        """Load books index from file"""
        try:
            with open(self.books_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle legacy format with "books" array
                if isinstance(data, dict) and "books" in data:
                    # Convert to new format: extract individual book entries
                    books_index = {}
                    
                    # Add individual book entries (they're the proper format)
                    for key, value in data.items():
                        if key != "books" and isinstance(value, dict) and "id" in value:
                            books_index[key] = value
                    
                    # Save in the new format
                    self._save_books_index(books_index)
                    return books_index
                
                # Already in correct format
                return data
        except Exception:
            return {}
    
    def _save_books_index(self, books_index):
        """Save books index to file"""
        try:
            with open(self.books_file, 'w', encoding='utf-8') as f:
                json.dump(books_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving books index: {e}")
    
    def get_storage_stats(self):
        """Get storage statistics"""
        try:
            books_index = self._load_books_index()
            
            # Count files and calculate sizes
            total_books = len(books_index)
            total_saves = len([f for f in os.listdir(self.saves_folder) if f.endswith('.json')])
            
            # Calculate total size (rough estimate)
            total_size = 0
            for root, dirs, files in os.walk(self.data_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            return {
                'total_books': total_books,
                'total_saves': total_saves,
                'storage_used_bytes': total_size,
                'storage_used_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {
                'total_books': 0,
                'total_saves': 0,
                'storage_used_bytes': 0,
                'storage_used_mb': 0
            }
    
    def clean_database(self, confirm=False):
        """
        Clean database by removing all books, saves, and ink scripts
        
        Args:
            confirm (bool): Safety confirmation required
            
        Returns:
            dict: Cleanup statistics
        """
        if not confirm:
            raise ValueError("Database cleanup requires explicit confirmation")
        
        stats = {
            'books_deleted': 0,
            'saves_deleted': 0,
            'ink_scripts_deleted': 0,
            'data_files_deleted': 0,
            'errors': []
        }
        
        try:
            # Get current stats before cleanup
            books_index = self._load_books_index()
            initial_books = len(books_index)
            
            # Delete all books (this will cascade to saves and ink scripts)
            for book_id in list(books_index.keys()):
                try:
                    if self.delete_book(book_id):
                        stats['books_deleted'] += 1
                    else:
                        stats['errors'].append(f"Failed to delete book: {book_id}")
                except Exception as e:
                    stats['errors'].append(f"Error deleting book {book_id}: {e}")
            
            # Clean up any remaining orphaned files
            stats['saves_deleted'] = self._clean_orphaned_saves()
            stats['ink_scripts_deleted'] = self._clean_orphaned_ink_scripts()
            stats['data_files_deleted'] = self._clean_orphaned_data_files()
            
            # Reset books index
            self._save_books_index({})
            
            print(f"Database cleanup completed:")
            print(f"  - Books deleted: {stats['books_deleted']}")
            print(f"  - Saves deleted: {stats['saves_deleted']}")  
            print(f"  - Ink scripts deleted: {stats['ink_scripts_deleted']}")
            print(f"  - Data files deleted: {stats['data_files_deleted']}")
            if stats['errors']:
                print(f"  - Errors: {len(stats['errors'])}")
            
            return stats
            
        except Exception as e:
            stats['errors'].append(f"Cleanup failed: {e}")
            print(f"Error during database cleanup: {e}")
            return stats
    
    def _clean_orphaned_saves(self):
        """Clean orphaned save files"""
        deleted = 0
        try:
            if os.path.exists(self.saves_folder):
                for filename in os.listdir(self.saves_folder):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.saves_folder, filename)
                        os.remove(file_path)
                        deleted += 1
        except Exception as e:
            print(f"Error cleaning saves: {e}")
        return deleted
    
    def _clean_orphaned_ink_scripts(self):
        """Clean orphaned ink script files"""
        deleted = 0
        try:
            if os.path.exists(self.ink_folder):
                for filename in os.listdir(self.ink_folder):
                    if filename.endswith('.ink'):
                        file_path = os.path.join(self.ink_folder, filename)
                        os.remove(file_path)
                        deleted += 1
        except Exception as e:
            print(f"Error cleaning ink scripts: {e}")
        return deleted
    
    def _clean_orphaned_data_files(self):
        """Clean orphaned book data files"""
        deleted = 0
        try:
            for filename in os.listdir(self.database_folder):
                if filename.startswith('book_') and filename.endswith('.json'):
                    file_path = os.path.join(self.database_folder, filename)
                    os.remove(file_path)
                    deleted += 1
        except Exception as e:
            print(f"Error cleaning data files: {e}")
        return deleted
    
    def verify_database_integrity(self):
        """
        Verify database integrity and report issues
        
        Returns:
            dict: Integrity report
        """
        report = {
            'total_books': 0,
            'valid_books': 0,
            'missing_data_files': [],
            'missing_ink_scripts': [],
            'orphaned_saves': [],
            'orphaned_ink_scripts': [],
            'orphaned_data_files': [],
            'corrupted_books': []
        }
        
        try:
            books_index = self._load_books_index()
            report['total_books'] = len(books_index)
            
            # Check each book in index
            for book_id, book_meta in books_index.items():
                # Check book data file exists
                book_file = os.path.join(self.database_folder, f'book_{book_id}.json')
                if not os.path.exists(book_file):
                    report['missing_data_files'].append(book_id)
                    continue
                    
                # Check ink script exists
                ink_file = os.path.join(self.ink_folder, f'{book_id}.ink')
                if not os.path.exists(ink_file):
                    report['missing_ink_scripts'].append(book_id)
                
                # Try to load book data
                try:
                    book_data = self.get_book(book_id)
                    if book_data:
                        report['valid_books'] += 1
                    else:
                        report['corrupted_books'].append(book_id)
                except Exception as e:
                    report['corrupted_books'].append(f"{book_id}: {e}")
            
            # Check for orphaned files
            report['orphaned_saves'] = self._find_orphaned_saves(books_index)
            report['orphaned_ink_scripts'] = self._find_orphaned_ink_scripts(books_index)
            report['orphaned_data_files'] = self._find_orphaned_data_files(books_index)
            
            return report
            
        except Exception as e:
            report['errors'] = [f"Integrity check failed: {e}"]
            return report
    
    def _find_orphaned_saves(self, books_index):
        """Find save files without corresponding books"""
        orphaned = []
        try:
            if os.path.exists(self.saves_folder):
                for filename in os.listdir(self.saves_folder):
                    if filename.endswith('.json'):
                        book_id = filename[:-5]  # Remove .json extension
                        if book_id not in books_index:
                            orphaned.append(filename)
        except Exception:
            pass
        return orphaned
    
    def _find_orphaned_ink_scripts(self, books_index):
        """Find ink script files without corresponding books"""
        orphaned = []
        try:
            if os.path.exists(self.ink_folder):
                for filename in os.listdir(self.ink_folder):
                    if filename.endswith('.ink'):
                        book_id = filename[:-4]  # Remove .ink extension
                        if book_id not in books_index:
                            orphaned.append(filename)
        except Exception:
            pass
        return orphaned
    
    def _find_orphaned_data_files(self, books_index):
        """Find book data files without corresponding index entries"""
        orphaned = []
        try:
            for filename in os.listdir(self.data_folder):
                if filename.startswith('book_') and filename.endswith('.json'):
                    book_id = filename[5:-5]  # Remove book_ prefix and .json suffix
                    if book_id not in books_index:
                        orphaned.append(filename)
        except Exception:
            pass
        return orphaned
    
    def generate_human_review(self, parsed_data, book_id):
        """
        Generate a human review file for parsed EPUB data
        
        Args:
            parsed_data (dict): Parsed story data from EPUB
            book_id (str): Book identifier
            
        Returns:
            str: Path to generated review file
        """
        review_file = os.path.join(self.review_folder, f'{book_id}_review.md')
        return self.review_generator.generate_review_file(parsed_data, review_file)
    
    def load_corrected_review(self, book_id):
        """
        Load and validate human-corrected review file
        
        Args:
            book_id (str): Book identifier
            
        Returns:
            tuple: (story_data, validation_report) or (None, error_message)
        """
        review_file = os.path.join(self.review_folder, f'{book_id}_review.md')
        
        if not os.path.exists(review_file):
            return None, f"Review file not found: {review_file}"
        
        try:
            # Parse the corrected file
            story_data = self.review_generator.parse_corrected_file(review_file)
            
            # Validate the corrected data
            is_valid = self.review_validator.validate_story(story_data)
            validation_report = self.review_validator.get_validation_report()
            
            return story_data, validation_report
            
        except Exception as e:
            return None, f"Error processing review file: {e}"
    
    def get_review_file_path(self, book_id):
        """Get the path to a book's review file"""
        return os.path.join(self.review_folder, f'{book_id}_review.md')