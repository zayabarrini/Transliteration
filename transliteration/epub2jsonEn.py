#!/usr/bin/env python3
"""
epub2jsonEn.py - Convert EPUB with foreign language + English translation to JSON

This script detects the foreign language from the EPUB filename (e.g., -ru, -ar, -zh)
and creates a JSON object matching the structure of epub2json.py.
Output is saved to language-specific directories.
Handles paragraph pairs within each file.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

# Supported language codes
SUPPORTED_LANGUAGES = [
    'ar', 'bn', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
    'la', 'mr', 'pa', 'pl', 'pt', 'ru', 'sw', 'ta', 'te', 'th', 'tr', 'ur', 
    'vi', 'zh', 'en'
]

# Default output base directory
DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json"

def detect_language_from_filename(filename):
    """
    Detect the source language from the EPUB filename.
    Matches the pattern from epub2json.py
    """
    stem = Path(filename).stem
    
    # List of all supported language codes
    language_codes = SUPPORTED_LANGUAGES
    
    # First, normalize the filename by replacing common separators
    normalized_stem = re.sub(r'[_\s]+', '-', stem)
    
    # Try different patterns
    for lang in language_codes:
        # Pattern 1: -lang at the end
        if re.search(rf'-{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
        
        # Pattern 2: _lang at the end
        if re.search(rf'_{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
        
        # Pattern 3: .lang at the end
        if re.search(rf'\.{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
        
        # Pattern 4: space then lang at the end
        if re.search(rf'\s+{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
        
        # Pattern 5: -db-lang pattern
        if re.search(rf'-db-{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
        
        # Pattern 6: -{lang} at the end of normalized stem
        if re.search(rf'-{lang}$', normalized_stem, re.IGNORECASE):
            return lang
    
    # If still not found, try splitting by common separators and check the last part
    parts = re.split(r'[\s_\-]+', stem)
    if parts:
        last_part = parts[-1].lower()
        if last_part in language_codes:
            return last_part
        
        # Check if the last part is something like "db-hi" and extract the code
        if '-' in last_part:
            subparts = last_part.split('-')
            if len(subparts) > 1 and subparts[-1] in language_codes:
                return subparts[-1]
    
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
    
    # Common paths for content in EPUBs
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
            # Find all .xhtml, .html, .htm files
            for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
                text_files.extend(Path(search_path).glob(ext))
    
    return sorted(text_files)

def extract_translation_pairs_from_file(file_path, source_lang):
    """
    Extract translation pairs from a file where:
    - English text has lang="en" attribute
    - Source language text has no lang attribute or has source_lang
    Returns list of pairs with keys: 'en' and source_lang
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
            
            p1_text = p1.get_text().strip()
            p2_text = p2.get_text().strip()
            
            if not p1_text or not p2_text:
                i += 1
                continue
            
            # Check language attributes
            p1_lang = p1.get('lang', '')
            p2_lang = p2.get('lang', '')
            
            # Case 1: English (lang="en") followed by source language
            if p1_lang == 'en' and (not p2_lang or p2_lang == source_lang):
                pairs.append({
                    'en': p1_text,
                    source_lang: p2_text
                })
                i += 2
                continue
            
            # Case 2: Source language followed by English (lang="en")
            elif (not p1_lang or p1_lang == source_lang) and p2_lang == 'en':
                pairs.append({
                    'en': p2_text,
                    source_lang: p1_text
                })
                i += 2
                continue
            
            # Case 3: Both have explicit language attributes
            elif p1_lang == 'en' and p2_lang == source_lang:
                pairs.append({
                    'en': p1_text,
                    source_lang: p2_text
                })
                i += 2
                continue
            
            elif p1_lang == source_lang and p2_lang == 'en':
                pairs.append({
                    'en': p2_text,
                    source_lang: p1_text
                })
                i += 2
                continue
            
            i += 1
        
        return pairs
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def extract_all_pairs(text_files, source_lang):
    """Extract all translation pairs from all files in order"""
    all_pairs = []
    
    for html_file in text_files:
        filename = html_file.name
        
        # Skip navigation and cover files
        if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
            continue
        
        print(f"  Processing: {filename}")
        
        pairs = extract_translation_pairs_from_file(html_file, source_lang)
        
        if pairs:
            print(f"    Found {len(pairs)} translation pairs")
            all_pairs.extend(pairs)
        else:
            print(f"    Warning: No translation pairs found in {filename}")
    
    return all_pairs

def extract_title_from_xhtml(text_files, source_lang):
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

