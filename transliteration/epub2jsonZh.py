#!/usr/bin/env python3
"""
epub2jsonMulti.py - Convert EPUB with multiple language parallel text to JSON

Handles structure where ALL translations for a sentence appear consecutively,
then the next sentence in ALL languages follows.
Chinese (zh) has no lang attribute (base language) but is interleaved with others.
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
        os.path.join(extract_path, 'OEBPS', 'Text'),
        os.path.join(extract_path, 'OEBPS'),
        extract_path,
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for ext in ['*.xhtml', '*.html', '*.htm']:
                files = list(Path(search_path).glob(ext))
                if files:
                    text_files.extend(sorted(files))
    
    # Sort by numeric sequences in filename
    def sort_key(path):
        numbers = re.findall(r'\d+', path.name)
        return [int(n) for n in numbers] if numbers else [0]
    
    return sorted(set(text_files), key=sort_key)

def should_skip_element(element):
    """Check if an element or its parent is inside a skipped div"""
    parent = element.parent
    while parent:
        if parent.name == 'div' and parent.get('class'):
            classes = parent.get('class', [])
            if any('fnote' in c for c in classes):
                return True
        parent = parent.parent
    return False

def extract_paragraphs_with_lang(file_path):
    """
    Extract all paragraphs with their language info in document order.
    Returns list of {'text': text, 'lang': lang} where lang is None for Chinese.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        paragraphs = []
        
        # Find all p tags (skip those inside fnote divs)
        for p in soup.find_all('p'):
            if should_skip_element(p):
                continue
            
            text = p.get_text().strip()
            if not text:
                continue
            
            # Get language from lang attribute (or None for Chinese)
            lang = p.get('lang', '')
            if lang:
                # Clean language code (e.g., 'zh-CN' -> 'zh')
                lang = lang.split('-')[0]
                # Only include if supported
                if lang not in SUPPORTED_LANGUAGES:
                    continue
            else:
                # No lang attribute = Chinese
                lang = 'zh'
            
            paragraphs.append({
                'text': text,
                'lang': lang
            })
        
        return paragraphs
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def group_by_sentence_clusters(all_paragraphs):
    """
    Group paragraphs into sentence clusters where each cluster contains 
    one paragraph per language in the same relative order.
    
    The pattern is: [zh, ru, en, ar, hi, ja, ko] for sentence 1,
    then [zh, ru, en, ar, hi, ja, ko] for sentence 2, etc.
    """
    if not all_paragraphs:
        return []
    
    # First, detect the language order from the first few paragraphs
    language_order = []
    seen_langs = set()
    
    for para in all_paragraphs[:50]:  # Look at first 50 paragraphs to determine pattern
        lang = para['lang']
        if lang not in seen_langs:
            seen_langs.add(lang)
            language_order.append(lang)
        # Once we have a reasonable set, break
        if len(language_order) >= 10:
            break
    
    print(f"  Detected language order: {language_order}")
    
    # Now group paragraphs sequentially based on language order
    groups = []
    current_group = {}
    
    # If we detected a language order, use it to align
    if language_order:
        # Reset index and rebuild groups based on the pattern
        expected_lang_index = 0
        current_group = {}
        
        for para in all_paragraphs:
            lang = para['lang']
            
            # If this is the expected next language in the pattern
            if expected_lang_index < len(language_order) and lang == language_order[expected_lang_index]:
                current_group[lang] = para['text']
                expected_lang_index += 1
                
                # If we've completed a full group
                if expected_lang_index == len(language_order):
                    groups.append(current_group)
                    current_group = {}
                    expected_lang_index = 0
            else:
                # Pattern broken - might be a new sentence or missing translation
                # If we have a partial group, check if it's complete enough
                if current_group:
                    # If we have at least Chinese, save it
                    if 'zh' in current_group:
                        groups.append(current_group)
                    current_group = {}
                
                # Start new group with this paragraph
                expected_lang_index = 0
                if lang == language_order[expected_lang_index]:
                    current_group[lang] = para['text']
                    expected_lang_index += 1
                else:
                    # This language doesn't match expected pattern, create single-item group
                    groups.append({lang: para['text']})
                    expected_lang_index = 0
    else:
        # Fallback: simple sequential grouping without pattern detection
        # Each group is a single paragraph
        for para in all_paragraphs:
            groups.append({para['lang']: para['text']})
    
    # Post-process: merge consecutive groups that are incomplete
    merged_groups = []
    i = 0
    while i < len(groups):
        if i + 1 < len(groups):
            # If current group doesn't have Chinese and next group does, they might need merging
            if 'zh' not in groups[i] and 'zh' in groups[i + 1]:
                merged = groups[i].copy()
                merged.update(groups[i + 1])
                merged_groups.append(merged)
                i += 2
                continue
        merged_groups.append(groups[i])
        i += 1
    
    return merged_groups

def extract_all_paragraphs(text_files):
    """Extract all paragraphs from all files in order with language detection"""
    all_paragraphs = []
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation, cover, and toc files
        skip_patterns = ['nav', 'cover', 'toc', 'titlepage']
        if any(pattern in filename.lower() for pattern in skip_patterns):
            continue
        
        print(f"  Processing: {filename}")
        
        paragraphs = extract_paragraphs_with_lang(xhtml_file)
        print(f"    Found {len(paragraphs)} paragraphs")
        
        # Debug: show first few paragraphs
        if paragraphs and len(all_paragraphs) < 10:
            print(f"    Sample: {paragraphs[0]['lang']}: {paragraphs[0]['text'][:50]}...")
        
        all_paragraphs.extend(paragraphs)
    
    return all_paragraphs

def extract_title_from_epub(text_files):
    """Extract title from the first suitable file"""
    for xhtml_file in text_files:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for h1 or h2 with Chinese text (no lang)
            for tag in ['h1', 'h2']:
                headers = soup.find_all(tag)
                for h in headers:
                    if not h.get('lang'):
                        text = h.get_text().strip()
                        if text:
                            return text
            
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
        for f in text_files:
            print(f"  - {f.name}")
        
        # Extract all paragraphs with language info
        print("\nExtracting paragraphs with language info...")
        all_paragraphs = extract_all_paragraphs(text_files)
        print(f"Total paragraphs extracted: {len(all_paragraphs)}")
        
        # Group paragraphs by sentence clusters
        print("\nGrouping paragraphs into sentence clusters...")
        translation_groups = group_by_sentence_clusters(all_paragraphs)
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
        if title:
            print(f"\nTitle: {title}")
        else:
            title = epub_path.stem
        
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
            
            print(f"\nSaved JSON to {output_path}")
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
            
            print(f"\nSaved JSON to {output_path}")
        
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
            print(f"\nSample translation groups (first 5):")
            for i, group in enumerate(sections[0]['paragraphs'][:5]):
                print(f"\n  Group {i+1}:")
                for lang, text in group.items():
                    preview = text[:60] + "..." if len(text) > 60 else text
                    print(f"    {lang.upper()}: {preview}")

if __name__ == '__main__':
    main()