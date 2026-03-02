#!/usr/bin/env python3
"""
epub2json.py - Convert EPUB with parallel text to JSON for language learning readers

The script detects the language code from the EPUB filename (e.g., title-ar.epub, title-es.epub)
and uses that as the target language, with English as the source language.
Output is saved to language-specific directories.
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

from bs4 import BeautifulSoup

# Supported language codes
SUPPORTED_LANGUAGES = [
    'ar', 'de', 'el', 'es', 'fr', 'he', 'id', 'it', 'ja', 'ko', 
    'la', 'pl', 'pt', 'sw', 'tr', 'zh'
]

# Default output base directory
DEFAULT_OUTPUT_BASE = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json"

def detect_language_from_filename(filename):
    """
    Detect the target language from the EPUB filename.
    More robust version that handles spaces, underscores, and various separators.
    """
    stem = Path(filename).stem
    
    import re

    # List of all supported language codes
    language_codes = ['ar', 'de', 'el', 'es', 'fr', 'he', 'id', 'it', 'ja', 'ko', 
                      'la', 'pl', 'pt', 'ru', 'sw', 'tr', 'zh']
    
    # Try different patterns
    for lang in language_codes:
        # Pattern 1: -lang at the end (with possible dot after)
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
        
        # Pattern 5: -db-lang pattern (common in your files)
        if re.search(rf'-db-{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
    
    # If still not found, try splitting by common separators and check the last part
    words = re.split(r'[\s_\-\.]+', stem)
    if words:
        last_word = words[-1].lower()
        if last_word in language_codes:
            return last_word
    
    return None

def get_language_unicode_ranges(lang_code):
    """Get Unicode ranges for character detection for the specified language"""
    ranges = {
        'zh': r'[\u4e00-\u9fff]',  # Chinese
        'ja': r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]',  # Japanese (Hiragana, Katakana, Kanji)
        'ko': r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]',  # Korean (Hangul)
        'ar': r'[\u0600-\u06FF\u0750-\u077F]',  # Arabic
        'he': r'[\u0590-\u05FF]',  # Hebrew
        'ru': r'[\u0400-\u04FF]',  # Russian Cyrillic
        'el': r'[\u0370-\u03FF]',  # Greek
        'th': r'[\u0E00-\u0E7F]',  # Thai
        'vi': r'[\u1EA0-\u1EF9]',  # Vietnamese
    }
    
    # Return the range for the language, or a generic non-Latin range as fallback
    return ranges.get(lang_code, r'[^\u0000-\u007F]')  # Any non-ASCII as fallback

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
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            # Find all .xhtml, .html, .htm files
            for ext in ['*.xhtml', '*.html', '*.htm']:
                text_files.extend(Path(search_path).glob(ext))
    
    return sorted(text_files)

def extract_text_from_xhtml(file_path, target_lang):
    """Extract target language and English text pairs from an XHTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        paragraphs = []
        
        # Get Unicode range for target language detection
        lang_range = get_language_unicode_ranges(target_lang)
        
        # Find all <p> tags (focus on class="author" as in the examples)
        author_paragraphs = soup.find_all('p', class_='author')
        
        if not author_paragraphs:
            # If no author paragraphs, try all paragraphs
            author_paragraphs = soup.find_all('p')
        
        i = 0
        while i < len(author_paragraphs) - 1:
            p1 = author_paragraphs[i]
            p2 = author_paragraphs[i + 1]
            
            # Check language attributes
            p1_lang = p1.get('lang', '')
            p2_lang = p2.get('lang', '')
            
            p1_text = p1.get_text().strip()
            p2_text = p2.get_text().strip()
            
            # Skip empty paragraphs
            if not p1_text or not p2_text:
                i += 1
                continue
            
            # Case 1: First is target language, second is English
            if p1_lang == target_lang and p2_lang != target_lang:
                # Verify with character detection
                if re.search(lang_range, p1_text):
                    paragraphs.append({
                        target_lang: p1_text,
                        'en': p2_text
                    })
                    i += 2
                    continue
            
            # Case 2: First is English, second is target language
            elif p1_lang != target_lang and p2_lang == target_lang:
                if re.search(lang_range, p2_text):
                    paragraphs.append({
                        target_lang: p2_text,
                        'en': p1_text
                    })
                    i += 2
                    continue
            
            # If no language attribute, try character detection
            else:
                p1_has_target = bool(re.search(lang_range, p1_text))
                p2_has_target = bool(re.search(lang_range, p2_text))
                
                # Check if one has target language and the other appears to be English
                # (English is mostly ASCII with possible punctuation)
                p1_is_english = bool(re.match(r'^[A-Za-z0-9\s\.,!?\'"-]+$', p1_text))
                p2_is_english = bool(re.match(r'^[A-Za-z0-9\s\.,!?\'"-]+$', p2_text))
                
                if p1_has_target and p2_is_english:
                    paragraphs.append({
                        target_lang: p1_text,
                        'en': p2_text
                    })
                    i += 2
                    continue
                elif p2_has_target and p1_is_english:
                    paragraphs.append({
                        target_lang: p2_text,
                        'en': p1_text
                    })
                    i += 2
                    continue
            
            i += 1
        
        return paragraphs
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def extract_title_from_xhtml(file_path, target_lang):
    """Extract title from XHTML file, preferring the target language"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for h1 with target language
        h1 = soup.find('h1', lang=target_lang)
        if h1:
            return h1.get_text().strip()
        
        # Look for any h1 that might be in the target language (by character detection)
        lang_range = get_language_unicode_ranges(target_lang)
        for h1 in soup.find_all('h1'):
            text = h1.get_text().strip()
            if re.search(lang_range, text):
                return text
        
        # Look for title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to any h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        return None
    except Exception:
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

def process_epub_file(epub_file, target_lang, output_file=None, output_base=None):
    """Process an EPUB file and convert to JSON"""
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
        print(f"Target language: {target_lang}")
        
        # Group files by section
        sections_dict = {}
        
        for xhtml_file in text_files:
            filename = xhtml_file.name
            
            # Skip navigation and cover files
            if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
                continue
            
            section_id = get_section_id_from_filename(filename)
            
            paragraphs = extract_text_from_xhtml(xhtml_file, target_lang)
            
            if paragraphs:
                if section_id not in sections_dict:
                    title = extract_title_from_xhtml(xhtml_file, target_lang)
                    
                    sections_dict[section_id] = {
                        'id': section_id,
                        'filename': filename,
                        'title': {target_lang: title} if title else None,
                        'paragraphs': paragraphs
                    }
                else:
                    sections_dict[section_id]['paragraphs'].extend(paragraphs)
        
        # Convert to list and sort
        sections = []
        for section_id in sorted(sections_dict.keys()):
            section = sections_dict[section_id]
            
            # Remove duplicates
            unique_paragraphs = []
            seen_pairs = set()
            
            for para in section['paragraphs']:
                pair_key = (para[target_lang], para['en'])
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    unique_paragraphs.append(para)
            
            section['paragraphs'] = unique_paragraphs
            sections.append(section)
        
        print(f"Created {len(sections)} sections with paragraph pairs")
        
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
            
            output_dir = Path(output_base) / target_lang
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean up the filename for JSON output
            json_filename = f"{epub_name}.json"
            output_path = output_dir / json_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)
            
            print(f"Saved JSON to {output_path}")
        
        return sections

def main():
    parser = argparse.ArgumentParser(description='Convert EPUB with parallel text to JSON')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output JSON file path (overrides auto-detection)')
    parser.add_argument('-l', '--lang', help='Target language code (e.g., zh, ja, es). If not provided, detected from filename')
    parser.add_argument('--output-base', default=DEFAULT_OUTPUT_BASE, 
                       help=f'Base output directory (default: {DEFAULT_OUTPUT_BASE})')
    
    args = parser.parse_args()
    
    # Detect language from filename if not provided
    target_lang = args.lang
    if not target_lang:
        target_lang = detect_language_from_filename(args.epub_file)
        if not target_lang:
            print("Error: Could not detect language from filename. Please specify with --lang", file=sys.stderr)
            print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}", file=sys.stderr)
            sys.exit(1)
    
    print(f"Processing EPUB file: {args.epub_file}")
    print(f"Target language: {target_lang}")
    print(f"Output base directory: {args.output_base}")
    
    sections = process_epub_file(
        args.epub_file, 
        target_lang, 
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
        print(f"  {target_lang.upper()}: {sample[target_lang][:50]}...")
        print(f"  EN: {sample['en'][:50]}...")

if __name__ == '__main__':
    main()