def get_section_id_from_filename(filename):
    """Extract section ID from filename"""
    base = os.path.splitext(filename)[0]
    
    # Handle patterns like ch001_split_000.xhtml
    match = re.search(r'(ch\d+)_split_\d+', base)
    if match:
        return match.group(1)
    
    # Handle title_page splits
    match = re.search(r'(title_page)_split_\d+', base)
    if match:
        return match.group(1)
    
    return base

def process_epub_file(epub_file, source_lang, output_file=None, output_base=None):
    """Process an EPUB file and convert to JSON matching epub2json.py structure"""
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
        print(f"Source language: {source_lang}")
        
        # Group files by section
        sections_dict = {}
        
        for xhtml_file in text_files:
            filename = xhtml_file.name
            
            # Skip navigation and cover files
            if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
                continue
            
            section_id = get_section_id_from_filename(filename)
            
            # Extract translation pairs
            pairs = extract_translation_pairs_from_file(xhtml_file, source_lang)
            
            if pairs:
                if section_id not in sections_dict:
                    title = extract_title_from_xhtml([xhtml_file], source_lang)
                    
                    sections_dict[section_id] = {
                        'id': section_id,
                        'filename': filename,
                        'title': {source_lang: title} if title else None,
                        'paragraphs': pairs
                    }
                else:
                    sections_dict[section_id]['paragraphs'].extend(pairs)
        
        # Convert to list and sort
        sections = []
        for section_id in sorted(sections_dict.keys()):
            section = sections_dict[section_id]
            
            # Remove duplicates
            unique_paragraphs = []
            seen_pairs = set()
            
            for para in section['paragraphs']:
                pair_key = (para.get(source_lang, ''), para.get('en', ''))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    unique_paragraphs.append(para)
            
            section['paragraphs'] = unique_paragraphs
            sections.append(section)
        
        print(f"Created {len(sections)} sections with {sum(len(s['paragraphs']) for s in sections)} paragraph pairs")
        
        # Save to JSON
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        elif output_base:
            # Auto-generate output filename with language code in directory
            epub_name = epub_path.stem
            # Remove language code from the end if present to avoid duplication
            for lang in SUPPORTED_LANGUAGES:
                if epub_name.endswith(f'-{lang}') or epub_name.endswith(f'_{lang}'):
                    epub_name = epub_name[:-(len(lang)+1)]
                    break
                # Also check for -db-lang pattern
                db_pattern = f'-db-{lang}'
                if db_pattern in epub_name:
                    epub_name = epub_name.replace(db_pattern, '')
                    break
            
            # Clean up the filename: replace spaces and underscores with hyphens
            epub_name = re.sub(r'[_\s]+', '-', epub_name)
            epub_name = re.sub(r'-+', '-', epub_name)
            epub_name = epub_name.strip('-')
            
            # Save in source_language subdirectory (matches epub2json.py structure)
            output_dir = Path(output_base) / source_lang
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_filename = f"{epub_name}.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        
        return sections

def main():
    parser = argparse.ArgumentParser(
        description='Convert foreign language + English translation EPUB to JSON',
        epilog='Example: epub2jsonEn.py book-ru.epub'
    )
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('-l', '--lang', help='Source language code (e.g., ru, ar, zh). If not provided, detected from filename')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    
    args = parser.parse_args()
    
    # Detect language from filename if not provided
    source_lang = args.lang
    if not source_lang:
        source_lang = detect_language_from_filename(args.epub_file)
        if not source_lang:
            print("Error: Could not detect language from filename. Please specify with --lang", file=sys.stderr)
            print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}", file=sys.stderr)
            sys.exit(1)
    
    print(f"Processing EPUB file: {args.epub_file}")
    print(f"Source language: {source_lang}")
    print(f"Output base directory: {args.output_base}")
    
    sections = process_epub_file(
        args.epub_file, 
        source_lang, 
        output_file=args.output,
        output_base=args.output_base if not args.output else None
    )
    
    # Print summary
    total_paragraphs = sum(len(section['paragraphs']) for section in sections)
    print(f"\nSummary:")
    print(f"  Sections: {len(sections)}")
    print(f"  Total paragraphs: {total_paragraphs}")
    
    if sections and sections[0]['paragraphs']:
        print(f"\nSample paragraph:")
        sample = sections[0]['paragraphs'][0]
        print(f"  {source_lang.upper()}: {sample[source_lang][:50]}...")
        print(f"  EN: {sample['en'][:50]}...")

if __name__ == '__main__':
    main()