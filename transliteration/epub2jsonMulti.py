#!/usr/bin/env python3
"""
epub2jsonOrdered.py - Convert multilingual EPUB to clean JSON

This script processes EPUBs where:
- English text has NO lang attribute (original/base text)
- Other languages have explicit lang attributes and are translations
- Languages available: 'en', 'de', 'ar', 'hi', 'ja', 'ko', 'zh', 'ru', etc.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

# Default output base directory for multilingual JSON
DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml"

# The correct language order based on your merged EPUB structure
# English (no lang attribute, original) should come first
# Then all translations in the order they appear in the merged file
DEFAULT_LANGUAGE_ORDER = ['en', 'de', 'ar', 'hi', 'ja', 'ko', 'zh', 'ru']

# Unicode ranges for Cyrillic characters (Russian)
CYRILLIC_RANGES = [
    (0x0400, 0x04FF),  # Cyrillic
    (0x0500, 0x052F),  # Cyrillic Supplement
]

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
        os.path.join(extract_path, 'OEBPS', 'Text'),
        os.path.join(extract_path, 'content'),
        os.path.join(extract_path, 'contents'),
        os.path.join(extract_path, 'Text'),
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
                text_files.extend(Path(search_path).glob(ext))
    
    # Also search recursively
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.endswith(('.xhtml', '.html', '.htm', '.xml')):
                text_files.append(Path(root) / file)
    
    return sorted(set(text_files))

def is_cyrillic(text: str) -> bool:
    """Check if text contains Cyrillic characters (Russian)"""
    if not text:
        return False
    
    # Count Cyrillic characters
    cyrillic_count = 0
    total_chars = 0
    
    for char in text:
        if char.isalpha():
            total_chars += 1
            code_point = ord(char)
            for start, end in CYRILLIC_RANGES:
                if start <= code_point <= end:
                    cyrillic_count += 1
                    break
    
    # If more than 30% of alphabetic characters are Cyrillic, consider it Russian
    if total_chars > 0:
        return (cyrillic_count / total_chars) > 0.3
    return False

def detect_language(element) -> Optional[str]:
    """
    Detect the language of an element.
    Prefers the lang attribute, but handles the case where Calibre incorrectly marks Russian as 'en'.
    """
    lang = element.get('lang')
    
    if lang:
        # If the text contains Cyrillic and lang is 'en', it's actually Russian
        if lang == 'en':
            text = element.get_text().strip()
            if is_cyrillic(text):
                return 'ru'
        return lang
    
    return None

def is_base_language_element(element) -> bool:
    """
    Determine if an element is the base language (English).
    Base language elements have NO lang attribute.
    """
    return element.get('lang') is None

def is_translation_element(element) -> bool:
    """
    Determine if an element is a translation.
    Translation elements have a lang attribute (or are implicitly Russian).
    """
    return detect_language(element) is not None

def extract_text_from_element(element) -> str:
    """Extract and clean text from an element"""
    text = element.get_text().strip()
    # Clean up extra whitespace, normalize spaces
    text = ' '.join(text.split())
    return text

def extract_translation_groups(file_path) -> List[Dict[str, str]]:
    """
    Extract translation groups from merged EPUB structure.
    Pattern: English (no lang) followed by translations (with lang attributes)
    Handles multiple tag types: p, h1, h2, h3, etc.
    Special handling: Russian paragraphs incorrectly marked as 'en' by Calibre.
    """
    groups = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all text-bearing elements
        all_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        i = 0
        while i < len(all_elements):
            current_elem = all_elements[i]
            
            # Check if this is a base language element (no lang attribute)
            if is_base_language_element(current_elem):
                base_text = extract_text_from_element(current_elem)
                
                if base_text:
                    # Create a group starting with base language (English)
                    group = OrderedDict()
                    group['en'] = base_text
                    
                    # Look ahead for translations (elements with lang attributes)
                    j = i + 1
                    translation_count = 0
                    expected_translations = 7  # de, ar, hi, ja, ko, zh, ru
                    
                    while j < len(all_elements) and translation_count < expected_translations:
                        next_elem = all_elements[j]
                        next_lang = detect_language(next_elem)
                        
                        # If it has a detected language, it's a translation
                        if next_lang:
                            text = extract_text_from_element(next_elem)
                            if text:
                                group[next_lang] = text
                                translation_count += 1
                            j += 1
                        # If we encounter another base language element without lang, stop this group
                        elif is_base_language_element(next_elem):
                            break
                        else:
                            # Skip any other elements
                            j += 1
                    
                    # Add group if it has more than just the base language
                    if len(group) > 1:
                        groups.append(group)
                    
                    # Move to next element after processing this group
                    i = j if j > i else i + 1
                else:
                    i += 1
            else:
                i += 1
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    return groups

def extract_all_content(text_files) -> List[Dict[str, str]]:
    """Extract all translation groups from all files"""
    all_groups = []
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation, cover, toc, and boilerplate files
        skip_keywords = ['nav', 'cover', 'toc', 'titlepage', 'copy', 'copyright', 
                        'termes', 'index', 'bibli', 'appendice', 'notes']
        if any(keyword in filename.lower() for keyword in skip_keywords):
            print(f"  Skipping: {filename}")
            continue
        
        print(f"  Processing: {filename}")
        
        # Extract translation groups
        groups = extract_translation_groups(xhtml_file)
        if groups:
            all_groups.extend(groups)
            print(f"    Found {len(groups)} translation groups")
            # Show sample of Russian detection
            for group in groups[:2]:
                if 'ru' in group:
                    ru_text = group['ru'][:50] + "..." if len(group['ru']) > 50 else group['ru']
                    print(f"      ✓ Russian detected: {ru_text}")
    
    return all_groups

def extract_title_from_epub(text_files) -> str:
    """Extract title from the EPUB"""
    # Look for title in specific order
    for xhtml_file in text_files:
        filename = xhtml_file.name
        if 'title' in filename.lower() or 'titre' in filename.lower():
            try:
                with open(xhtml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for h1 or h2 with no lang attribute (base language)
                for heading in ['h1', 'h2']:
                    elem = soup.find(heading)
                    if elem and is_base_language_element(elem):
                        title = extract_text_from_element(elem)
                        if title:
                            return title
                
                # Look for title tag
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                    if title:
                        return title
            
            except Exception:
                continue
    
    # Try to find h1 in any file
    for xhtml_file in text_files[:10]:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            h1 = soup.find('h1')
            if h1 and is_base_language_element(h1):
                title = extract_text_from_element(h1)
                if title:
                    return title
        except Exception:
            continue
    
    return "Multilingual Book"

def normalize_groups(groups, target_language_order) -> List[Dict[str, str]]:
    """
    Ensure all groups have all languages in the correct order.
    Fill missing languages with empty strings.
    """
    normalized_groups = []
    
    for group in groups:
        normalized_group = OrderedDict()
        
        # Add languages in the target order
        for lang in target_language_order:
            if lang in group:
                normalized_group[lang] = group[lang]
            else:
                normalized_group[lang] = ""  # Empty string for missing languages
        
        normalized_groups.append(normalized_group)
    
    return normalized_groups

def fix_alignment(groups: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Fix the alignment of en and ru values by shifting them up one position.
    This handles the case where the extraction got the order wrong.
    """
    if len(groups) < 2:
        return groups
    
    # Create a copy of the groups
    fixed_groups = []
    
    # Store the first group's en and ru to use at the end
    first_en = groups[0].get('en', '')
    first_ru = groups[0].get('ru', '')
    
    # For each group except the last one, take en and ru from the next group
    for i in range(len(groups) - 1):
        current_group = dict(groups[i])
        next_group = groups[i + 1]
        
        # Replace en and ru with values from the next group
        current_group['en'] = next_group.get('en', '')
        current_group['ru'] = next_group.get('ru', '')
        
        fixed_groups.append(OrderedDict(current_group))
    
    # For the last group, use the first group's en and ru
    if len(groups) > 0:
        last_group = dict(groups[-1])
        last_group['en'] = first_en
        last_group['ru'] = first_ru
        fixed_groups.append(OrderedDict(last_group))
    
    return fixed_groups

