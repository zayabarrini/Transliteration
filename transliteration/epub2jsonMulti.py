#!/usr/bin/env python3
"""
epub2jsonOrdered.py - Convert EPUB with explicit lang attributes to clean JSON

This script processes EPUBs where paragraphs have explicit lang attributes,
grouping them into translation groups and outputting a clean JSON structure.
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
from typing import Any, Dict, List

from bs4 import BeautifulSoup

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

def extract_paragraph_groups(file_path) -> List[Dict[str, str]]:
    """
    Extract groups of paragraphs that form translations.
    Each group contains paragraphs in different languages that appear together.
    """
    groups = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all divs with class="indent" - these contain translation groups
        indent_divs = soup.find_all('div', class_='indent')
        
        if indent_divs:
            # Process each indent div as a translation group
            for div in indent_divs:
                group = OrderedDict()
                
                # Find all paragraphs within this div
                paragraphs = div.find_all('p')
                
                # Also check for headings (h2) that might be part of the group
                headings = div.find_all(['h2', 'h3'])
                all_elements = paragraphs + headings
                
                for elem in all_elements:
                    # Get language from lang attribute
                    lang = elem.get('lang')
                    
                    # If no lang, check parent
                    if not lang:
                        parent = elem.parent
                        while parent and not lang:
                            lang = parent.get('lang')
                            parent = parent.parent
                    
                    # Check if this is a French paragraph (no lang attribute, no color style)
                    # French paragraphs in your sample don't have lang or the color style
                    if not lang:
                        style = elem.get('style', '')
                        # French paragraphs typically don't have color:#00557f
                        if '#00557f' not in style:
                            lang = 'fr'
                        else:
                            # This is a translation with color but no lang - check parent
                            if not lang:
                                lang = 'unknown'
                    
                    text = elem.get_text().strip()
                    if text and lang != 'unknown':
                        group[lang] = text
                
                # Only add if we have at least one paragraph
                if group:
                    # Ensure French is included if missing (sometimes French is the default)
                    if 'fr' not in group and len(group) > 0:
                        # Look for the first paragraph without special styling as French
                        for elem in paragraphs + headings:
                            style = elem.get('style', '')
                            if '#00557f' not in style and not elem.get('lang'):
                                text = elem.get_text().strip()
                                if text:
                                    group['fr'] = text
                                    break
                    
                    groups.append(group)
        else:
            # Fallback: Look for any paragraphs with lang attributes
            all_paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            current_group = OrderedDict()
            for p in all_paragraphs:
                lang = p.get('lang')
                
                # If no lang attribute, check parent
                if not lang:
                    parent = p.parent
                    while parent and not lang:
                        lang = parent.get('lang')
                        parent = parent.parent
                
                # Check if it's French (no lang, no color)
                if not lang:
                    style = p.get('style', '')
                    if '#00557f' not in style:
                        lang = 'fr'
                    else:
                        # Skip colored paragraphs without lang
                        continue
                
                text = p.get_text().strip()
                if not text:
                    continue
                
                # If we see the same language again, start a new group
                if lang in current_group:
                    if current_group:
                        groups.append(current_group)
                    current_group = OrderedDict()
                    current_group[lang] = text
                else:
                    current_group[lang] = text
            
            # Add the last group
            if current_group:
                groups.append(current_group)
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    return groups

def extract_all_groups(text_files):
    """
    Extract all translation groups from all files.
    """
    all_groups = []
    all_languages = set()
    
    for xhtml_file in text_files:
        filename = xhtml_file.name
        
        # Skip navigation, cover, toc, and boilerplate files
        skip_keywords = ['nav', 'cover', 'toc', 'titlepage', 'copy', 'copyright', 
                        'copy', 'termes', 'index', 'bibli', 'appendice', 'notes']
        if any(keyword in filename.lower() for keyword in skip_keywords):
            print(f"  Skipping: {filename}")
            continue
        
        print(f"  Processing: {filename}")
        
        groups = extract_paragraph_groups(xhtml_file)
        if groups:
            all_groups.extend(groups)
            # Track all languages found
            for group in groups:
                all_languages.update(group.keys())
            print(f"    Found {len(groups)} translation groups with languages: {', '.join(sorted(all_languages))}")
    
    return all_groups

def extract_title_from_epub(text_files):
    """Extract title from the EPUB"""
    for xhtml_file in text_files:
        if 'title' in xhtml_file.name.lower() or 'titre' in xhtml_file.name.lower():
            try:
                with open(xhtml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for h1 or title
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()
                    if title:
                        return title
                
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                    if title:
                        return title
            
            except Exception:
                continue
    
    # Try to find h1 in any file
    for xhtml_file in text_files[:5]:
        try:
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
                if title:
                    return title
        except Exception:
            continue
    
    return "Multilingual Book"

def get_language_order(groups):
    """
    Determine the language order from the first few groups.
    Returns list of language codes in order of appearance.
    """
    if not groups:
        return []
    
    # Get the order from the first complete group
    for group in groups:
        if len(group) > 1:
            return list(group.keys())
    
    return []

def process_ordered_epub(epub_file, output_file=None, output_base=None, title=None):
    """
    Process an EPUB with explicit language attributes and convert to clean JSON
    """
    epub_path = Path(epub_file)
    
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_file}", file=sys.stderr)
        return None
    
    print(f"Processing EPUB: {epub_path.name}")
    
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
        all_groups = extract_all_groups(text_files)
        
        if not all_groups:
            print("Error: No translation groups found in EPUB", file=sys.stderr)
            return None
        
        print(f"\nTotal translation groups extracted: {len(all_groups)}")
        
        # Determine language order
        language_order = get_language_order(all_groups)
        print(f"Language order: {', '.join(language_order)}")
        
        # Show sample groups
        if all_groups:
            print(f"\n✅ Sample translation groups:")
            for i, group in enumerate(all_groups[:2]):
                print(f"\n  Group {i+1}:")
                for lang, text in list(group.items())[:4]:
                    preview = text[:60] + "..." if len(text) > 60 else text
                    print(f"    {lang}: {preview}")
        
        # Extract title if not provided
        if not title:
            title = extract_title_from_epub(text_files)
        
        # Create the clean JSON structure
        output_data = [{
            "id": "main",
            "filename": "all_content",
            "title": title,
            "paragraphs": all_groups
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
            
            json_filename = f"{epub_name}.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Saved JSON to {output_path}")
        
        return output_data

def main():
    parser = argparse.ArgumentParser(description='Convert multilingual EPUB to clean JSON format')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    parser.add_argument('--title', help='Book title (overrides auto-detection)')
    
    args = parser.parse_args()
    
    print(f"\n📚 Processing multilingual EPUB file: {args.epub_file}")
    print(f"📁 Output base directory: {args.output_base}")
    
    result = process_ordered_epub(
        args.epub_file,
        output_file=args.output,
        output_base=args.output_base if not args.output else None,
        title=args.title
    )
    
    # Print summary
    if result:
        print(f"\n" + "="*60)
        print(f"📊 FINAL SUMMARY")
        print(f"="*60)
        print(f"  📖 File: {os.path.basename(args.epub_file)}")
        print(f"  📝 Title: {result[0]['title']}")
        print(f"  📦 Translation groups: {len(result[0]['paragraphs'])}")
        
        if result[0]['paragraphs']:
            first_group = result[0]['paragraphs'][0]
            print(f"  🌐 Languages in first group: {', '.join(first_group.keys())}")
        
        # Count total languages across all groups
        all_langs = set()
        for group in result[0]['paragraphs']:
            all_langs.update(group.keys())
        print(f"  🌐 All languages found: {', '.join(sorted(all_langs))}")
        
        # Show output location
        if args.output:
            print(f"  💾 Output: {args.output}")
        else:
            output_name = Path(args.epub_file).stem.replace('_', '-').replace(' ', '-')
            print(f"  💾 Output: {args.output_base}/{output_name}.json")

if __name__ == '__main__':
    main()