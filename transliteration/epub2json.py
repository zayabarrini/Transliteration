#!/usr/bin/env python3
"""
epub2json.py - Convert EPUB with parallel text to JSON for language learning readers

The script detects the language code from the EPUB filename (e.g., title-ar.epub, title-es.epub)
and uses that as the target language, with English as the source language.
Output is saved to language-specific directories.
Handles paragraph pairs that span across multiple files.
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

# Supported language codes - expanded to include all common codes
SUPPORTED_LANGUAGES = [
    'ar', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
    'la', 'pl', 'pt', 'ru', 'sw', 'tr', 'zh', 'en', 'th', 'vi'
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
    language_codes = ['ar', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 'it', 'ja', 'ko', 
                      'la', 'pl', 'pt', 'ru', 'sw', 'th', 'tr', 'zh', 'en']
    
    # First, normalize the filename by replacing common separators
    # This helps with pattern matching
    normalized_stem = re.sub(r'[_\s]+', '-', stem)
    
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
        
        # Pattern 6: _db_lang pattern
        if re.search(rf'_db_{lang}(\.|$)', stem, re.IGNORECASE):
            return lang
        
        # Pattern 7: Check normalized version with hyphens
        if re.search(rf'-db-{lang}$', normalized_stem, re.IGNORECASE):
            return lang
        if re.search(rf'-{lang}$', normalized_stem, re.IGNORECASE):
            return lang
    
    # If still not found, try splitting by common separators and check the last part
    # Split by hyphens, underscores, spaces
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

def get_language_unicode_ranges(lang_code):
    """Get Unicode ranges for character detection for the specified language"""
    ranges = {
        'zh': r'[\u4e00-\u9fff]',  # Chinese
        'ja': r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]',  # Japanese
        'ko': r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]',  # Korean
        'ar': r'[\u0600-\u06FF\u0750-\u077F]',  # Arabic
        'he': r'[\u0590-\u05FF]',  # Hebrew
        'ru': r'[\u0400-\u04FF]',  # Russian
        'el': r'[\u0370-\u03FF]',  # Greek
        'hi': r'[\u0900-\u097F]',  # Hindi (Devanagari)
        'th': r'[\u0E00-\u0E7F]',  # Thai
        'vi': r'[\u1EA0-\u1EF9]',  # Vietnamese
        'pl': r'[\u0104\u0105\u0106\u0107\u0118\u0119\u0141\u0142\u0143\u0144\u015A\u015B\u0179\u017A\u017B\u017C]',  # Polish
        'tr': r'[\u011E\u011F\u0130\u0131\u015E\u015F\u00FC]',  # Turkish
        'fr': r'[àâäéèêëîïôöùûüÿçœ]',  # French accents
        'es': r'[áéíóúüñ]',  # Spanish accents
        'de': r'[äöüß]',  # German
        'pt': r'[áâãàçéêíóôõúü]',  # Portuguese
        'it': r'[àèéìíîòóùú]',  # Italian
    }
    
    # For languages without specific ranges, return a pattern that matches common non-Latin scripts
    # or just any non-ASCII as fallback
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
        os.path.join(extract_path, 'contents'),
        os.path.join(extract_path, 'Text'),
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            # Find all .xhtml, .html, .htm files
            for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
                text_files.extend(Path(search_path).glob(ext))
    
    return sorted(text_files)

def extract_all_paragraphs_with_context(file_path, target_lang, lang_range):
    """
    Extract all paragraphs from a file, preserving order and tracking 
    which paragraphs are target language and which are English.
    Returns a list of tuples (text, is_target_lang, is_english)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all paragraphs
        author_paragraphs = soup.find_all('p', class_='author')
        if not author_paragraphs:
            author_paragraphs = soup.find_all('p')
        
        result = []
        for p in author_paragraphs:
            text = p.get_text().strip()
            if not text:
                continue
            
            # Check language attributes
            p_lang = p.get('lang', '')
            
            # Determine if this is target language or English
            is_target = False
            is_english = False
            
            if p_lang == target_lang:
                is_target = True
            elif p_lang != target_lang and p_lang:
                # If it has a lang attribute but not target, check if it's English
                is_english = True
            else:
                # No language attribute, try character detection
                has_target_chars = bool(re.search(lang_range, text))
                is_english_chars = bool(re.match(r'^[A-Za-z0-9\s\.,!?\'"-]+$', text))
                
                if has_target_chars:
                    is_target = True
                elif is_english_chars:
                    is_english = True
            
            result.append((text, is_target, is_english))
        
        return result
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return []

