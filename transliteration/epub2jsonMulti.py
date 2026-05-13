#!/usr/bin/env python3
"""
epub2jsonMulti.py - Convert EPUB with multiple language parallel text to JSON

The script detects all languages present in the EPUB (based on lang attributes)
and creates a JSON object where each paragraph has translations in all available languages.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from collections import defaultdict, OrderedDict
from bs4 import BeautifulSoup

SUPPORTED_LANGUAGES = [
    'ar', 'bn', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
    'la', 'mr', 'pa', 'pl', 'pt', 'ru', 'sw', 'ta', 'te', 'th', 'tr', 'ur', 
    'vi', 'zh', 'en'
]

DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml"

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
    """Find all XHTML/HTML files in the extracted EPUB in order"""
    text_files = []
    
    search_paths = [
        os.path.join(extract_path, 'EPUB', 'text'),
        os.path.join(extract_path, 'EPUB'),
        os.path.join(extract_path, 'OEBPS', 'text'),
        os.path.join(extract_path, 'OEBPS'),
        extract_path,
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for ext in ['*.xhtml', '*.html', '*.htm']:
                files = list(Path(search_path).glob(ext))
                if files:
                    # Sort by filename to maintain order (split_000, split_001, etc.)
                    text_files.extend(sorted(files))
    
    return text_files

def extract_paragraphs_from_file(file_path):
    """
    Extract paragraphs preserving the structure where:
    - English paragraphs have calibre2 class and no lang attribute
    - Translations have calibre3 class and lang attributes
    Returns list of paragraph groups: {'en': 'text', 'translations': [...]}
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        paragraph_groups = []
        
        # Find all p tags
        all_p_tags = soup.find_all('p')
        
        i = 0
        while i < len(all_p_tags):
            p = all_p_tags[i]
            classes = p.get('class', [])
            
            # Check if this is an English paragraph (calibre2)
            if 'calibre2' in classes and not p.get('lang'):
                english_text = p.get_text().strip()
                if not english_text:
                    i += 1
                    continue
                
                # Look for following translations (calibre3 with lang attributes)
                translations = {}
                j = i + 1
                
                # Collect consecutive translation paragraphs
                while j < len(all_p_tags):
                    next_p = all_p_tags[j]
                    next_classes = next_p.get('class', [])
                    lang_attr = next_p.get('lang', '')
                    
                    if 'calibre3' in next_classes and lang_attr:
                        trans_text = next_p.get_text().strip()
                        if trans_text:
                            translations[lang_attr] = trans_text
                        j += 1
                    elif 'calibre2' in next_classes and not next_p.get('lang'):
                        # Next English paragraph found, stop collecting translations
                        break
                    else:
                        # Skip other elements
                        j += 1
                
                # Create group with English and all translations
                group = {'en': english_text}
                group.update(translations)
                paragraph_groups.append(group)
                
                # Move index to the next English paragraph
                i = j
            else:
                # Skip non-English paragraphs (they should be collected as translations)
                i += 1
        
        return paragraph_groups
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def extract_all_paragraphs(text_files):
    """
    Extract all paragraphs from all files in order.
    """
    all_groups = []
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation and cover files
        if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
            continue
        
        print(f"  Processing: {filename}")
        
        groups = extract_paragraphs_from_file(xhtml_file)
        all_groups.extend(groups)
    
    return all_groups

def extract_title_from_epub(text_files):
    """Extract title from the first suitable file"""
    for xhtml_file in text_files:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for any h1 or title
            h1 = soup.find('h1')
            if h1:
                return h1.get_text().strip()
            
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
        
        # Extract all paragraph groups
        print("Extracting paragraph groups...")
        all_groups = extract_all_paragraphs(text_files)
        print(f"Total paragraph groups extracted: {len(all_groups)}")
        
        # Show language distribution
        lang_counts = defaultdict(int)
        for group in all_groups:
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
            'title': title or epub_path.stem,
            'paragraphs': all_groups
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
        total_groups = len(sections[0]['paragraphs'])
        print(f"\nSummary:")
        print(f"  Sections: {len(sections)}")
        print(f"  Total translation groups: {total_groups}")
        
        if sections[0]['paragraphs']:
            print(f"\nSample translation group (first 3):")
            for i, group in enumerate(sections[0]['paragraphs'][:3]):
                print(f"\n  Group {i+1}:")
                for lang, text in list(group.items())[:3]:  # Show first 3 languages
                    print(f"    {lang.upper()}: {text[:60]}...")

if __name__ == '__main__':
    main()