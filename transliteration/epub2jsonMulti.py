#!/usr/bin/env python3
"""
epub2jsonViolence.py - Convert the "暴力的拓扑学" (Topology of Violence) EPUB to JSON

This script is specifically designed for the Chinese-original multilingual EPUB where:
- Chinese (zh) is the original without lang attribute
- Other languages have explicit lang attributes
- Content inside <div class="fnote1"> and <div class="fnote"> should be skipped
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

# Language order for this specific EPUB (based on the pattern in the content)
# Order observed: en, ar, hi, ja, ko, zh, ru
# But zh appears without lang attribute, so we need to detect it by position
DEFAULT_LANGUAGE_ORDER = ['en', 'ar', 'hi', 'ja', 'ko', 'zh', 'ru']

# Default output base directory for multilingual JSON
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

def should_skip_element(element):
    """Check if an element is inside a footnote div that should be skipped"""
    # Check if element is inside any footnote div
    for parent in element.parents:
        if parent.name == 'div':
            classes = parent.get('class', [])
            if 'fnote' in str(classes) or 'fnote1' in str(classes):
                return True
    return False

def extract_content_with_position(file_path, start_position=0, target_lang='zh'):
    """
    Extract all h2 and p content in order, skipping footnotes.
    Returns (content_items, next_position) where each item has text, lang, and position.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        content_items = []
        
        # Find all h2 and p tags in document order
        all_elements = soup.find_all(['h2', 'p'])
        
        current_pos = start_position
        for elem in all_elements:
            # Skip if inside footnote
            if should_skip_element(elem):
                continue
            
            text = elem.get_text().strip()
            if not text:
                continue
            
            # Determine language
            p_lang = elem.get('lang', '')
            
            # For h2 tags, they might be titles in Chinese or Russian
            if elem.name == 'h2':
                # h2 tags are titles - Russian has lang attribute, Chinese doesn't
                if p_lang == 'ru':
                    lang = 'ru'
                else:
                    # No lang attribute means Chinese (original)
                    lang = target_lang
            else:
                # For p tags
                if p_lang and p_lang in DEFAULT_LANGUAGE_ORDER:
                    lang = p_lang
                elif p_lang == 'ltr' or not p_lang:
                    # Check if it looks like Chinese characters
                    if re.search(r'[\u4e00-\u9fff]', text):
                        lang = target_lang
                    else:
                        # Fallback to English detection
                        if re.match(r'^[A-Za-z0-9\s\.,!?\'"-]+$', text):
                            lang = 'en'
                        else:
                            # Unknown, skip
                            continue
                else:
                    continue
            
            content_items.append({
                'text': text,
                'lang': lang,
                'position': current_pos,
                'tag': elem.name
            })
            current_pos += 1
        
        return content_items, current_pos
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return [], start_position

def extract_all_content_with_positions(text_files, target_lang='zh'):
    """
    Extract all content from all files in order with continuous position tracking.
    """
    all_content = []
    current_position = 0
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation and cover files
        if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
            continue
        
        print(f"  Processing: {filename} (starting at position {current_position})")
        
        content_items, current_position = extract_content_with_position(xhtml_file, current_position, target_lang)
        
        if content_items:
            print(f"    Found {len(content_items)} items")
            all_content.extend(content_items)
    
    return all_content

def detect_language_order_from_content(content_items):
    """
    Detect the language order from the first complete cycle.
    """
    if not content_items:
        return DEFAULT_LANGUAGE_ORDER
    
    # Look at the first 50 items to detect pattern
    sample_items = content_items[:50]
    
    # Find unique languages in order of first appearance
    seen = set()
    order = []
    for item in sample_items:
        if item['lang'] not in seen:
            seen.add(item['lang'])
            order.append(item['lang'])
    
    # Ensure zh is included
    if 'zh' not in order:
        order.append('zh')
    
    return order

def group_content_by_sequence(content_items, language_order):
    """
    Group content items based on their position.
    """
    if not content_items:
        return []
    
    group_size = len(language_order)
    translation_groups = []
    
    # Group by position using integer division
    groups_dict = defaultdict(dict)
    
    for item in content_items:
        position = item['position']
        group_index = position // group_size
        position_in_group = position % group_size
        
        if position_in_group < len(language_order):
            expected_lang = language_order[position_in_group]
            groups_dict[group_index][expected_lang] = item['text']
    
    # Convert to list and sort by group index
    for group_index in sorted(groups_dict.keys()):
        group = groups_dict[group_index]
        if group:
            translation_groups.append(group)
    
    return translation_groups

def extract_title_from_epub(text_files):
    """Extract title from the first suitable file"""
    for xhtml_file in text_files:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for h2 with Chinese title (no lang attribute)
            for h2 in soup.find_all('h2'):
                if not h2.get('lang'):
                    text = h2.get_text().strip()
                    if text:
                        return text
            
            # Look for any h2
            h2 = soup.find('h2')
            if h2:
                return h2.get_text().strip()
        
        except Exception:
            continue
    
    return "暴力的拓扑学"

