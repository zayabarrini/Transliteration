# CsvRT.py
import csv
import random
from datetime import datetime
import subprocess
import os
import uuid
from pypinyin import pinyin, Style  # For Chinese transliteration
import pykakasi  # For Japanese romanization

def generate_epubs(csv_file_path, output_dir='output', date=None, dictionary_name="Dictionary"):
    """
    Generate EPUB dictionaries from a CSV file.
    
    Args:
        csv_file_path (str): Path to the CSV file
        output_dir (str): Output directory for EPUB files
        date (str): Date string in YYYY-MM-DD format (optional)
        dictionary_name (str): Name of the dictionary to use in titles
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if date is None:
        date = datetime.today().strftime('%Y-%m-%d')
    
    # Initialize Japanese romanization converter
    kakasi = pykakasi.kakasi()
    kakasi.setMode("H", "a")  # Hiragana to romaji
    kakasi.setMode("K", "a")  # Katakana to romaji
    kakasi.setMode("J", "a")  # Kanji to romaji
    kakasi.setMode("r", "Hepburn")  # Use Hepburn romanization
    kakasi.setMode("s", True)  # Add space between words
    kakasi.setMode("C", True)  # Capitalize first letter
    converter = kakasi.getConverter()
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    
    for language in ['ja', 'ch']:
        lang_names = {
            'de': 'German',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'ch': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'fr': 'French',
            'pt': 'Portuguese',
            'it': 'Italian',
            'es': 'Spanish',
            'po': 'Polish',
            'gr': 'Greek',
            'hb': 'Hebrew'
        }
        random_number = random.randint(1, 211)
        
        # Generate both versions (translated and non-translated)
        for version in ['', '-en']:
            is_translated = version == '-en'
            base_name = f"{dictionary_name}-{language}{version}-trans"
            
            metadata = f"""---
title:
  - type: main
    text: {dictionary_name} {lang_names[language]}{' with English-trans' if is_translated else ''}
  - type: subtitle
    text: Vocabulary Builder
creator:
  - role: author
    text: Zaya Barrini
  - role: editor
    text: Zaya Barrini
date: {date}
cover-image: /home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_number}.png
identifier:
  - scheme: UUID
    text: {str(uuid.uuid4())}
publisher: Zaya's Language Press
rights: © {datetime.today().year} Zaya Barrini, CC BY-NC
language: {language}
ibooks:
  version: 1.3.4
...
"""
            md_content = [metadata]
            words = []
            
            for row in rows:
                if row[language].startswith('#'):
                    md_content.append(f"\n{row[language]}\n\n")
                    continue
                    
                if language in row and row[language].strip():
                    if language == 'ch':  # Special handling for Chinese
                        chinese_word = row[language].strip()
                        # Generate pinyin transliteration
                        pinyin_word = ' '.join([p[0] for p in pinyin(chinese_word, style=Style.TONE)])
                        
                        if is_translated:
                            content = f'<ruby>{chinese_word}<rt class="translation">{row["en"].strip()}</rt><rt>{pinyin_word}</rt></ruby>'
                        else:
                            content = f'<ruby>{chinese_word}<rt>{pinyin_word}</rt></ruby>'
                    elif language == 'ja':  # Special handling for Japanese
                        japanese_word = row[language].strip()
                        # Generate romaji transliteration
                        romaji_word = converter.do(japanese_word)
                        
                        if is_translated:
                            content = f'<ruby>{japanese_word}<rt class="translation">{row["en"].strip()}</rt><rt>{romaji_word}</rt></ruby>'
                        else:
                            content = f'<ruby>{japanese_word}<rt>{romaji_word}</rt></ruby>'
                    else:  # Other languages
                        if is_translated:
                            content = f'<ruby>{row[language].strip()}<rt>{row["en"].strip()}</rt></ruby>'
                        else:
                            content = row[language].strip()
                    
                    words.append(content)
                    
                    if len(words) % 10 == 0:
                        md_content.append(', '.join(words[-10:]) + '\n\n')
            
            if words:
                md_content.append(', '.join(words[-(len(words)%10):]) + '\n')
            
            md_filename = os.path.join(output_dir, f"{base_name}.md")
            with open(md_filename, 'w', encoding='utf-8') as md_file:
                md_file.writelines(md_content)
            
            epub_filename = os.path.join(output_dir, f"{base_name}.epub")
            css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/styles4.css"
            
            pandoc_cmd = [
                'pandoc',
                '-s', md_filename,
                '-o', epub_filename,
                '--toc',
                '--toc-depth=2',
                f'--css={css_path}',
                f'--epub-cover-image=/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_number}.png'
            ]
            
            try:
                subprocess.run(pandoc_cmd, check=True)
                print(f"Successfully created {epub_filename}")
                os.remove(md_filename)
                print(f"Removed temporary file: {md_filename}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting to EPUB: {e}")

if __name__ == "__main__":
    csv_file_path = '/home/zaya/Downloads/Words.csv'
    output_dir = '/home/zaya/Documents/Ebooks/Flow/Dictionaries/Base'
    dictionary_name = "Dictionary"  # You can change this to whatever dictionary name you want
    generate_epubs(csv_file_path, output_dir, dictionary_name=dictionary_name)