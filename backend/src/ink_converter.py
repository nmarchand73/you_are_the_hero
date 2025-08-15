"""
Ink Converter for Interactive Story Game
Converts parsed book content to ink script format
"""

import re
import json
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import datetime

class InkConverter:
    def convert_to_ink(self, book_data):
        """
        Convert parsed book content to simple JSON story format
        
        Args:
            book_data (dict): Parsed book data
            
        Returns:
            str: JSON story format for our custom game engine
        """
        sections = book_data['content']
        
        # Sort sections by paragraph number - handle mixed int/string types
        def sort_key(section):
            para_num = section['paragraph_number']
            if isinstance(para_num, int):
                return (0, para_num)  # Numbers first, then by value
            elif isinstance(para_num, str) and para_num.isdigit():
                return (0, int(para_num))  # Numeric strings as numbers
            else:
                return (1, para_num)  # Non-numeric strings last, alphabetically
        
        sorted_sections = sorted(sections.values(), key=sort_key)
        
        print(f"Converting {len(sorted_sections)} sections to simple JSON format")
        
        # Always start from the Introduction section
        starting_section = self._find_introduction_section(sections)
        print(f"Starting section set to: {starting_section}")
        
        # Create a simple story structure
        story_data = {
            "title": book_data['title'],
            "author": book_data['author'],
            "startingSection": starting_section,
            "sections": {}
        }
        
        for section in sorted_sections:
            section_id = str(section['paragraph_number'])
            story_data['sections'][section_id] = {
                "text": section['text'].strip() if section['text'] else "",
                "choices": section['choices'] if section['choices'] else [],
                "isEnd": len(section['choices']) == 0 if section['choices'] is not None else True
            }
        
        return json.dumps(story_data, ensure_ascii=False, indent=2)
    
    def _detect_starting_section(self, sections):
        """
        Detect the actual starting section of the adventure
        
        Args:
            sections (dict): All parsed sections
            
        Returns:
            int: The paragraph number of the likely starting section
        """
        # Patterns that indicate a story beginning
        beginning_patterns = [
            r'[Dd]ès que vous (êtes )?arriv[eé]',
            r'[Vv]ous arrivez',
            r'[Vv]ous (êtes )?arriv[eé].*[Vv]argenhof',
            r'[Vv]otre qu[eê]te commence',
            r'[Ll]\'aventure commence',
            r'[Vv]ous entrez.*ville',
            r'[Vv]ous voyagez',
            r'[Aa]u début de',
            r'[Cc]ommencez par'
        ]
        
        # Score sections based on how likely they are to be the beginning
        candidates = []
        
        for section_id, section in sections.items():
            text = section.get('text', '').strip()
            if not text:
                continue
                
            score = 0
            paragraph_num = section.get('paragraph_number', 0)
            
            # Higher score for sections that match beginning patterns
            for pattern in beginning_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 10
                    break
            
            # Boost score for sections mentioning key locations
            if re.search(r'[Vv]argenhof', text, re.IGNORECASE):
                score += 5
            
            # Slightly prefer higher numbered sections (gamebooks often start at 100+ or 500+)
            # Only apply this to numeric sections
            if isinstance(paragraph_num, int):
                if paragraph_num >= 500:
                    score += 3
                elif paragraph_num >= 100:
                    score += 1
            
            # Penalize sections that start mid-action
            if re.search(r'^[Vv]ous allez devoir|^[Ss]oudain|^[Aa]lors que|^[Mm]aintenant', text):
                score -= 5
            
            # Prefer sections with text length that suggests introduction
            if 100 <= len(text) <= 1000:
                score += 2
            
            if score > 0:
                candidates.append((paragraph_num, score, text[:100]))
        
        # Check if there's an introduction (section 0)
        if 0 in sections:
            intro_section = sections[0]
            intro_text = intro_section.get('text', '')
            if len(intro_text) > 50:  # Substantial introduction content
                print(f"Found introduction (section 0): {intro_text[:100]}...")
                return 0
        
        if candidates:
            # Sort by score (highest first), then by section number for tie-breaking
            # Handle mixed int/string section numbers
            def sort_candidates(item):
                section_id, score, text = item  # Unpack 3 values
                if isinstance(section_id, int):
                    return (-score, 0, section_id)  # Numbers first
                elif isinstance(section_id, str) and section_id.isdigit():
                    return (-score, 0, int(section_id))  # Numeric strings as numbers
                else:
                    return (-score, 1, section_id)  # Non-numeric strings last
            
            candidates.sort(key=sort_candidates)
            
            best_section = candidates[0][0]
            print(f"Starting section detection:")
            for num, score, text_preview in candidates[:3]:
                print(f"  Section {num} (score: {score}): {text_preview}...")
                
            return best_section
        
        # Fallback: return 1 if no good candidate found
        print("No clear starting section found, defaulting to section 1")
        return 1
    
    def _find_introduction_section(self, sections):
        """
        Find the Introduction section marked manually by the user
        
        Args:
            sections (dict): All sections from the book
            
        Returns:
            str or int: The ID of the Introduction section
        """
        # Look for section with ID "intro" (from manual tagging)
        if 'intro' in sections:
            print("Found manually tagged Introduction section")
            return 'intro'
        
        # Fallback: look for sections with "Introduction" in the title  
        for section_id, section in sections.items():
            if 'Introduction' in section.get('title', ''):
                print(f"Found Introduction section by title: {section_id}")
                return section_id
        
        # Last fallback: return first section
        if sections:
            first_key = list(sections.keys())[0]
            print(f"No Introduction found, using first section: {first_key}")
            return first_key
        
        # Ultimate fallback
        print("No sections found, defaulting to 1")
        return 1
    
    def validate_ink_script(self, story_json):
        """
        Validate generated story JSON
        
        Args:
            story_json (str): Generated story JSON
            
        Returns:
            dict: Validation result
        """
        errors = []
        warnings = []
        
        # Basic validation
        if not story_json or not story_json.strip():
            errors.append("Empty story data")
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        try:
            story_data = json.loads(story_json)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check required fields
        required_fields = ['title', 'author', 'startingSection', 'sections']
        for field in required_fields:
            if field not in story_data:
                errors.append(f"Missing required field: {field}")
        
        # Check sections structure
        if 'sections' in story_data:
            sections = story_data['sections']
            if not isinstance(sections, dict):
                errors.append("Sections must be a dictionary")
            else:
                section_count = len(sections)
                if section_count == 0:
                    errors.append("No sections found")
                
                # Check starting section exists
                starting_section = str(story_data.get('startingSection', 1))
                if starting_section not in sections:
                    warnings.append(f"Starting section '{starting_section}' not found")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'stats': {
                'sections': len(story_data.get('sections', {})),
                'title': story_data.get('title', 'Unknown'),
                'author': story_data.get('author', 'Unknown')
            }
        }