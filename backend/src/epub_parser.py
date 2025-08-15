"""
EPUB Parser for Interactive Story Game

Robust EPUB processing using ebooklib and BeautifulSoup to extract
gamebook content and convert it to structured data.
"""

import os
import re
import uuid
import logging
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

logger = logging.getLogger(__name__)

class EPUBParser:
    """Parses EPUB files and extracts interactive gamebook content"""
    
    def __init__(self, max_file_size=50 * 1024 * 1024):
        self.max_file_size = max_file_size
    
    def parse_epub(self, epub_path):
        """
        Parse an EPUB file and extract gamebook content
        
        Args:
            epub_path (str): Path to the EPUB file
            
        Returns:
            dict: Parsed book data
        """
        # Validate file
        self._validate_file(epub_path)
        
        try:
            # Read EPUB file
            book = epub.read_epub(epub_path)
            
            # Extract metadata
            metadata = self._extract_metadata(book)
            
            # Extract content sections
            content = self._extract_content(book)
            
            # Generate book data
            book_data = {
                'id': self._generate_book_id(metadata['title'], metadata['author']),
                'title': metadata['title'],
                'author': metadata['author'], 
                'cover': metadata.get('cover'),
                'content': content,
                'total_sections': len(content),
                'created_at': datetime.now().isoformat(),
                'original_filename': os.path.basename(epub_path)
            }
            
            return book_data
            
        except Exception as e:
            raise Exception(f"Failed to parse EPUB: {str(e)}")
    
    def _validate_file(self, file_path):
        """Validate EPUB file"""
        if not os.path.exists(file_path):
            raise Exception("File does not exist")
        
        if not file_path.lower().endswith('.epub'):
            raise Exception("File must have .epub extension")
        
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise Exception(f"File too large: {file_size // (1024*1024)}MB (max: 50MB)")
    
    def _extract_metadata(self, book):
        """Extract metadata from EPUB"""
        try:
            title = book.get_metadata('DC', 'title')
            author = book.get_metadata('DC', 'creator')
            
            title_text = title[0][0] if title else "Livre sans titre"
            author_text = author[0][0] if author else "Auteur inconnu"
            
            # Try to extract cover
            cover = None
            try:
                cover_item = None
                for item in book.get_items():
                    if item.get_name().lower().startswith('cover') and item.get_type() == ebooklib.ITEM_IMAGE:
                        cover_item = item
                        break
                
                if cover_item:
                    import base64
                    cover_data = base64.b64encode(cover_item.get_content()).decode('utf-8')
                    mime_type = cover_item.get_type()
                    cover = f"data:{mime_type};base64,{cover_data}"
            except Exception:
                pass  # Cover extraction is optional
            
            return {
                'title': title_text,
                'author': author_text,
                'cover': cover
            }
            
        except Exception as e:
            print(f"Warning: Could not extract metadata: {e}")
            return {
                'title': "Livre sans titre",
                'author': "Auteur inconnu",
                'cover': None
            }
    
    def _extract_content(self, book):
        """Extract content sections from EPUB"""
        content = {}
        
        # Get all HTML items
        html_items = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_items.append(item)
        
        print(f"Found {len(html_items)} HTML items in EPUB")
        
        # Process each HTML item
        for item in html_items:
            try:
                section = self._parse_html_content(item)
                if section and section['paragraph_number']:
                    content[section['paragraph_number']] = section
            except Exception as e:
                print(f"Warning: Failed to process {item.get_name()}: {e}")
                continue
        
        print(f"Extracted {len(content)} sections")
        return content
    
    def _parse_html_content(self, html_item):
        """Parse individual HTML content item"""
        try:
            html_content = html_item.get_content().decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for paragraph number
            paragraph_number = self._extract_paragraph_number(soup)
            if not paragraph_number:
                return None
            
            # Extract main text
            main_text = self._extract_main_text(soup)
            
            # Extract choices/links
            choices = self._extract_choices(soup)
            
            # Extract combat stats
            combat = self._extract_combat_stats(soup)
            
            return {
                'paragraph_number': paragraph_number,
                'text': main_text,
                'choices': choices,
                'combat': combat,
                'file_name': html_item.get_name()
            }
            
        except Exception as e:
            print(f"Error parsing HTML content: {e}")
            return None
    
    def _extract_paragraph_number(self, soup):
        """Extract paragraph number from HTML"""
        # Look for anchor with ID containing paragraph number
        anchor = soup.find('a', id=re.compile(r'_num\d+'))
        if anchor:
            match = re.search(r'_num(\d+)', anchor.get('id', ''))
            if match:
                return int(match.group(1))
        
        # Look for heading with paragraph number
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            heading = soup.find(tag)
            if heading:
                text = heading.get_text().strip()
                if text.isdigit():
                    return int(text)
        
        return None
    
    def _extract_main_text(self, soup):
        """Extract main narrative text"""
        text_parts = []
        
        # Look for paragraphs with main text
        text_paragraphs = soup.find_all('p', class_=re.compile(r'text|body|content', re.I))
        
        if not text_paragraphs:
            # Fallback: get all paragraphs
            text_paragraphs = soup.find_all('p')
        
        for p in text_paragraphs:
            # Skip paragraphs containing links (usually choice instructions)
            if p.find('a', href=True):
                continue
                
            # Skip empty paragraphs
            text = p.get_text().strip()
            if not text or text == ' ':
                continue
                
            # Skip paragraphs that look like metadata or navigation
            if any(keyword in text.lower() for keyword in ['copyright', 'titre original', 'rendez-vous au']):
                continue
                
            text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def _extract_choices(self, soup):
        """Extract choice options from HTML"""
        choices = []
        
        # Find all links that reference other sections
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            
            # Look for links to other book sections
            if 'book_' in href or '_num' in href:
                destination = self._extract_destination_number(href)
                if destination:
                    choice_text = self._find_choice_text(link, soup)
                    if choice_text:
                        choices.append({
                            'text': choice_text,
                            'destination': destination
                        })
        
        return choices
    
    def _extract_destination_number(self, href):
        """Extract destination paragraph number from href"""
        # Look for _numXXX pattern
        match = re.search(r'_num(\d+)', href)
        if match:
            return int(match.group(1))
        
        # Look for book_XXXX pattern and try to map to paragraph number
        match = re.search(r'book_(\d+)', href)
        if match:
            # This is a rough mapping - in real implementation you'd need
            # a mapping table between file numbers and paragraph numbers
            return int(match.group(1))
        
        return None
    
    def _find_choice_text(self, link, soup):
        """Find descriptive text for a choice link"""
        # Check if link has text content
        link_text = link.get_text().strip()
        if link_text and not link_text.isdigit():
            return link_text
        
        # Look for text in parent paragraph
        parent_p = link.find_parent('p')
        if parent_p:
            full_text = parent_p.get_text()
            
            # Extract text before "rendez-vous au"
            if 'rendez-vous au' in full_text.lower():
                before_link = full_text.split('rendez-vous au')[0].strip()
                if before_link:
                    # Clean up the choice text
                    before_link = re.sub(r'^(si vous|allez-vous|voulez-vous|désirez-vous)\s*', '', before_link, flags=re.I)
                    before_link = re.sub(r'\s*[,.]?\s*$', '', before_link)
                    return before_link
        
        # Look for adjacent choice description
        next_sibling = link.parent.find_next_sibling()
        if next_sibling and 'choice' in next_sibling.get('class', []):
            return next_sibling.get_text().strip()
        
        # Fallback: generate generic choice text
        destination = self._extract_destination_number(link.get('href'))
        return f"Aller au paragraphe {destination}" if destination else "Continuer"
    
    def _extract_combat_stats(self, soup):
        """Extract combat creature statistics"""
        combat_creatures = []
        
        # Look for combat-related paragraphs
        combat_elements = soup.find_all('p', class_=re.compile(r'creature|combat|monster', re.I))
        
        for element in combat_elements:
            text = element.get_text()
            
            # Parse creature name and stats
            # Pattern: CREATURE NAME HABILETÉ: X ENDURANCE: Y
            pattern = r'([A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ\s]+?)\s*HABILETÉ\s*:?\s*(\d+)\s*ENDURANCE\s*:?\s*(\d+)'
            
            match = re.search(pattern, text, re.I)
            if match:
                name = match.group(1).strip()
                skill = int(match.group(2))
                endurance = int(match.group(3))
                
                combat_creatures.append({
                    'name': name,
                    'skill': skill,
                    'endurance': endurance
                })
        
        return combat_creatures if combat_creatures else None
    
    def _generate_book_id(self, title, author):
        """Generate unique book ID"""
        text = f"{title}_{author}_{datetime.now().timestamp()}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, text)).replace('-', '')[:16]