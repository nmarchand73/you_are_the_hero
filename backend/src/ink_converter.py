"""
Ink Converter for Interactive Story Game
Converts parsed book content to ink script format
"""

import re
from datetime import datetime

class InkConverter:
    def convert_to_ink(self, book_data):
        """
        Convert parsed book content to ink script
        
        Args:
            book_data (dict): Parsed book data
            
        Returns:
            str: Generated ink script
        """
        sections = book_data['content']
        ink_script = self._generate_header(book_data)
        
        # Sort sections by paragraph number
        sorted_sections = sorted(sections.values(), key=lambda x: x['paragraph_number'])
        
        print(f"Converting {len(sorted_sections)} sections to ink format")
        
        # Convert each section
        for section in sorted_sections:
            ink_script += self._convert_section(section)
        
        # Add footer
        ink_script += self._generate_footer()
        
        return ink_script
    
    def _generate_header(self, book_data):
        """Generate ink script header"""
        return f"""// {book_data['title']}
// by {book_data['author']}
// Converted from EPUB format
// Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

VAR current_section = 1
VAR player_health = 20
VAR player_skill = 10
VAR player_luck = 10

-> section_1

"""
    
    def _convert_section(self, section):
        """Convert a single section to ink format"""
        ink_content = f"=== section_{section['paragraph_number']} ===\n"
        
        # Add main text
        if section['text']:
            formatted_text = self._format_text(section['text'])
            ink_content += formatted_text + '\n\n'
        
        # Add combat if present
        if section['combat']:
            ink_content += self._format_combat(section['combat']) + '\n\n'
        
        # Add choices or end
        if section['choices']:
            ink_content += self._format_choices(section['choices'])
        else:
            ink_content += '-> END\n'
        
        ink_content += '\n'
        return ink_content
    
    def _format_text(self, text):
        """Format text content for ink"""
        # Clean up text
        formatted = text.replace('\n\n\n+', '\n\n')  # Remove excessive line breaks
        formatted = formatted.strip()
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in formatted.split('\n\n') if p.strip()]
        
        return '\n\n'.join(paragraphs)
    
    def _format_combat(self, creatures):
        """Format combat encounters"""
        combat_text = '# Combat!\n\n'
        
        for creature in creatures:
            combat_text += f"**{creature['name']}** - Habileté: {creature['skill']}, Endurance: {creature['endurance']}\n\n"
        
        combat_text += '*(Résolvez ce combat selon les règles du jeu)*\n'
        return combat_text
    
    def _format_choices(self, choices):
        """Format choices for ink"""
        if not choices:
            return '-> END\n'
        
        choice_text = ''
        for choice in choices:
            clean_text = self._clean_choice_text(choice['text'])
            choice_text += f"+ [{clean_text}] -> section_{choice['destination']}\n"
        
        return choice_text
    
    def _clean_choice_text(self, text):
        """Clean choice text"""
        # Remove common prefixes
        clean = re.sub(r'^(si vous|allez-vous|voulez-vous|désirez-vous)\s*', '', text, flags=re.I)
        
        # Remove trailing punctuation
        clean = re.sub(r'\s*[,.?!]\s*$', '', clean)
        
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Capitalize first letter
        if clean:
            clean = clean[0].upper() + clean[1:]
        
        return clean
    
    def _generate_footer(self):
        """Generate ink script footer"""
        return """
// End of story
=== END ===
Fin de l'aventure.

-> DONE
"""
    
    def validate_ink_script(self, ink_script):
        """
        Validate generated ink script
        
        Args:
            ink_script (str): Generated ink script
            
        Returns:
            dict: Validation result
        """
        errors = []
        warnings = []
        
        lines = ink_script.split('\n')
        
        # Basic validation
        if not ink_script or not ink_script.strip():
            errors.append("Empty ink script")
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check for required elements
        if '-> section_1' not in ink_script:
            warnings.append("No starting section found (expected '-> section_1')")
        
        # Check knot structure
        knot_count = len(re.findall(r'=== \w+ ===', ink_script))
        if knot_count == 0:
            errors.append("No knots found - invalid ink script structure")
        
        # Check for basic syntax errors
        choice_count = len(re.findall(r'\+ \[.*?\] ->', ink_script))
        divert_count = len(re.findall(r'-> \w+', ink_script))
        
        # Validate choice syntax
        invalid_choices = re.findall(r'\+ \[.*?\](?! ->)', ink_script)
        if invalid_choices:
            errors.extend([f"Invalid choice syntax: {choice}" for choice in invalid_choices])
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'stats': {
                'total_lines': len(lines),
                'sections': knot_count,
                'choices': choice_count,
                'diverts': divert_count
            }
        }