def process_ordered_epub(epub_file, output_file=None, output_base=None, title=None, lang_order=None):
    """
    Process an EPUB and convert to clean JSON
    """
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return None
    
    print(f"Processing EPUB: {epub_path.name}")
    
    # Parse language order if provided, otherwise use default
    language_order = None
    if lang_order:
        language_order = [lang.strip() for lang in lang_order.split(',')]
        print(f"Using provided language order: {', '.join(language_order)}")
    else:
        language_order = DEFAULT_LANGUAGE_ORDER
        print(f"Using default language order: {', '.join(language_order)}")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract EPUB
        print("\nExtracting EPUB...")
        if not extract_epub(epub_file, temp_dir):
            print(f"Error: Failed to extract EPUB {epub_file}", file=sys.stderr)
            return None
        
        # Find all text files
        text_files = find_text_files(temp_dir)
        
        if not text_files:
            print(f"Error: No XHTML/HTML files found in EPUB", file=sys.stderr)
            return None
        
        print(f"Found {len(text_files)} content files")
        
        # Extract all translation groups
        print("\nExtracting translation groups...")
        print("  Note: Russian detection is based on Cyrillic characters (Calibre bug workaround)")
        all_groups = extract_all_content(text_files)
        
        if not all_groups:
            print("Error: No translation groups found in EPUB", file=sys.stderr)
            print("Make sure your EPUB has base language elements (no lang attribute) followed by translations (with lang attribute)")
            return None
        
        print(f"\nTotal translation groups extracted: {len(all_groups)}")
        
        # Fix alignment of en and ru values
        print("\nFixing alignment of en and ru values...")
        all_groups = fix_alignment(all_groups)
        
        # Normalize groups to have all languages
        print(f"\nNormalizing groups with {len(language_order)} languages...")
        normalized_groups = normalize_groups(all_groups, language_order)
        
        # Count complete vs incomplete groups
        complete_groups = 0
        groups_with_base = 0
        groups_with_russian = 0
        
        for group in normalized_groups:
            if group.get('en', ''):
                groups_with_base += 1
            if group.get('ru', ''):
                groups_with_russian += 1
            if all(text != "" for text in group.values()):
                complete_groups += 1
        
        print(f"Groups with English text: {groups_with_base}/{len(normalized_groups)}")
        print(f"Groups with Russian text: {groups_with_russian}/{len(normalized_groups)}")
        print(f"Complete groups (all languages present): {complete_groups}/{len(normalized_groups)}")
        
        # Show sample groups
        if normalized_groups:
            print(f"\n✅ Sample translation groups (after alignment fix):")
            for i, group in enumerate(normalized_groups[:3]):
                print(f"\n  Group {i+1}:")
                for lang, text in list(group.items())[:5]:
                    preview = text[:60] + "..." if len(text) > 60 else text
                    status = "✓" if text else "✗"
                    lang_display = lang
                    if lang == 'ru':
                        lang_display = "ru (Cyrillic detected)"
                    print(f"    [{status}] {lang_display}: {preview if preview else '[MISSING]'}")
                if len(group) > 5:
                    print(f"    ... and {len(group) - 5} more languages")
        
        # Extract title if not provided
        if not title:
            title = extract_title_from_epub(text_files)
        
        # Create the clean JSON structure
        output_data = [{
            "id": "main",
            "filename": "all_content",
            "title": title,
            "language_order": language_order,
            "paragraphs": normalized_groups
        }]
        
        # Save to JSON
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Saved JSON to {output_path}")
        elif output_base:
            # Auto-generate output filename
            epub_name = epub_path.stem
            
            # Clean up the filename
            epub_name = re.sub(r'[_\s]+', '-', epub_name)
            epub_name = re.sub(r'-+', '-', epub_name)
            epub_name = epub_name.strip('-')
            
            output_dir = Path(output_base)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_filename = f"{epub_name}-clean.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Saved JSON to {output_path}")
        
        return output_data