def process_violence_epub(epub_file, language_order=None, output_file=None, output_base=None):
    """
    Process the violence EPUB file with footnote skipping.
    """
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return []
    
    print(f"Processing EPUB: {epub_path.name}")
    print("Skipping content inside <div class='fnote1'> and <div class='fnote'>")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract EPUB
        print("\nExtracting EPUB...")
        if not extract_epub(epub_file, temp_dir):
            print(f"Error: Failed to extract EPUB {epub_file}", file=sys.stderr)
            return []
        
        # Find all text files
        text_files = find_text_files(temp_dir)
        
        if not text_files:
            print(f"Error: No XHTML/HTML files found in EPUB", file=sys.stderr)
            return []
        
        print(f"Found {len(text_files)} content files to process")
        
        # Extract all content with position tracking
        print("\nExtracting content with position tracking (skipping footnotes)...")
        all_content = extract_all_content_with_positions(text_files, target_lang='zh')
        print(f"Total items extracted: {len(all_content)}")
        
        # Show position range
        if all_content:
            min_pos = min(item['position'] for item in all_content)
            max_pos = max(item['position'] for item in all_content)
            print(f"Position range: {min_pos} to {max_pos}")
        
        # Detect or use provided language order
        if language_order is None:
            print("\nDetecting language order from content...")
            language_order = detect_language_order_from_content(all_content)
            print(f"Detected {len(language_order)} languages in order: {', '.join(language_order)}")
        else:
            print(f"\nUsing provided language order: {', '.join(language_order)}")
        
        # Group content by sequence
        print(f"\nGrouping content into translation groups...")
        print(f"Expected group size: {len(language_order)} items")
        
        translation_groups = group_content_by_sequence(all_content, language_order)
        print(f"Created {len(translation_groups)} translation groups")
        
        # Verify group integrity
        complete_groups = 0
        incomplete_groups = 0
        groups_by_size = defaultdict(int)
        
        for group in translation_groups:
            group_size = len(group)
            groups_by_size[group_size] += 1
            if group_size == len(language_order):
                complete_groups += 1
            else:
                incomplete_groups += 1
        
        print(f"\nGroup size distribution:")
        for size, count in sorted(groups_by_size.items()):
            print(f"  {size} languages: {count} groups")
        
        print(f"\nComplete groups (all {len(language_order)} languages): {complete_groups}")
        if incomplete_groups > 0:
            print(f"Incomplete groups: {incomplete_groups}")
        
        # Show sample
        if translation_groups:
            print(f"\n✅ Sample translation group:")
            # Find first complete group
            complete_sample = next((g for g in translation_groups if len(g) == len(language_order)), None)
            if complete_sample:
                for i, (lang, text) in enumerate(list(complete_sample.items())[:5]):
                    preview = text[:60] + "..." if len(text) > 60 else text
                    print(f"  {i+1}. {lang}: {preview}")
                if len(complete_sample) > 5:
                    print(f"  ... and {len(complete_sample) - 5} more languages")
            else:
                sample = translation_groups[0]
                for lang, text in list(sample.items())[:3]:
                    preview = text[:60] + "..." if len(text) > 60 else text
                    print(f"  {lang}: {preview}")
        
        # Extract title
        title = extract_title_from_epub(text_files)
        
        # Create sections
        metadata = {
            'id': 'main',
            'filename': 'all_content',
            'title': title,
            'language_order': language_order,
            'total_languages': len(language_order),
            'total_items_extracted': len(all_content),
            'total_translation_groups': len(translation_groups),
            'complete_translation_groups': complete_groups,
            'incomplete_translation_groups': incomplete_groups
        }
        
        sections = [{
            **metadata,
            'paragraphs': translation_groups
        }]
        
        # Save to JSON
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
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
            
            json_filename = f"暴力拓扑学-violence-topology.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Saved JSON to {output_path}")
        
        return sections

def main():
    parser = argparse.ArgumentParser(description='Convert violence topology EPUB to JSON')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    parser.add_argument('--lang-order', help='Comma-separated list of language codes in order')
    
    args = parser.parse_args()
    
    # Parse language order if provided
    language_order = None
    if args.lang_order:
        language_order = [lang.strip() for lang in args.lang_order.split(',')]
    
    print(f"\n📚 Processing EPUB: {args.epub_file}")
    print(f"📁 Output base directory: {args.output_base}")
    
    sections = process_violence_epub(
        args.epub_file,
        language_order=language_order,
        output_file=args.output,
        output_base=args.output_base if not args.output else None
    )
    
    # Print summary
    if sections:
        print(f"\n" + "="*60)
        print(f"📊 FINAL SUMMARY")
        print(f"="*60)
        print(f"  📖 File: {os.path.basename(args.epub_file)}")
        print(f"  📝 Title: {sections[0]['title']}")
        print(f"  🌐 Languages ({sections[0]['total_languages']}): {', '.join(sections[0]['language_order'])}")
        print(f"  📄 Total items extracted: {sections[0]['total_items_extracted']}")
        print(f"  📦 Translation groups created: {sections[0]['total_translation_groups']}")
        print(f"  ✅ Complete groups: {sections[0]['complete_translation_groups']}")
        print(f"  ⚠️  Incomplete groups: {sections[0]['incomplete_translation_groups']}")
        
        # Show output location
        if args.output:
            print(f"\n  💾 Output: {args.output}")
        else:
            print(f"\n  💾 Output: {args.output_base}/暴力拓扑学-violence-topology.json")

if __name__ == '__main__':
    main()