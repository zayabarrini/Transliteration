#!/usr/bin/env python3
"""
csv_transliteration.py - Adds transliteration columns to CSV for all target languages
Reads input CSV, processes each language column, and adds _translit columns
"""

import csv
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add transliteration module path
TRANSLIT_PATH = Path("/home/zaya/Downloads/Zayas/ZayasTransliteration/transliteration")
sys.path.insert(0, str(TRANSLIT_PATH))

# Import transliteration functions
try:
    from transliteration import filter_language_text, is_language_text, transliterate
    TRANSLIT_AVAILABLE = True
    print("✅ Transliteration module loaded successfully")
except ImportError as e:
    print(f"⚠️  Could not import transliteration module: {e}")
    print("   Will use fallback methods")
    TRANSLIT_AVAILABLE = False

# Language configuration
LANGUAGES = {
    'hindi': {'code': 'hi', 'column': 'hindi', 'script': 'devanagari'},
    'russian': {'code': 'ru', 'column': 'ru', 'script': 'cyrillic'},
    'chinese': {'code': 'zh', 'column': 'zh', 'script': 'hanzi'},
    'japanese': {'code': 'ja', 'column': 'ja', 'script': 'kana_kanji'},
    'korean': {'code': 'ko', 'column': 'ko', 'script': 'hangul'},
    'arabic': {'code': 'ar', 'column': 'ar', 'script': 'arabic'}
}

# Language-specific processing flags
LANGUAGE_NEEDS_TOKENIZATION = {
    'ja': True,   # Japanese needs word segmentation
    'zh': True,   # Chinese needs word segmentation
    'ko': False,  # Korean works character by character
    'ru': False,  # Russian works word by word
    'ar': False,  # Arabic works word by word
    'hi': False   # Hindi works word by word
}

def safe_transliterate(text: str, language: str) -> str:
    """
    Safely transliterate text with error handling
    Returns empty string on failure
    """
    if not text or not text.strip():
        return ""
    
    if not TRANSLIT_AVAILABLE:
        # Fallback: simple character mapping or return original
        return fallback_transliterate(text, language)
    
    try:
        result = transliterate(text, language)
        
        # Handle different return types based on language
        if language == 'ja':
            # Japanese returns list of dicts
            if isinstance(result, list) and all(isinstance(x, dict) for x in result):
                # Extract hepburn romanization
                translit_parts = []
                for item in result:
                    if 'hepburn' in item and item['hepburn']:
                        translit_parts.append(item['hepburn'])
                    elif 'orig' in item:
                        translit_parts.append(item['orig'])
                return ' '.join(translit_parts)
            else:
                return str(result) if result else ""
        
        elif language == 'ko':
            # Korean returns list of [char, trans] pairs
            if isinstance(result, list) and all(isinstance(x, (list, tuple)) and len(x) >= 2 for x in result):
                return ' '.join(trans for _, trans in result)
            else:
                return str(result) if result else ""
        
        elif language == 'zh':
            # Chinese returns HTML with ruby annotations
            # Extract just the pinyin text
            if result and isinstance(result, str):
                # Remove HTML tags to get plain pinyin
                import re
                pinyin_text = re.sub(r'<[^>]+>', ' ', result)
                pinyin_text = re.sub(r'\s+', ' ', pinyin_text).strip()
                return pinyin_text
            return str(result) if result else ""
        
        else:
            # Hindi, Russian, Arabic - return as string
            return str(result) if result else ""
    
    except Exception as e:
        print(f"⚠️  Transliteration error for language {language}: {e}")
        print(f"   Text: {text[:50]}...")
        return fallback_transliterate(text, language)

def fallback_transliterate(text: str, language: str) -> str:
    """
    Simple fallback transliteration when main module fails
    """
    # Common character mappings for fallback
    if language == 'ru':
        # Basic Cyrillic to Latin mapping
        cyrillic_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': "'", 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
            'Ъ': '', 'Ы': 'Y', 'Ь': "'", 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        return ''.join(cyrillic_map.get(char, char) for char in text)
    
    elif language == 'ar':
        # Very basic Arabic mapping (should be improved)
        arabic_map = {
            'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
            'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
            'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
            'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y'
        }
        return ''.join(arabic_map.get(char, char) for char in text)
    
    else:
        # Return original for other languages
        return text