def main():
    parser = argparse.ArgumentParser(description='Convert multilingual EPUB to clean JSON')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    parser.add_argument('--title', help='Book title (overrides auto-detection)')
    parser.add_argument('--lang-order', default='en,de,ar,hi,ja,ko,zh,ru',
                       help='Comma-separated language order (default: "en,de,ar,hi,ja,ko,zh,ru")')
    
    args = parser.parse_args()
    
    print(f"\n📚 Processing multilingual EPUB file: {args.epub_file}")
    print(f"📁 Output base directory: {args.output_base}")
    print(f"🔍 Russian detection: Using Cyrillic character detection (Calibre bug workaround)")
    print(f"🌐 Base language: English (no lang attribute)")
    
    result = process_ordered_epub(
        args.epub_file,
        output_file=args.output,
        output_base=args.output_base if not args.output else None,
        title=args.title,
        lang_order=args.lang_order
    )
    
    # Print summary
    if result:
        print(f"\n" + "="*60)
        print(f"📊 FINAL SUMMARY")
        print(f"="*60)
        print(f"  📖 File: {os.path.basename(args.epub_file)}")
        print(f"  📝 Title: {result[0]['title']}")
        print(f"  🌐 Language order: {', '.join(result[0]['language_order'])}")
        print(f"  📦 Translation groups: {len(result[0]['paragraphs'])}")
        
        # Count complete groups
        complete_groups = sum(1 for g in result[0]['paragraphs'] if all(text for text in g.values()))
        print(f"  ✅ Complete groups: {complete_groups}")
        print(f"  ⚠️  Incomplete groups: {len(result[0]['paragraphs']) - complete_groups}")
        
        # Count Russian groups
        russian_groups = sum(1 for g in result[0]['paragraphs'] if g.get('ru', ''))
        print(f"  🇷🇺 Groups with Russian: {russian_groups}")
        
        # Show output location
        if args.output:
            print(f"  💾 Output: {args.output}")
        else:
            output_name = Path(args.epub_file).stem.replace('_', '-').replace(' ', '-')
            print(f"  💾 Output: {args.output_base}/{output_name}-clean.json")

if __name__ == '__main__':
    main()