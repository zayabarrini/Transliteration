#!/usr/bin/env python3
"""
epub2jsonMulti.py - Convert EPUB with multiple language parallel text to JSON

The script detects all languages present in the EPUB (based on lang attributes or character detection)
and creates a JSON object where each paragraph has translations in all available languages.
Output is saved to /static/json/ml/ directory.
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
from collections import defaultdict

from bs4 import BeautifulSoup

# Supported language codes - expanded to include all common codes
SUPPORTED_LANGUAGES = [
    'ar', 'bn', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
    'la', 'mr', 'pa', 'pl', 'pt', 'ru', 'sw', 'ta', 'te', 'th', 'tr', 'ur', 
    'vi', 'zh', 'en'
]

# Default output base directory for multilingual JSON
DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml"

def detect_language_from_filename(filename):
    """
    Detect languages from the EPUB filename (optional, mainly for metadata)
    """
    stem = Path(filename).stem
    
    import re
    
    # Try to find language codes in filename
    detected_langs = []
    for lang in SUPPORTED_LANGUAGES:
        if re.search(rf'-{lang}(\.|$)', stem, re.IGNORECASE):
            detected_langs.append(lang)
        elif re.search(rf'_{lang}(\.|$)', stem, re.IGNORECASE):
            detected_langs.append(lang)
    
    return detected_langs

def get_language_unicode_ranges(lang_code):
    """Get Unicode ranges for character detection for the specified language"""
    ranges = {
        # East Asian languages
        'zh': r'[\u4e00-\u9fff]',  # Chinese
        'ja': r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]',  # Japanese
        'ko': r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]',  # Korean
        
        # South Asian languages
        'hi': r'[\u0900-\u097F]',  # Hindi
        'bn': r'[\u0980-\u09FF]',  # Bengali
        'pa': r'[\u0A00-\u0A7F]',  # Punjabi
        'mr': r'[\u0900-\u097F]',  # Marathi
        'te': r'[\u0C00-\u0C7F]',  # Telugu
        'ta': r'[\u0B80-\u0BFF]',  # Tamil
        'ur': r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]',  # Urdu
        
        # Middle Eastern languages
        'ar': r'[\u0600-\u06FF\u0750-\u077F]',  # Arabic
        'he': r'[\u0590-\u05FF]',  # Hebrew
        
        # European languages
        'ru': r'[\u0400-\u04FF]',  # Russian
        'el': r'[\u0370-\u03FF]',  # Greek
        'pl': r'[\u0104\u0105\u0106\u0107\u0118\u0119\u0141\u0142\u0143\u0144\u015A\u015B\u0179\u017A\u017B\u017C]',  # Polish
        'tr': r'[\u011E\u011F\u0130\u0131\u015E\u015F\u00FC]',  # Turkish
        'fr': r'[àâäéèêëîïôöùûüÿçœ]',  # French
        'es': r'[áéíóúüñ]',  # Spanish
        'de': r'[äöüß]',  # German
        'pt': r'[áâãàçéêíóôõúü]',  # Portuguese
        'it': r'[àèéìíîòóùú]',  # Italian
        'sw': r'[A-Za-z\s\.,!?\'"-]',  # Swahili
        
        # Southeast Asian languages
        'th': r'[\u0E00-\u0E7F]',  # Thai
        'vi': r'[\u1EA0-\u1EF9]',  # Vietnamese
        'id': r'[A-Za-z\s\.,!?\'"-]',  # Indonesian
        
        # Latin-based
        'la': r'[A-Za-z\s\.,!?\'"-]',  # Latin
    }
    
    return ranges.get(lang_code, r'[^\u0000-\u007F]')

def detect_language_by_content(text, lang_range_cache=None):
    """
    Detect which language a text is in based on character patterns.
    Returns language code or None if not detected.
    """
    if not text:
        return None
    
    if lang_range_cache is None:
        lang_range_cache = {}
    
    # Check each language's Unicode range
    for lang_code in SUPPORTED_LANGUAGES:
        if lang_code not in lang_range_cache:
            lang_range_cache[lang_code] = get_language_unicode_ranges(lang_code)
        
        # Skip English detection (it's the fallback)
        if lang_code == 'en':
            continue
        
        if re.search(lang_range_cache[lang_code], text):
            return lang_code
    
    # Check if it's English (mostly ASCII)
    if re.match(r'^[A-Za-z0-9\s\.,!?\'"-]+$', text):
        return 'en'
    
    return None

def extract_epub(epub_path, extract_path):
    """Extract EPUB file to a temporary directory"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return True
    except Exception as e:
        print(f"Error extracting EPUB {epub_path}: {e}", file=sys.stderr)
        return False

