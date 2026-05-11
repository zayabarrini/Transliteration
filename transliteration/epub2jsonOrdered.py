#!/usr/bin/env python3
"""
epub2jsonOrdered.py - Convert EPUB with consistent multilingual paragraph order to JSON

This script is designed for EPUBs where paragraphs appear in a consistent language order
without explicit lang attributes. Handles content split across multiple files by tracking
paragraph sequence positions.
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

# Default language order for the Milano_Multilingual.epub
DEFAULT_LANGUAGE_ORDER = [
    'en', 'de', 'ru', 'ar', 'hi', 'zh', 'ja', 'ko', 'fr', 'pt', 'it', 'es', 'pl', 'el', 'he'
]

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

def extract_paragraphs_with_position(file_path, start_position=0):
    """
    Extract all paragraph texts in order with position tracking.
    Returns (paragraphs, next_position) where each paragraph has position index.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        paragraphs = []
        
        # Find all paragraphs
        all_p = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        current_pos = start_position
        for p in all_p:
            text = p.get_text().strip()
            if text:
                paragraphs.append({
                    'text': text,
                    'position': current_pos
                })
                current_pos += 1
        
        return paragraphs, current_pos
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return [], start_position

def extract_all_paragraphs_with_positions(text_files):
    """
    Extract all paragraphs from all files in order with continuous position tracking.
    """
    all_paragraphs = []
    current_position = 0
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation and cover files
        if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
            continue
        
        print(f"  Processing: {filename} (starting at position {current_position})")
        
        paragraphs, current_position = extract_paragraphs_with_position(xhtml_file, current_position)
        all_paragraphs.extend(paragraphs)
    
    return all_paragraphs

def group_paragraphs_by_sequence(paragraphs, language_order):
    """
    Group paragraphs based on their position, assuming consistent language order.
    Each complete group should have exactly len(language_order) paragraphs.
    
    This function validates the grouping by checking if the paragraphs form
    complete cycles of the language order.
    """
    if not paragraphs:
        return []
    
    group_size = len(language_order)
    translation_groups = []
    
    # Group by position using integer division
    groups_dict = defaultdict(dict)
    
    for para in paragraphs:
        position = para['position']
        group_index = position // group_size
        position_in_group = position % group_size
        
        # Get language for this position
        if position_in_group < len(language_order):
            lang = language_order[position_in_group]
            groups_dict[group_index][lang] = para['text']
    
    # Convert to list and sort by group index
    for group_index in sorted(groups_dict.keys()):
        group = groups_dict[group_index]
        
        # Only add if we have at least one paragraph
        if group:
            translation_groups.append(group)
    
    return translation_groups

