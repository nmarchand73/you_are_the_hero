#!/usr/bin/env python3
"""
EPUB to Markdown converter using spine order and direct XHTML extraction
"""

import os
import sys
import zipfile
import re
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

def extract_spine_order(epub_path):
    """Extract the reading order from EPUB spine (OPF file)"""
    spine_files = []
    
    with zipfile.ZipFile(epub_path, 'r') as zf:
        # Find OPF file
        opf_files = [f for f in zf.namelist() if f.endswith('.opf')]
        if not opf_files:
            raise Exception("No OPF file found in EPUB")
        
        opf_content = zf.read(opf_files[0]).decode('utf-8', errors='ignore')
        
        # Extract spine order
        spine_match = re.search(r'<spine[^>]*>(.*?)</spine>', opf_content, re.DOTALL)
        if not spine_match:
            raise Exception("No spine found in OPF")
        
        itemrefs = re.findall(r'<itemref[^>]*idref=["\']([^"\']+)["\'][^>]*>', spine_match.group(1))
        
        # Get manifest items to map IDs to hrefs (support both id-first and href-first formats)
        manifest_items = re.findall(r'<item[^>]*id=["\']([^"\']+)["\'][^>]*href=["\']([^"\']+)["\'][^>]*>', opf_content)
        if not manifest_items:
            # Try href-first format
            manifest_items = re.findall(r'<item[^>]*href=["\']([^"\']+)["\'][^>]*id=["\']([^"\']+)["\'][^>]*>', opf_content)
            # Swap the order to maintain (id, href) format
            manifest_items = [(href_id, href) for (href, href_id) in manifest_items]
        manifest_dict = dict(manifest_items)
        
        # Build list of files in spine order
        for item_id in itemrefs:
            href = manifest_dict.get(item_id)
            if href:
                spine_files.append(href)
    
    print(f"Found {len(spine_files)} files in spine order")
    return spine_files

def extract_xhtml_content(epub_path, xhtml_file):
    """Extract content and links directly from XHTML file"""
    with zipfile.ZipFile(epub_path, 'r') as zf:
        try:
            xhtml_content = zf.read(xhtml_file).decode('utf-8', errors='ignore')
            soup = BeautifulSoup(xhtml_content, 'html.parser')
            
            # Extract title - improved detection
            title = ""
            
            # Try multiple sources for title
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()
            
            # Also check for headings in content for title extraction only
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().strip()
                if not title or len(heading_text) > len(title):
                    title = heading_text
            
            # Extract body text
            body = soup.find('body')
            if body:
                # Clean up the text
                body_text = body.get_text(separator='\n', strip=True)
                # Remove extra whitespace
                body_text = re.sub(r'\n\s*\n', '\n\n', body_text)
            else:
                body_text = ""
            
            # Extract XHTML links - pure tag-based approach
            xhtml_links = []
            if body:
                links = body.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    link_text = link.get_text().strip()
                    if href and link_text:
                        xhtml_links.append({
                            'text': link_text,
                            'href': href,
                            'raw_html': str(link)
                        })
            
            return {
                'title': title,
                'content': body_text,
                'file': xhtml_file,
                'xhtml_links': xhtml_links,
                'corrupted': False
            }
            
        except Exception as e:
            print(f"Warning: Could not read {xhtml_file}: {e}")
            # Return a corrupted section marker instead of None
            return {
                'title': f"[CORRUPTED] {xhtml_file}",
                'content': f"⚠️ This section is corrupted and could not be read.\n\nError: {str(e)}\nFile: {xhtml_file}",
                'file': xhtml_file,
                'xhtml_links': [],
                'corrupted': True,
                'error': str(e)
            }

