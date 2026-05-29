#!/usr/bin/env python3
"""
epub2json.py - Convert EPUB with ruby tags to a flat JSON list
"""

import argparse
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

SUPPORTED_LANGUAGES = ['ar', 'bn', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
                       'la', 'mr', 'pa', 'pl', 'pt', 'ru', 'sw', 'ta', 'te', 'th', 'tr', 'ur', 
                       'vi', 'zh', 'en']

DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json"

def detect_language_from_filename(filename):
    """Detect language from filename ending with -zh, -ja, -ru, -ar, etc."""
    stem = Path(filename).stem
    
    for lang in SUPPORTED_LANGUAGES:
        if re.search(rf'-{lang}$', stem, re.IGNORECASE):
            return lang
        if re.search(rf'_{lang}$', stem, re.IGNORECASE):
            return lang
    
    parts = re.split(r'[\s_\-]+', stem)
    if parts and parts[-1].lower() in SUPPORTED_LANGUAGES:
        return parts[-1].lower()
    
    return None

def extract_ruby_entries(soup, target_lang):
    """Extract entries from ruby tags as a flat list"""
    entries = []
    
    for ruby in soup.find_all('ruby'):
        # Get base text
        base_text = ''
        for child in ruby.children:
            if child.name != 'rt':
                if hasattr(child, 'get_text'):
                    base_text += child.get_text().strip()
                elif hasattr(child, 'string') and child.string:
                    base_text += child.string.strip()
        base_text = base_text.strip()
        
        # Find translations and transliterations
        en_text = None
        translit_text = None
        
        for rt in ruby.find_all('rt'):
            rt_text = rt.get_text().strip()
            if rt.get('class') and 'translation' in rt.get('class'):
                en_text = rt_text
            else:
                translit_text = rt_text
        
        if base_text and en_text:
            entry = {
                target_lang: base_text,
                'en': en_text,
                'translit': translit_text if translit_text else ''
            }
            entries.append(entry)
    
    return entries

def process_epub(epub_path, target_lang, output_file=None, output_base=None):
    """Process EPUB and return flat list of entries"""
    epub_path = Path(epub_path)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return []
    
    print(f"Processing: {epub_path.name}")
    print(f"Language: {target_lang}")
    
    all_entries = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract EPUB
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find all XHTML/HTML files
        text_files = []
        for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
            text_files.extend(Path(temp_dir).rglob(ext))
        
        print(f"Found {len(text_files)} files")
        
        for xhtml_file in sorted(text_files):
            # Skip navigation/cover files
            if any(skip in xhtml_file.name.lower() for skip in ['nav', 'cover', 'toc']):
                continue
            
            try:
                with open(xhtml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                entries = extract_ruby_entries(soup, target_lang)
                
                if entries:
                    all_entries.extend(entries)
                    print(f"  {xhtml_file.name}: {len(entries)} entries")
            
            except Exception as e:
                print(f"  Error in {xhtml_file.name}: {e}", file=sys.stderr)
    
    print(f"\nTotal entries: {len(all_entries)}")
    
    # Save JSON
    if output_file:
        output_path = Path(output_file)
    elif output_base:
        epub_name = re.sub(r'[-_][a-z]+$', '', epub_path.stem)  # Remove language suffix
        output_dir = Path(output_base) / target_lang
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{epub_name}.json"
    else:
        output_path = epub_path.with_suffix('.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to: {output_path}")
    return all_entries

def main():
    parser = argparse.ArgumentParser(description='Convert EPUB with ruby tags to JSON list')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-l', '--lang', help='Target language code')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE)
    
    args = parser.parse_args()
    
    # Detect language
    target_lang = args.lang or detect_language_from_filename(args.epub_file)
    if not target_lang:
        print("Error: Could not detect language. Use --lang", file=sys.stderr)
        sys.exit(1)
    
    entries = process_epub(args.epub_file, target_lang, args.output, args.output_base)
    
    # Show sample
    if entries:
        print("\nSample entry:")
        print(json.dumps(entries[0], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()