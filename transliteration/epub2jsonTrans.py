#!/usr/bin/env python3
"""
epub2json.py - Convert EPUB with parallel text to JSON for language learning readers
Modified to handle ruby tags and detect language from title ending with language codes.
"""

import argparse
import html
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

# Supported language codes - expanded to include all common codes
SUPPORTED_LANGUAGES = [
    'ar', 'bn', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
    'la', 'mr', 'pa', 'pl', 'pt', 'ru', 'sw', 'ta', 'te', 'th', 'tr', 'ur', 
    'vi', 'zh', 'en'
]

# Default output base directory
DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json"

def detect_language_from_filename(filename):
    """
    Detect the target language from the EPUB filename.
    Looks for language codes at the end of the title with patterns like:
    - title-zh.epub, title-ja.epub, title-ru.epub, title-ar.epub, etc.
    """
    stem = Path(filename).stem
    
    # List of all supported language codes
    language_codes = SUPPORTED_LANGUAGES
    
    # First, normalize the filename by replacing common separators
    normalized_stem = re.sub(r'[_\s]+', '-', stem)
    
    # Try different patterns
    for lang in language_codes:
        # Pattern 1: -lang at the end (most common for your use case: title-zh, title-ja)
        if re.search(rf'-{lang}$', stem, re.IGNORECASE):
            return lang
        
        # Pattern 2: _lang at the end
        if re.search(rf'_{lang}$', stem, re.IGNORECASE):
            return lang
        
        # Pattern 3: .lang at the end
        if re.search(rf'\.{lang}$', stem, re.IGNORECASE):
            return lang
        
        # Pattern 4: space then lang at the end
        if re.search(rf'\s+{lang}$', stem, re.IGNORECASE):
            return lang
        
        # Pattern 5: -lang.epub pattern (already handled by $ anchor)
        if re.search(rf'-{lang}\.epub$', filename, re.IGNORECASE):
            return lang
        
        # Pattern 6: Check normalized version with hyphens
        if re.search(rf'-{lang}$', normalized_stem, re.IGNORECASE):
            return lang
    
    # If not found, try splitting by hyphens and checking the last part
    parts = re.split(r'[\s_\-]+', stem)
    if parts and parts[-1].lower() in language_codes:
        return parts[-1].lower()
    
    return None

def extract_ruby_data(soup, target_lang):
    """
    Extract data from ruby tags in the format:
    <ruby>base_text<rt class="translation">english</rt><rt>transliteration</rt></ruby>
    
    Returns a list of dictionaries with 'target_lang', 'en', and 'translit' fields
    """
    ruby_elements = soup.find_all('ruby')
    entries = []
    
    for ruby in ruby_elements:
        # Get the base text (the main word/phrase in the target language)
        # This is typically the direct text before any rt tags
        base_text = ''
        for child in ruby.children:
            if child.name != 'rt':
                if hasattr(child, 'get_text'):
                    base_text += child.get_text().strip()
                elif hasattr(child, 'string') and child.string:
                    base_text += child.string.strip()
        
        # Remove trailing/leading whitespace
        base_text = base_text.strip()
        
        # Find all rt (ruby text) elements
        rt_elements = ruby.find_all('rt')
        
        en_text = None
        translit_text = None
        
        for rt in rt_elements:
            rt_text = rt.get_text().strip()
            # Check if this rt has class="translation"
            if rt.get('class') and 'translation' in rt.get('class'):
                en_text = rt_text
            else:
                # This is likely the transliteration (pinyin, romaji, etc.)
                translit_text = rt_text
        
        # If we found all three parts, create an entry
        if base_text and en_text:
            entry = {
                target_lang: base_text,
                'en': en_text,
                'translit': translit_text if translit_text else ''
            }
            entries.append(entry)
    
    return entries

