"""
Book Manager for Interactive Story Game
Handles book storage, retrieval, and save game management
"""

import os
import json
import uuid
from datetime import datetime

class BookManager:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.books_file = os.path.join(data_folder, 'books.json')
        self.saves_folder = os.path.join(data_folder, 'saves')
        self.ink_folder = os.path.join(data_folder, 'ink_scripts')
        
        # Ensure directories exist
        os.makedirs(self.saves_folder, exist_ok=True)
        os.makedirs(self.ink_folder, exist_ok=True)
        
        # Initialize books index if it doesn't exist
        if not os.path.exists(self.books_file):
            self._save_books_index({})
    
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
        
        # Save book metadata to index
        books_index[book_id] = book_entry
        self._save_books_index(books_index)
        
        # Save full book data
        book_file = os.path.join(self.data_folder, f'book_{book_id}.json')
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
        book_file = os.path.join(self.data_folder, f'book_{book_id}.json')
        
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
            book_file = os.path.join(self.data_folder, f'book_{book_id}.json')
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
                return json.load(f)
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