def identify_section_type(content_data):
    """Identify what type of section this is"""
    # Handle corrupted sections
    if content_data.get('corrupted', False):
        filename = content_data.get('file', 'unknown')
        # Try to extract a section number from filename for corrupted files
        file_match = re.search(r'book_(\d+)\.xhtml', filename)
        if file_match:
            section_num = int(file_match.group(1)) + 1  # Adjust for 0-based indexing
            return f"corrupted-{section_num}", f"Section {section_num}: corrompu"
        else:
            return 'corrupted', f"Section corrompu ({filename})"
    
    title = content_data['title'].lower()
    content = content_data['content'].lower()
    filename = content_data.get('file', '')
    
    # Try to extract section number from filename even for empty content
    file_match = re.search(r'book_(\d+)\.xhtml', filename)
    if file_match:
        section_num = int(file_match.group(1)) + 1  # Adjust for 0-based indexing
        
        # Check if content is empty/minimal
        if len(content.strip()) < 10:
            return f"empty-{section_num}", f"Section {section_num}: vide"
        
        # Look for numbered sections in content
        section_match = re.search(r'#(\d+)\s*-\s*(.+)', content)
        if section_match:
            content_section_num = int(section_match.group(1))
            section_title = section_match.group(2).split('\n')[0].strip()
            return str(content_section_num), f"Section {content_section_num}: {section_title}"
        else:
            # Use filename-based numbering for sections without clear content markers
            return str(section_num), f"Section {section_num}"
    
    # Handle special sections - only numbered sections
    if len(content.strip()) >= 50:
        content_lower = content.lower()
        
        # ONLY: Look for numbered sections (no automatic special section detection)
        section_match = re.search(r'#(\d+)\s*-\s*(.+)', content)
        if section_match:
            section_num = int(section_match.group(1))
            section_title = section_match.group(2).split('\n')[0].strip()
            return str(section_num), f"Section {section_num}: {section_title}"
    
    # All other sections are marked as unknown for manual identification
    if filename.endswith('.xhtml'):
        # Generic section from filename
        return f"unknown-{filename}", f"Section inconnue ({filename})"
    
    return None, None

def extract_choices_from_xhtml_links(xhtml_links, sections_map):
    """Extract choices from XHTML links using pure tag-based approach - no text analysis"""
    choices = []
    seen_targets = set()  # Track unique targets to avoid duplicates
    
    for link in xhtml_links:
        href = link['href']
        text = link['text'].strip()
        
        # Skip empty links
        if not text:
            continue
        
        # Check if this is a link to another section file (with or without fragments)
        if '.xhtml' in href or '.html' in href:
            # Find the target file
            target_file = href
            if '/' in target_file:
                target_file = target_file.split('/')[-1]
            
            # Remove any anchor fragments from the filename
            if '#' in target_file:
                target_file = target_file.split('#')[0]
            
            # Find the actual section number from the sections_map
            if target_file in sections_map:
                section_info = sections_map[target_file]
                section_id = section_info['id']
                
                # Convert section_id to target anchor (same format as TOC)
                target_anchor = f"#{section_info['anchor_title']}"
                
                # Skip if we already have this target to avoid duplicates
                if target_anchor in seen_targets:
                    continue
                seen_targets.add(target_anchor)
                
                # Simple approach: use the link text directly
                # For numeric links, create descriptive text
                if text.isdigit():
                    choice_text = f"Aller au paragraphe {text}"
                else:
                    choice_text = text
                
                choice = {
                    'text': choice_text,
                    'target': target_anchor,
                    'section_ref': section_id,
                    'original_href': href
                }
                
                choices.append(choice)
    
    return choices

def extract_choices_from_content(content):
    """Extract choices from the content text by identifying choice-link pairs"""
    choices = []
    
    # Method 1: Find "rendez-vous au X" patterns (for La-nuit-du-loup-garou style)
    rendez_vous_pattern = r'([^.!?\n]{10,300})[.,]?\s*\(?rendez-vous au\s*(\d+)\)?'
    rendez_matches = re.findall(rendez_vous_pattern, content, re.IGNORECASE | re.MULTILINE)
    
    for choice_text, section_num in rendez_matches:
        choice_text = choice_text.strip()
        
        # Clean up choice text - take only the last sentence if too long
        if len(choice_text) > 100:
            sentences = re.split(r'[.!?]', choice_text)
            if len(sentences) > 1:
                choice_text = sentences[-1].strip()
        
        target = f"#section-{int(section_num)}"
        
        # Avoid duplicates and noise
        existing_targets = [c['target'] for c in choices]
        existing_texts = [c['text'].lower() for c in choices]
        
        if (target not in existing_targets and 
            choice_text.lower() not in existing_texts and
            5 < len(choice_text) < 250):
            
            choices.append({
                'text': choice_text,
                'target': target,
                'section_ref': int(section_num)
            })
    
    # Method 2: Find combined patterns "Choice text. Action au numéro X" (Golden_Bullets style)
    choice_link_pattern = r'([^.!?\n]{10,200})\.\s*(?:aller|continuer|poursuivre|avancer)(?:\s+(?:au|jusqu\'au))?\s+(?:numéro|paragraphe)\s*[#]?(\d+)'
    all_matches = re.findall(choice_link_pattern, content, re.IGNORECASE | re.MULTILINE)
    
    for choice_text, section_num in all_matches:
        choice_text = choice_text.strip()
        
        # Clean up choice text - take only the last sentence if too long
        if len(choice_text) > 100:
            sentences = re.split(r'[.!?]', choice_text)
            if len(sentences) > 1:
                choice_text = sentences[-1].strip()
        
        target = f"#section-{int(section_num)}"
        
        # Avoid duplicates
        existing_targets = [c['target'] for c in choices]
        existing_texts = [c['text'].lower() for c in choices]
        
        if (target not in existing_targets and 
            choice_text.lower() not in existing_texts and
            5 < len(choice_text) < 200 and
            not re.search(r'(?:numéro|paragraphe|chapitre)\s*[#]?\d+', choice_text, re.IGNORECASE)):
            
            choices.append({
                'text': choice_text,
                'target': target,
                'section_ref': int(section_num)
            })
    
    # Sort choices by section reference for consistency
    choices.sort(key=lambda x: x.get('section_ref', 0))
    
    return choices