def process_epub_with_ruby(epub_path, target_lang, output_file=None, output_base=None):
    """
    Process an EPUB file with ruby tags and convert to JSON.
    Specifically designed for language learning materials with ruby annotations.
    """
    epub_path = Path(epub_path)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return []
    
    print(f"Processing EPUB: {epub_path.name}")
    print(f"Detected language: {target_lang}")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract EPUB
        print("Extracting EPUB...")
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            print(f"Error extracting EPUB {epub_path}: {e}", file=sys.stderr)
            return []
        
        # Find all XHTML/HTML files
        text_files = []
        for ext in ['*.xhtml', '*.html', 'htm', '*.xml']:
            text_files.extend(Path(temp_dir).rglob(ext))
        
        if not text_files:
            print(f"Error: No XHTML/HTML files found in EPUB", file=sys.stderr)
            return []
        
        print(f"Found {len(text_files)} content files to process")
        
        # Process each file and extract ruby data
        all_entries = []
        section_id = 1
        
        for xhtml_file in sorted(text_files):
            # Skip navigation, cover, and TOC files
            filename = xhtml_file.name.lower()
            if any(skip in filename for skip in ['nav', 'cover', 'toc', 'title']):
                continue
            
            try:
                with open(xhtml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract ruby data from this file
                entries = extract_ruby_data(soup, target_lang)
                
                if entries:
                    # Create a section for this file
                    section = {
                        'id': f"section_{section_id:03d}",
                        'filename': xhtml_file.name,
                        'title': None,
                        'paragraphs': entries
                    }
                    
                    # Try to extract title from the file
                    title_elem = soup.find('h1') or soup.find('title')
                    if title_elem:
                        section['title'] = {target_lang: title_elem.get_text().strip()}
                    
                    all_entries.append(section)
                    section_id += 1
                    
                    print(f"  Found {len(entries)} entries in {xhtml_file.name}")
            
            except Exception as e:
                print(f"Error processing {xhtml_file}: {e}", file=sys.stderr)
                continue
        
        # Combine all entries into sections (group by logical units if needed)
        if not all_entries:
            # If no sections with ruby tags found, create a single section with all entries
            all_entries = [{
                'id': 'section_001',
                'filename': 'combined',
                'title': {target_lang: epub_path.stem},
                'paragraphs': all_entries
            }]
        
        print(f"\nCreated {len(all_entries)} sections with vocabulary entries")
        total_entries = sum(len(section['paragraphs']) for section in all_entries)
        print(f"Total vocabulary entries: {total_entries}")
        
        # Save to JSON
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        elif output_base:
            # Generate output filename based on the original EPUB name
            epub_name = epub_path.stem
            # Remove language code from the end if present to avoid duplication
            for lang in SUPPORTED_LANGUAGES:
                if epub_name.endswith(f'-{lang}'):
                    epub_name = epub_name[:-(len(lang)+1)]
                    break
                elif epub_name.endswith(f'_{lang}'):
                    epub_name = epub_name[:-(len(lang)+1)]
                    break
            
            # Clean up the filename
            epub_name = re.sub(r'[_\s]+', '-', epub_name)
            epub_name = re.sub(r'-+', '-', epub_name)
            epub_name = epub_name.strip('-')
            
            # Create language-specific directory
            output_dir = Path(output_base) / target_lang
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_filename = f"{epub_name}.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        
        return all_entries

def main():
    parser = argparse.ArgumentParser(description='Convert EPUB with ruby tags to JSON for language learning')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('-l', '--lang', help='Target language code (e.g., zh, ja, es). If not provided, detected from filename ending')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    
    args = parser.parse_args()
    
    # Detect language from filename if not provided
    target_lang = args.lang
    if not target_lang:
        target_lang = detect_language_from_filename(args.epub_file)
        if not target_lang:
            print("Error: Could not detect language from filename. Please specify with --lang", file=sys.stderr)
            print(f"Expected filename patterns: title-zh.epub, title-ja.epub, title-ru.epub, title-ar.epub, etc.", file=sys.stderr)
            print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}", file=sys.stderr)
            sys.exit(1)
    
    print(f"Processing EPUB file: {args.epub_file}")
    print(f"Target language: {target_lang}")
    print(f"Output base directory: {args.output_base}")
    
    sections = process_epub_with_ruby(
        args.epub_file, 
        target_lang, 
        output_file=args.output,
        output_base=args.output_base if not args.output else None
    )
    
    # Print summary with sample
    if sections and sections[0]['paragraphs']:
        print(f"\nSample output entry:")
        sample = sections[0]['paragraphs'][0]
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    
    # Provide instruction for adding to your database
    print("\n" + "="*60)
    print("To add this to your database:")
    print("="*60)
    print(f"1. The JSON file has been saved to the {target_lang}/ directory")
    print("2. Each entry contains: target language word, English translation, and transliteration")
    print("3. You can import this JSON into your language learning application")
    print("\nExample entry format:")
    print('{')
    print(f'  "{target_lang}": "笔记本",')
    print('  "en": "notebook",')
    print('  "translit": "bǐ jì běn"')
    print('}')

if __name__ == '__main__':
    main()