def process_epub_file(epub_file, target_lang, output_file=None, output_base=None):
    """Process an EPUB file and convert to JSON with cross-file synchronization"""
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
        
        # Get Unicode range for target language detection
        lang_range = get_language_unicode_ranges(target_lang)
        
        # Process all files sequentially to maintain paragraph order
        all_paragraphs = []
        
        for xhtml_file in text_files:
            filename = xhtml_file.name
            
            # Skip navigation and cover files
            if 'nav' in filename.lower() or 'cover' in filename.lower() or 'toc' in filename.lower():
                continue
            
            print(f"  Processing: {filename}")
            
            # Extract paragraphs with context
            file_paragraphs = extract_all_paragraphs_with_context(xhtml_file, target_lang, lang_range)
            all_paragraphs.extend(file_paragraphs)
        
        # Now pair the paragraphs: target language with English
        paired_paragraphs = []
        i = 0
        
        while i < len(all_paragraphs):
            text, is_target, is_english = all_paragraphs[i]
            
            # If this is target language, look for English partner
            if is_target:
                # Look ahead for English text
                j = i + 1
                found_english = None
                
                while j < len(all_paragraphs):
                    _, next_is_target, next_is_english = all_paragraphs[j]
                    
                    if next_is_english:
                        found_english = all_paragraphs[j][0]
                        break
                    elif next_is_target:
                        # Found another target text without English in between - might be a sequence
                        break
                    j += 1
                
                if found_english:
                    paired_paragraphs.append({
                        target_lang: text,
                        'en': found_english
                    })
                    i = j + 1  # Skip the English paragraph we used
                    continue
                else:
                    # No English partner found, add as standalone (might be processed later)
                    paired_paragraphs.append({
                        target_lang: text,
                        'en': "[MISSING TRANSLATION]"
                    })
                    i += 1
            
            # If this is English, look for target language partner (reverse direction)
            elif is_english:
                # Look ahead for target language text
                j = i + 1
                found_target = None
                
                while j < len(all_paragraphs):
                    _, next_is_target, next_is_english = all_paragraphs[j]
                    
                    if next_is_target:
                        found_target = all_paragraphs[j][0]
                        break
                    elif next_is_english:
                        # Found another English without target in between
                        break
                    j += 1
                
                if found_target:
                    paired_paragraphs.append({
                        target_lang: found_target,
                        'en': text
                    })
                    i = j + 1  # Skip the target paragraph we used
                    continue
                else:
                    # No target partner found
                    i += 1
            
            # If it's neither (unclassified), just move on
            else:
                i += 1
        
        # Remove duplicates
        unique_paragraphs = []
        seen_pairs = set()
        
        for para in paired_paragraphs:
            pair_key = (para[target_lang], para['en'])
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                unique_paragraphs.append(para)
        
        # Group into sections (simple approach - all in one section)
        sections = [{
            'id': 'main',
            'filename': 'all_content',
            'title': {target_lang: None},
            'paragraphs': unique_paragraphs
        }]
        
        print(f"Created 1 section with {len(unique_paragraphs)} paragraph pairs")
        
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
            
            output_dir = Path(output_base) / target_lang
            output_dir.mkdir(parents=True, exist_ok=True)
            
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