def process_csv(input_path: Path, output_path: Path, languages: List[str]):
    """
    Main function to process CSV and add transliteration columns
    """
    print(f"📖 Reading input CSV: {input_path}")
    
    # Read original CSV
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    
    print(f"   Found {len(rows)} rows")
    
    # Add transliteration columns to fieldnames
    translit_columns = []
    for lang in languages:
        lang_code = LANGUAGES.get(lang, {}).get('code', lang)
        translit_col = f"{lang_code}_translit"
        if translit_col not in fieldnames:
            translit_columns.append(translit_col)
    
    fieldnames.extend(translit_columns)
    
    # Process each row
    for idx, row in enumerate(rows):
        if (idx + 1) % 100 == 0:
            print(f"   Processing row {idx + 1}/{len(rows)}...")
        
        for lang in languages:
            lang_code = LANGUAGES.get(lang, {}).get('code', lang)
            lang_column = LANGUAGES.get(lang, {}).get('column', lang)
            translit_col = f"{lang_code}_translit"
            
            # Get original text
            original_text = row.get(lang_column, '')
            
            # Skip if already has transliteration
            if row.get(translit_col, '').strip():
                continue
            
            # Add transliteration
            if original_text and original_text.strip():
                translit = safe_transliterate(original_text, lang)
                row[translit_col] = translit
            else:
                row[translit_col] = ""
    
    # Write output CSV
    print(f"💾 Writing output CSV: {output_path}")
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Successfully created {output_path}")
    
    # Print summary
    print("\n📊 Summary:")
    for lang in languages:
        lang_code = LANGUAGES.get(lang, {}).get('code', lang)
        translit_col = f"{lang_code}_translit"
        non_empty = sum(1 for row in rows if row.get(translit_col, '').strip())
        print(f"   {lang_code.upper()}: {non_empty}/{len(rows)} rows have transliteration")

def add_hindi_translit_only(input_path: Path, output_path: Path):
    """
    Special function for when you only have Hindi data and need Hindi transliteration
    """
    print(f"📖 Processing Hindi-only CSV: {input_path}")
    
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    
    # Add hi_translit column if not present
    if 'hi_translit' not in fieldnames:
        fieldnames.append('hi_translit')
    
    for idx, row in enumerate(rows):
        hindi_text = row.get('hindi', '')
        if hindi_text and not row.get('hi_translit', ''):
            row['hi_translit'] = safe_transliterate(hindi_text, 'hi')
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Added Hindi transliteration to {output_path}")

def create_template_with_translit_columns(output_path: Path, languages: List[str]):
    """
    Create an empty CSV template with transliteration columns for Google Sheets
    """
    base_columns = ['id', 'category', 'subcategory', 'hindi', 'english']
    
    # Add language columns and their transliteration columns
    for lang in languages:
        lang_code = LANGUAGES.get(lang, {}).get('code', lang)
        base_columns.append(lang)
        base_columns.append(f"{lang_code}_translit")
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(base_columns)
    
    print(f"✅ Created template CSV with transliteration columns: {output_path}")
    print(f"   Columns: {', '.join(base_columns)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add transliteration columns to CSV')
    parser.add_argument('input', type=str, help='Input CSV file path')
    parser.add_argument('-o', '--output', type=str, help='Output CSV file path', default=None)
    parser.add_argument('-l', '--languages', type=str, nargs='+', 
                       default=['hindi', 'russian', 'chinese', 'japanese', 'korean', 'arabic'],
                       help='Languages to process')
    parser.add_argument('--template', action='store_true', 
                       help='Create template CSV instead of processing')
    parser.add_argument('--hindi-only', action='store_true',
                       help='Only add Hindi transliteration')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if args.template:
        # Create template
        output_path = Path(args.output) if args.output else Path("vocabulary_template.csv")
        create_template_with_translit_columns(output_path, args.languages)
    
    elif args.hindi_only:
        # Only add Hindi transliteration
        output_path = Path(args.output) if args.output else input_path.parent / f"{input_path.stem}_with_translit{input_path.suffix}"
        add_hindi_translit_only(input_path, output_path)
    
    else:
        # Full processing
        output_path = Path(args.output) if args.output else input_path.parent / f"{input_path.stem}_with_translit{input_path.suffix}"
        process_csv(input_path, output_path, args.languages)