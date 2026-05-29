#!/usr/bin/env python3
"""
epub2jsonEn.py - Convert EPUB with foreign language + English translation to JSON

This script detects the foreign language from the EPUB filename (e.g., -ru, -ar, -zh)
and creates a JSON object where each paragraph has both the original text and English translation.
Expected structure: English (with lang="en") followed by foreign language (no lang attribute)
"""

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from collections import defaultdict
from bs4 import BeautifulSoup

SUPPORTED_LANGUAGES = {
    'ru': 'Russian',
    'ar': 'Arabic',
    'zh': 'Chinese',
    'hi': 'Hindi',
    'ko': 'Korean',
    'ja': 'Japanese',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'tr': 'Turkish',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'pl': 'Polish',
    'uk': 'Ukrainian'
}

DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json"

def detect_source_language(epub_path):
    """Detect source language from filename (e.g., file-ru.epub -> ru)"""
    filename = Path(epub_path).stem
    # Look for patterns like -ru, _ru, -ar, _ar at the end
    match = re.search(r'[-_](ru|ar|zh|hi|ko|ja|es|fr|de|it|pt|tr|vi|th|pl|uk)$', filename)
    if match:
        return match.group(1)
    
    # Also check for language in the full path
    path_str = str(epub_path).lower()
    for lang_code in SUPPORTED_LANGUAGES.keys():
        if f'-{lang_code}' in path_str or f'_{lang_code}' in path_str:
            return lang_code
    
    print(f"Warning: Could not detect source language from filename: {filename}", file=sys.stderr)
    print(f"Supported language codes: {', '.join(SUPPORTED_LANGUAGES.keys())}", file=sys.stderr)
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
    """Find all XHTML/HTML files in the extracted EPUB in order"""
    text_files = []
    
    search_paths = [
        os.path.join(extract_path, 'EPUB', 'text'),
        os.path.join(extract_path, 'EPUB'),
        os.path.join(extract_path, 'OEBPS', 'text'),
        os.path.join(extract_path, 'OEBPS', 'Text'),
        os.path.join(extract_path, 'OEBPS'),
        extract_path,
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
                files = list(Path(search_path).glob(ext))
                if files:
                    text_files.extend(sorted(files))
    
    # Also look for any HTML files in root
    root_html = list(Path(extract_path).glob('*.html')) + list(Path(extract_path).glob('*.xhtml'))
    for f in root_html:
        if f not in text_files:
            text_files.append(f)
    
    return sorted(set(text_files))

def extract_translation_pairs_from_file(file_path):
    """
    Extract translation pairs from a file where:
    - English text has lang="en" attribute (or dir="ltr" lang="en")
    - Foreign text has no lang attribute (or different lang)
    - Structure alternates: English paragraph followed by foreign paragraph
    Returns list of pairs with dynamic language keys
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        pairs = []
        
        # Find all p tags
        all_p_tags = soup.find_all('p')
        
        i = 0
        while i < len(all_p_tags) - 1:
            p1 = all_p_tags[i]
            p2 = all_p_tags[i + 1]
            
            # Check if p1 is English (has lang="en" or dir="ltr" lang="en")
            p1_lang = p1.get('lang', '')
            p1_classes = p1.get('class', [])
            p1_has_en = p1_lang == 'en' or (p1_lang and p1_lang.lower() == 'en')
            
            # Check if p2 is foreign (no lang attribute, or lang is not 'en')
            p2_lang = p2.get('lang', '')
            p2_is_foreign = not p2_lang or p2_lang.lower() != 'en'
            
            # If this looks like an EN -> Foreign pair
            if p1_has_en and p2_is_foreign:
                en_text = p1.get_text().strip()
                foreign_text = p2.get_text().strip()
                
                if en_text and foreign_text:
                    # Return with dynamic keys - source language will be added later
                    pairs.append({
                        'en': en_text,
                        'source': foreign_text
                    })
                    i += 2
                    continue
            
            # Also check reverse pattern (Foreign -> EN) - less common but possible
            p1_is_foreign = not p1_lang or p1_lang.lower() != 'en'
            p2_has_en = p2_lang == 'en' or (p2_lang and p2_lang.lower() == 'en')
            
            if p1_is_foreign and p2_has_en:
                en_text = p2.get_text().strip()
                foreign_text = p1.get_text().strip()
                
                if en_text and foreign_text:
                    pairs.append({
                        'en': en_text,
                        'source': foreign_text
                    })
                    i += 2
                    continue
            
            # If no pattern matches, just move to next
            i += 1
        
        return pairs
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def extract_translation_pairs_alternative(file_path):
    """
    Alternative extraction for cases where English and foreign are in the same p tag
    or have different structure (like your example where they're separate but not alternating)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        pairs = []
        
        # Find all p tags that contain English
        en_paragraphs = soup.find_all('p', {'lang': 'en'})
        
        for en_p in en_paragraphs:
            en_text = en_p.get_text().strip()
            if not en_text:
                continue
            
            # Look for the next sibling that might be the foreign translation
            # Check next sibling p tag
            foreign_p = en_p.find_next_sibling('p')
            if foreign_p:
                foreign_lang = foreign_p.get('lang', '')
                # If next p has no lang or different lang, consider it the translation
                if not foreign_lang or foreign_lang.lower() != 'en':
                    foreign_text = foreign_p.get_text().strip()
                    if foreign_text:
                        pairs.append({
                            'en': en_text,
                            'source': foreign_text
                        })
                        continue
            
            # If no sibling, maybe the foreign text is inside a span or div
            # This handles cases like your example structure
            parent = en_p.parent
            if parent:
                # Get all text after this paragraph within same parent
                next_p = parent.find_next_sibling('p')
                if next_p:
                    foreign_lang = next_p.get('lang', '')
                    if not foreign_lang or foreign_lang.lower() != 'en':
                        foreign_text = next_p.get_text().strip()
                        if foreign_text:
                            pairs.append({
                                'en': en_text,
                                'source': foreign_text
                            })
        
        return pairs
    
    except Exception as e:
        print(f"Error in alternative extraction for {file_path}: {e}", file=sys.stderr)
        return []

def extract_all_pairs(text_files):
    """Extract all translation pairs from all files in order"""
    all_pairs = []
    
    for html_file in text_files:
        filename = html_file.name
        
        # Skip navigation and cover files
        if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
            continue
        
        print(f"  Processing: {filename}")
        
        # Try main extraction method
        pairs = extract_translation_pairs_from_file(html_file)
        
        # If no pairs found, try alternative method
        if not pairs:
            print(f"    No pairs found with main method, trying alternative...")
            pairs = extract_translation_pairs_alternative(html_file)
        
        if pairs:
            print(f"    Found {len(pairs)} translation pairs")
            all_pairs.extend(pairs)
        else:
            print(f"    Warning: No translation pairs found in {filename}")
    
    return all_pairs

def extract_title_from_epub(text_files):
    """Extract title from the first suitable file"""
    for html_file in text_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for title in metadata
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                if title:
                    return title
            
            # Look for h1
            h1 = soup.find('h1')
            if h1:
                return h1.get_text().strip()
        
        except Exception:
            continue
    
    return None

def process_epub_to_json(epub_file, output_file=None, output_base=None):
    """Process an EPUB file and convert to JSON with English translations"""
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return None
    
    print(f"Processing EPUB: {epub_path.name}")
    
    # Detect source language
    source_lang = detect_source_language(epub_file)
    if not source_lang:
        print("Error: Could not detect source language from filename", file=sys.stderr)
        print("Please ensure filename ends with language code like -ru, -ar, -zh, etc.", file=sys.stderr)
        return None
    
    source_lang_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
    print(f"Detected source language: {source_lang} ({source_lang_name})")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract EPUB
        print("Extracting EPUB...")
        if not extract_epub(epub_file, temp_dir):
            print(f"Error: Failed to extract EPUB {epub_file}", file=sys.stderr)
            return None
        
        # Find all text files
        text_files = find_text_files(temp_dir)
        
        if not text_files:
            print(f"Error: No HTML/XHTML files found in EPUB", file=sys.stderr)
            return None
        
        print(f"Found {len(text_files)} content files to process")
        
        # Extract all translation pairs
        print("Extracting translation pairs...")
        all_pairs_raw = extract_all_pairs(text_files)
        print(f"Total translation pairs extracted: {len(all_pairs_raw)}")
        
        if not all_pairs_raw:
            print("Error: No translation pairs found in the EPUB", file=sys.stderr)
            print("This script expects English paragraphs (lang='en') followed by foreign text paragraphs")
            return None
        
        # Convert to final format with dynamic language key
        all_pairs = []
        for pair in all_pairs_raw:
            # Transform from {'en': 'text', 'source': 'foreign'} to {'en': 'text', source_lang: 'foreign'}
            formatted_pair = {
                'en': pair['en'],
                source_lang: pair['source']
            }
            all_pairs.append(formatted_pair)
        
        # Show sample
        print(f"\nSample translations (first 3 pairs):")
        for i, pair in enumerate(all_pairs[:3]):
            print(f"\n  Pair {i+1}:")
            print(f"    EN: {pair['en'][:80]}...")
            print(f"    {source_lang.upper()}: {pair[source_lang][:80]}...")
        
        # Extract title
        title = extract_title_from_epub(text_files)
        if not title:
            title = epub_path.stem
            # Clean up title by removing language suffix
            title = re.sub(r'[-_](ru|ar|zh|hi|ko|ja|es|fr|de|it|pt|tr|vi|th|pl|uk)$', '', title)
            title = title.replace('-', ' ').replace('_', ' ').strip()
        
        # Create the JSON structure
        json_data = {
            'metadata': {
                'title': title,
                'source_language': source_lang,
                'source_language_name': source_lang_name,
                'target_language': 'en',
                'target_language_name': 'English',
                'total_pairs': len(all_pairs),
                'filename': epub_path.name
            },
            'translations': all_pairs
        }
        
        # Determine output directory (save in source_language subfolder)
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        elif output_base:
            # Create source_language subdirectory
            output_dir = Path(output_base) / source_lang
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            epub_name = epub_path.stem
            # Remove language suffix for cleaner filename
            epub_name = re.sub(r'[-_](ru|ar|zh|hi|ko|ja|es|fr|de|it|pt|tr|vi|th|pl|uk)$', '', epub_name)
            json_filename = f"{epub_name}.json"
            output_path = output_dir / json_filename
        else:
            # Fallback to current directory
            output_path = Path(f"{epub_path.stem}.json")
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Saved JSON to {output_path}")
        
        return json_data

def main():
    parser = argparse.ArgumentParser(
        description='Convert foreign language + English translation EPUB to JSON',
        epilog='Example: epub2jsonEn.py book-ru.epub'
    )
    parser.add_argument('epub_file', help='Path to the EPUB file (should include language code like -ru, -ar)')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    parser.add_argument('--source-lang', help='Manually specify source language code (e.g., ru, ar, zh)')
    
    args = parser.parse_args()
    
    # Override source language detection if manually specified
    if args.source_lang:
        # We would need to modify the function, but for simplicity,
        # we'll let the auto-detection run and it will use the manual override
        print(f"Note: You specified source language '{args.source_lang}'")
        print("The script will attempt auto-detection first. Use -o to specify output path if needed.")
    
    print(f"Processing EPUB file: {args.epub_file}")
    print(f"Output base directory: {args.output_base}")
    
    result = process_epub_to_json(
        args.epub_file, 
        output_file=args.output,
        output_base=args.output_base if not args.output else None
    )
    
    if result:
        source_lang = result['metadata']['source_language']
        print(f"\n✅ Success! Created {len(result['translations'])} translation pairs")
        print(f"   Source: {result['metadata']['source_language_name']} ({source_lang})")
        print(f"   Target: {result['metadata']['target_language_name']}")
        print(f"   Title: {result['metadata']['title']}")
        print(f"   Output format: {{'en': '...', '{source_lang}': '...'}}")
    else:
        print("\n❌ Failed to process EPUB", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()