def validate_sequence(paragraphs, language_order):
    """
    Validate that the paragraph sequence follows the expected language order.
    Returns validation results and warning messages.
    """
    group_size = len(language_order)
    warnings = []
    
    # Check expected positions for each language
    expected_counts = defaultdict(int)
    actual_counts = defaultdict(int)
    
    for para in paragraphs:
        position = para['position']
        group_index = position // group_size
        position_in_group = position % group_index
        
        if position_in_group < len(language_order):
            expected_lang = language_order[position_in_group]
            expected_counts[expected_lang] += 1
    
    for para in paragraphs:
        actual_counts[para.get('detected_lang', 'unknown')] += 1
    
    # Find potential split issues
    max_position = max([p['position'] for p in paragraphs]) if paragraphs else 0
    expected_total = ((max_position // group_size) + 1) * group_size
    actual_total = len(paragraphs)
    
    if actual_total != expected_total:
        warnings.append(f"Potential split issue: expected {expected_total} paragraphs but found {actual_total}")
    
    return warnings

def extract_title_from_epub(text_files):
    """Extract title from the first suitable file"""
    for xhtml_file in text_files:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for h1 or title
            h1 = soup.find('h1')
            if h1:
                return h1.get_text().strip()
            
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
        
        except Exception:
            continue
    
    return "Multilingual Book"

def process_ordered_epub(epub_file, language_order=None, output_file=None, output_base=None):
    """
    Process an EPUB with consistent paragraph order and convert to JSON
    """
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return []
    
    # Use default language order if not provided
    if language_order is None:
        language_order = DEFAULT_LANGUAGE_ORDER
    
    print(f"Processing EPUB: {epub_path.name}")
    print(f"Language order: {', '.join(language_order)}")
    print(f"Number of languages: {len(language_order)}")
    
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
        
        # Extract all paragraphs with position tracking
        print("\nExtracting paragraphs with position tracking...")
        all_paragraphs = extract_all_paragraphs_with_positions(text_files)
        print(f"Total paragraphs extracted: {len(all_paragraphs)}")
        
        # Show position range
        if all_paragraphs:
            min_pos = min(p['position'] for p in all_paragraphs)
            max_pos = max(p['position'] for p in all_paragraphs)
            print(f"Position range: {min_pos} to {max_pos}")
        
        # Group paragraphs by sequence
        print(f"\nGrouping paragraphs into translation groups...")
        print(f"Expected group size: {len(language_order)} paragraphs")
        
        translation_groups = group_paragraphs_by_sequence(all_paragraphs, language_order)
        print(f"Created {len(translation_groups)} translation groups")
        
        # Verify group integrity
        complete_groups = 0
        incomplete_groups = 0
        missing_languages = []
        
        for group in translation_groups:
            if len(group) == len(language_order):
                complete_groups += 1
            else:
                incomplete_groups += 1
                missing = [lang for lang in language_order if lang not in group]
                if missing:
                    missing_languages.append(missing)
        
        print(f"\nComplete groups (all {len(language_order)} languages): {complete_groups}")
        if incomplete_groups > 0:
            print(f"Incomplete groups (missing languages): {incomplete_groups}")
            if missing_languages:
                print(f"Example missing languages: {missing_languages[0]}")
        
        # Check for file split anomalies
        group_size = len(language_order)
        positions_by_file = defaultdict(list)
        
        for para in all_paragraphs:
            group_idx = para['position'] // group_size
            positions_by_file[group_idx].append(para['position'])
        
        # Find incomplete groups that span multiple files
        split_groups = []
        for group_idx, positions in positions_by_file.items():
            if len(positions) > 0 and len(positions) < group_size:
                # This group is split across files
                split_groups.append(group_idx)
        
        if split_groups:
            print(f"\n⚠️  Warning: {len(split_groups)} groups appear to be split across files")
            print(f"   Groups affected: {split_groups[:10]}...")
            print(f"   These groups have incomplete translations")
        
        # Show sample
        if translation_groups:
            print(f"\n✅ Sample complete translation group:")
            # Find first complete group
            complete_sample = next((g for g in translation_groups if len(g) == len(language_order)), None)
            if complete_sample:
                for i, (lang, text) in enumerate(list(complete_sample.items())[:5]):
                    preview = text[:60] + "..." if len(text) > 60 else text
                    print(f"  {i+1}. {lang}: {preview}")
                if len(complete_sample) > 5:
                    print(f"  ... and {len(complete_sample) - 5} more languages")
            else:
                # Show any group
                sample = translation_groups[0]
                for i, (lang, text) in enumerate(list(sample.items())[:3]):
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
            'total_paragraphs': len(all_paragraphs),
            'total_translation_groups': len(translation_groups),
            'complete_translation_groups': complete_groups,
            'incomplete_translation_groups': incomplete_groups
        }
        
        if split_groups:
            metadata['warning'] = f"{len(split_groups)} translation groups are split across files and may be incomplete"
        
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
            
            json_filename = f"{epub_name}-ordered-ml.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Saved JSON to {output_path}")
        
        return sections

def main():
    parser = argparse.ArgumentParser(description='Convert ordered multilingual EPUB to JSON')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    parser.add_argument('--lang-order', help='Comma-separated list of language codes in order (e.g., "en,de,ru,ar")')
    
    args = parser.parse_args()
    
    # Parse language order if provided
    language_order = None
    if args.lang_order:
        language_order = [lang.strip() for lang in args.lang_order.split(',')]
    else:
        # Use default order
        language_order = DEFAULT_LANGUAGE_ORDER
        print(f"Using default language order with {len(language_order)} languages")
    
    print(f"\n📚 Processing ordered multilingual EPUB file: {args.epub_file}")
    print(f"🔤 Language order: {', '.join(language_order)}")
    print(f"📁 Output base directory: {args.output_base}")
    
    sections = process_ordered_epub(
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
        print(f"  🌐 Languages: {len(sections[0]['language_order'])}")
        print(f"  📄 Total paragraphs extracted: {sections[0]['total_paragraphs']}")
        print(f"  📦 Translation groups created: {sections[0]['total_translation_groups']}")
        print(f"  ✅ Complete groups: {sections[0]['complete_translation_groups']}")
        print(f"  ⚠️  Incomplete groups: {sections[0]['incomplete_translation_groups']}")
        
        if 'warning' in sections[0]:
            print(f"  ⚠️  {sections[0]['warning']}")
        
        # Show output location
        if args.output:
            print(f"  💾 Output: {args.output}")
        else:
            output_name = Path(args.epub_file).stem.replace('_', '-').replace(' ', '-')
            print(f"  💾 Output: {args.output_base}/{output_name}-ordered-ml.json")

if __name__ == '__main__':
    main()