def find_text_files(extract_path):
    """Find all XHTML/HTML files in the extracted EPUB"""
    text_files = []
    
    search_paths = [
        extract_path,
        os.path.join(extract_path, 'EPUB'),
        os.path.join(extract_path, 'EPUB', 'text'),
        os.path.join(extract_path, 'OEBPS'),
        os.path.join(extract_path, 'OEBPS', 'text'),
        os.path.join(extract_path, 'content'),
        os.path.join(extract_path, 'contents'),
        os.path.join(extract_path, 'Text'),
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
                text_files.extend(Path(search_path).glob(ext))
    
    return sorted(text_files)

def extract_paragraphs_multilingual(file_path, lang_range_cache=None):
    """
    Extract all paragraphs from an XHTML file and detect their languages.
    Returns a list of dictionaries with 'text' and 'lang' for each paragraph.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        paragraphs = []
        
        # Find all paragraphs
        author_paragraphs = soup.find_all('p', class_='author')
        if not author_paragraphs:
            author_paragraphs = soup.find_all('p')
        
        for p in author_paragraphs:
            text = p.get_text().strip()
            if not text:
                continue
            
            # Check for explicit language attribute first
            p_lang = p.get('lang', '')
            
            if p_lang and p_lang in SUPPORTED_LANGUAGES:
                lang = p_lang
            else:
                # Detect language by content
                lang = detect_language_by_content(text, lang_range_cache)
            
            if lang:
                paragraphs.append({
                    'text': text,
                    'lang': lang
                })
        
        return paragraphs
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def group_paragraphs_by_sequence(all_paragraphs):
    """
    Group consecutive paragraphs into translation groups.
    Each group contains one paragraph per language.
    """
    if not all_paragraphs:
        return []
    
    # Group by index (assuming same index across languages)
    # First, collect all unique index positions
    # Since paragraphs appear in sequence, we'll group them as they appear
    
    translation_groups = []
    current_group = {}
    lang_range_cache = {}
    
    i = 0
    while i < len(all_paragraphs):
        para = all_paragraphs[i]
        lang = para['lang']
        
        # If this language is not in current group, add it
        if lang not in current_group:
            current_group[lang] = para['text']
            i += 1
        else:
            # This language already exists in current group, so this is a new group
            if current_group:
                translation_groups.append(current_group)
            current_group = {lang: para['text']}
            i += 1
    
    # Add the last group
    if current_group:
        translation_groups.append(current_group)
    
    return translation_groups

def extract_all_paragraphs_global(text_files):
    """
    Extract all paragraphs from all files in order with language detection.
    """
    all_paragraphs = []
    lang_range_cache = {}
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation and cover files
        if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
            continue
        
        print(f"  Processing: {filename}")
        
        paragraphs = extract_paragraphs_multilingual(xhtml_file, lang_range_cache)
        all_paragraphs.extend(paragraphs)
    
    return all_paragraphs

def extract_title_from_epub(text_files):
    """Extract title from the first suitable file"""
    for xhtml_file in text_files:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for any h1
            h1 = soup.find('h1')
            if h1:
                return h1.get_text().strip()
            
            # Look for title tag
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
        
        except Exception:
            continue
    
    return None

def process_epub_file_multilingual(epub_file, output_file=None, output_base=None):
    """Process an EPUB file and convert to multilingual JSON"""
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return []
    
    print(f"Processing EPUB: {epub_path.name}")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract EPUB
        print("Extracting EPUB...")
        if not extract_epub(epub_file, temp_dir):
            print(f"Error: Failed to extract EPUB {epub_file}", file=sys.stderr)
            return []
        
        # Find all text files
        text_files = find_text_files(temp_dir)
        
        if not text_files:
            print(f"Error: No XHTML/HTML files found in EPUB", file=sys.stderr)
            return []
        
        print(f"Found {len(text_files)} content files to process")
        
        # Extract all paragraphs with language detection
        print("Extracting paragraphs with language detection...")
        all_paragraphs = extract_all_paragraphs_global(text_files)
        print(f"Total paragraphs extracted: {len(all_paragraphs)}")
        
        # Group paragraphs into translation groups
        print("Grouping paragraphs by translation...")
        translation_groups = group_paragraphs_by_sequence(all_paragraphs)
        print(f"Created {len(translation_groups)} translation groups")
        
        # Show language distribution
        lang_counts = defaultdict(int)
        for group in translation_groups:
            for lang in group.keys():
                lang_counts[lang] += 1
        
        print("\nLanguage distribution:")
        for lang, count in sorted(lang_counts.items()):
            print(f"  {lang}: {count} paragraphs")
        
        # Extract title
        title = extract_title_from_epub(text_files)
        
        # Create sections
        sections = [{
            'id': 'main',
            'filename': 'all_content',
            'title': title,
            'paragraphs': translation_groups
        }]
        
        # Save to JSON
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        elif output_base:
            # Auto-generate output filename
            epub_name = epub_path.stem
            
            # Clean up the filename
            epub_name = re.sub(r'[_\s]+', '-', epub_name)
            epub_name = re.sub(r'-+', '-', epub_name)
            epub_name = epub_name.strip('-')
            
            # Remove language codes from filename for multilingual version
            for lang in SUPPORTED_LANGUAGES:
                if epub_name.endswith(f'-{lang}'):
                    epub_name = epub_name[:-(len(lang)+1)]
                    break
                elif epub_name.endswith(f'_{lang}'):
                    epub_name = epub_name[:-(len(lang)+1)]
                    break
                elif f'-db-{lang}' in epub_name:
                    epub_name = epub_name.replace(f'-db-{lang}', '')
                    break
            
            output_dir = Path(output_base)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_filename = f"{epub_name}-ml.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        
        return sections

def main():
    parser = argparse.ArgumentParser(description='Convert multilingual EPUB to JSON')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    
    args = parser.parse_args()
    
    print(f"Processing multilingual EPUB file: {args.epub_file}")
    print(f"Output base directory: {args.output_base}")
    
    sections = process_epub_file_multilingual(
        args.epub_file, 
        output_file=args.output,
        output_base=args.output_base if not args.output else None
    )
    
    # Print summary
    if sections:
        total_paragraphs = sum(len(section['paragraphs']) for section in sections)
        print(f"\nSummary:")
        print(f"  Sections: {len(sections)}")
        print(f"  Total translation groups: {total_paragraphs}")
        
        if sections[0]['paragraphs']:
            print(f"\nSample translation group:")
            sample = sections[0]['paragraphs'][0]
            for lang, text in sample.items():
                print(f"  {lang.upper()}: {text[:50]}...")

if __name__ == '__main__':
    main()