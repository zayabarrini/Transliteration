#!/usr/bin/env python3
"""
transliteration_csv.py - Add transliteration columns to vocabulary CSV files
Reads a CSV file and adds transliteration columns for Russian, Chinese, Japanese, Korean, and Arabic.
"""

import csv
import os
import re
import sys
from pathlib import Path

# Add the transliteration module to path
sys.path.insert(0, "/home/zaya/Downloads/Zayas/ZayasTransliteration/transliteration")

# Import the transliteration functions
from transliteration.transliteration import transliterate, get_pinyin_annotations, process_chinese_advanced
import pykakasi


def extract_plain_transliteration(text, language):
    """
    Extract plain text transliteration without HTML/ruby tags.
    
    Args:
        text: Original text to transliterate
        language: Language code (ru, zh, ja, ko, ar)
    
    Returns:
        Plain text transliteration string
    """
    if not text or not text.strip():
        return ""
    
    try:
        if language == "zh":
            # For Chinese, get pinyin using pypinyin directly
            from pypinyin import lazy_pinyin, Style
            pinyin_list = lazy_pinyin(text, style=Style.TONE, neutral_tone_with_five=True)
            return " ".join(pinyin_list)
        
        elif language == "ja":
            # For Japanese, use kakasi directly
            import pykakasi as original_pykakasi

            test_kakasi = original_pykakasi.kakasi()
            result = test_kakasi.convert(text)
            print(f"Transliteration result: {[{'orig': item['orig'], 'trans': item['hira'] or item['hepburn']} for item in result]}")
            # Join the transliteration results, preferring Hepburn if available over Hiragana
            res = " ".join([item['hepburn'] if item['hepburn'] else item['hira'] for item in result])
            return res

        
        elif language == "ko":
            # For Korean, use hangul_romanize
            from hangul_romanize import Transliter
            from hangul_romanize.rule import academic
            transliter = Transliter(rule=academic)
            result = transliter.translit(text)
            # Result is a list of (character, romanization) tuples
            if isinstance(result, list):
                return " ".join([rom for char, rom in result])
            return result
        
        elif language == "ru":
            # For Russian, use the transliterate function but extract plain text
            result = transliterate(text, language)
            # If result is HTML, strip tags
            if isinstance(result, str):
                return re.sub(r'<[^>]+>', '', result)
            return str(result)
        
        elif language == "ar":
            # For Arabic, use the transliterate function
            result = transliterate(text, language)
            if isinstance(result, str):
                return re.sub(r'<[^>]+>', '', result)
            return str(result)
        
        else:
            return text
    
    except Exception as e:
        # print(f"  Error in extract_plain_transliteration for {language}: {e}")
        return text


def add_transliteration_columns(input_csv_path, output_csv_path=None):
    """
    Read a CSV file and add transliteration columns for multiple languages.
    """
    if output_csv_path is None:
        name, ext = os.path.splitext(input_csv_path)
        output_csv_path = f"{name}_transliterated{ext}"
    
    # Detect delimiter (tab or comma)
    with open(input_csv_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        delimiter = '\t' if '\t' in first_line else ','
    
    # print(f"Detected delimiter: {repr(delimiter)}")
    
    # Read the CSV file
    with open(input_csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    
    # print(f"Original fieldnames: {fieldnames}")
    # print(f"Found {len(rows)} rows")
    
    # Add transliteration columns if not already present
    translit_cols = {
        'ru': 'ru_translit',
        'zh': 'zh_translit', 
        'ja': 'ja_translit',
        'ko': 'ko_translit',
        'ar': 'ar_translit'
    }
    
    for col in translit_cols.values():
        if col not in fieldnames:
            fieldnames.append(col)
    
    # Process each row
    for idx, row in enumerate(rows):
        row_id = row.get('id', f'row_{idx}')
        # print(f"\nProcessing {row_id}:")
        
        for lang, col_name in translit_cols.items():
            original_text = row.get(lang, '').strip()
            
            if original_text:
                try:
                    # print(f"  {lang}: '{original_text}'")
                    translit_text = extract_plain_transliteration(original_text, lang)
                    row[col_name] = translit_text
                    # print(f"    -> '{translit_text}'")
                except Exception as e:
                    # print(f"    Error: {e}")
                    row[col_name] = original_text
            else:
                row[col_name] = ''
                # print(f"  {lang}: (empty)")
    
    # Write the updated CSV
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)
    
    # print(f"\n✓ Successfully created {output_csv_path}")
    
    # Show preview
    # if rows:
        # print("\nPreview of first row:")
        # print(f"  Original zh: {rows[0].get('zh', '')}")
        # print(f"  zh_translit: {rows[0].get('zh_translit', '')}")
        # print(f"  Original ja: {rows[0].get('ja', '')}")
        # print(f"  ja_translit: {rows[0].get('ja_translit', '')}")
        # print(f"  Original ko: {rows[0].get('ko', '')}")
        # print(f"  ko_translit: {rows[0].get('ko_translit', '')}")
        # print(f"  Original ru: {rows[0].get('ru', '')}")
        # print(f"  ru_translit: {rows[0].get('ru_translit', '')}")
        # print(f"  Original ar: {rows[0].get('ar', '')}")
        # print(f"  ar_translit: {rows[0].get('ar_translit', '')}")
    
    return rows


if __name__ == "__main__":
    input_file = "/home/zaya/Downloads/vocabulary_template.csv"
    
    if not os.path.exists(input_file):
        # print(f"Error: {input_file} not found!")
        sys.exit(1)
    
    # print(f"Processing: {input_file}")
    add_transliteration_columns(input_file)
    
    # print("\n✓ Done!")