def convert_epub_to_md_spine(epub_path, output_file=None):
    """Convert EPUB to Markdown using spine order and direct XHTML extraction"""
    
    if output_file is None:
        epub_name = Path(epub_path).stem
        # Store reviews in the backend/data/reviews directory
        reviews_dir = Path(__file__).parent.parent / "backend" / "data" / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)
        output_file = reviews_dir / f"{epub_name}_review.md"
    
    print(f"Converting {epub_path} to {output_file}")
    
    # Extract spine order
    spine_files = extract_spine_order(epub_path)
    
    # First pass: Extract content and build sections map
    sections = []
    sections_map = {}  # Map filename to section info
    
    for i, xhtml_file in enumerate(spine_files):
        print(f"Processing {i+1}/{len(spine_files)}: {xhtml_file}")
        
        content_data = extract_xhtml_content(epub_path, xhtml_file)
        # Now content_data is never None - corrupted sections return a marker
        
        section_id, section_title = identify_section_type(content_data)
        if not section_id:
            print(f"  Skipping (no content): {xhtml_file}")
            continue
        
        # Create anchor title for this section
        anchor_title = section_title.lower().replace(' ', '-').replace(':', '').replace('?', '').replace('!', '').replace(',', '').replace('(', '').replace(')', '').replace('«', '').replace('»', '').replace('"', '')
        
        # Map the filename to section info
        filename = xhtml_file.split('/')[-1]
        sections_map[filename] = {
            'id': section_id,
            'title': section_title,
            'anchor_title': anchor_title
        }
        
        sections.append({
            'id': section_id,
            'title': section_title,
            'content': content_data['content'],
            'choices': [],  # Will be filled in second pass
            'file': xhtml_file,
            'xhtml_links': content_data.get('xhtml_links', []),
            'corrupted': content_data.get('corrupted', False),
            'error': content_data.get('error', '')
        })
        
        print(f"  Added: {section_title}")
    
    # Second pass: Extract choices now that we have the complete sections map
    for section in sections:
        # Extract choices using XHTML links technique
        choices = extract_choices_from_xhtml_links(section['xhtml_links'], sections_map)
        section['choices'] = choices
    
    # Generate section anchor mapping
    section_anchors = {}
    for section in sections:
        anchor_title = section['title'].lower().replace(' ', '-').replace(':', '').replace('?', '').replace('!', '').replace(',', '').replace('(', '').replace(')', '').replace('«', '').replace('»', '').replace('"', '')
        section_anchors[section['id']] = anchor_title
    
    # Update choice targets to use proper anchors
    for section in sections:
        for choice in section['choices']:
            # Extract section number from target like "#section-2" 
            if choice['target'].startswith('#section-'):
                target_id = choice['target'].replace('#section-', '')
                if target_id in section_anchors:
                    choice['target'] = f"#{section_anchors[target_id]}"
    
    # Generate Markdown
    md_content = []
    
    # Header
    md_content.append("---")
    md_content.append(f"title: \"{sections[0]['title'] if sections else 'EPUB Content'}\"")
    md_content.append("sections_found: " + str(len(sections)))
    md_content.append("review_status: \"spine_extracted\"")
    md_content.append("---")
    md_content.append("")
    
    # Instructions
    md_content.append("# Story Content (Spine Order)")
    md_content.append("")
    md_content.append("> **This file follows the exact EPUB spine reading order**")
    md_content.append("> - Content extracted directly from XHTML files") 
    md_content.append("> - Choices auto-detected from XHTML links")
    md_content.append("> - Navigate with Ctrl+Click on links")
    md_content.append("")
    md_content.append("## Review Instructions")
    md_content.append("")
    md_content.append("Before indexing with `python app.py --index`, please review:")
    md_content.append("")
    md_content.append("1. **Section identification**: Check if sections are correctly identified")
    md_content.append("   - Special sections: Introduction, Règles, Titre should be clearly marked")
    md_content.append("   - Numbered sections: Should follow the book's numbering")
    md_content.append("")
    md_content.append("2. **Choices validation**: Verify that detected choices are accurate")
    md_content.append("   - All story branches should have proper links")
    md_content.append("   - No broken or missing choice links")
    md_content.append("")
    md_content.append("3. **Content quality**: Ensure text is readable and complete")
    md_content.append("   - Fix any corrupted or garbled text")
    md_content.append("   - Remove system artifacts or formatting issues")
    md_content.append("")
    
    # Table of Contents
    md_content.append("## Table of Contents")
    md_content.append("")
    corrupted_count = 0
    empty_count = 0
    valid_count = 0
    for section in sections:
        # Use auto-generated heading anchors based on title
        anchor_title = section['title'].lower().replace(' ', '-').replace(':', '').replace('?', '').replace('!', '').replace(',', '').replace('(', '').replace(')', '').replace('«', '').replace('»', '').replace('"', '').replace('[', '').replace(']', '')
        
        # Mark different section types in TOC (same format as Golden_Bullets)
        if section['id'].startswith('corrupted'):
            corrupted_count += 1
            md_content.append(f"- [**{section['title']}**](#{anchor_title}) (`{section['id']}`)")
        elif section['id'].startswith('empty'):
            empty_count += 1
            md_content.append(f"- [**{section['title']}**](#{anchor_title}) (`{section['id']}`)")
        else:
            valid_count += 1
            md_content.append(f"- [**{section['title']}**](#{anchor_title}) (`{section['id']}`)")
    md_content.append("")
    md_content.append(f"**Summary:** {valid_count} valid sections, {empty_count} empty sections, {corrupted_count} corrupted sections")
    md_content.append("")
    
    # Sections
    for section in sections:
        # Use clean section titles (same format as Golden_Bullets)
        md_content.append(f"## {section['title']}")
        
        # Add review comments for special sections that need identification
        section_title_lower = section['title'].lower()
        if any(word in section_title_lower for word in ['section inconnue', 'unknown', 'part']):
            md_content.append("<!-- REVIEW: Please identify this section. Could it be:")
            md_content.append("     - Introduction/Prologue?")  
            md_content.append("     - Rules/How to play?")
            md_content.append("     - Title page?")
            md_content.append("     - A numbered story section?")
            md_content.append("     Edit the title above to match the correct identification. -->")
            md_content.append("")
        
        if section['id'].startswith('corrupted') or section['id'].startswith('empty'):
            md_content.append(f"**Status:** {section.get('error', 'No content available')}")
        md_content.append("")
        
        # Content (same format as Golden_Bullets)
        md_content.append(section['content'])
        md_content.append("")
        
        # Choices (only for valid sections with content)
        if not section['id'].startswith('corrupted') and not section['id'].startswith('empty'):
            if section['choices']:
                md_content.append("**Choices:**")
                md_content.append("")
                for choice in section['choices']:
                    md_content.append(f"- [{choice['text']}]({choice['target']})")
                md_content.append("")
            else:
                md_content.append("**Choices:**")
                md_content.append("")
                md_content.append("*No choices detected. Add manually if needed.*")
                md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"✅ Generated: {output_file}")
    print(f"📊 {len(sections)} sections extracted in spine order")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Convert EPUB to Markdown using spine order')
    parser.add_argument('epub_file', help='Path to EPUB file')
    parser.add_argument('-o', '--output', help='Output markdown file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.epub_file):
        print(f"Error: EPUB file not found: {args.epub_file}")
        return 1
    
    try:
        convert_epub_to_md_spine(args.epub_file, args.output)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())