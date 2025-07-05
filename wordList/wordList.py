# CsvRT.py
import csv
import random
from datetime import datetime
import subprocess
import os
import uuid

def generate_epubs(csv_file_path, output_dir='output', date=None, dictionary_name="Dictionary"):
    os.makedirs(output_dir, exist_ok=True)
    
    if date is None:
        date = datetime.today().strftime('%Y-%m-%d')
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    
    # for language in ['de', 'ru', 'ar', 'hi', 'ch', 'ja']:
    for language in ['de', 'ru', 'ar', 'hi', 'ch', 'ja', 'ko', 'fr', 'it', 'es', 'po', 'gr', 'hb']:
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
            base_name = f"{dictionary_name}-{language}{version}"
            
            metadata = f"""---
title:
  - type: main
    text: {dictionary_name} {lang_names[language]}{' with English' if is_translated else ''}
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
                # if not row.get('en', '').strip():
                #     continue
                    
                if row[language].startswith('#'):
                    md_content.append(f"\n{row[language]}\n\n")
                    continue
                    
                if language in row and row[language].strip():
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
            css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/styles3.css"
            
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
            except subprocess.CalledProcessError as e:
                print(f"Error converting to EPUB: {e}")

if __name__ == "__main__":
    csv_file_path = '/home/zaya/Downloads/LGBT.csv'
    output_dir = '/home/zaya/Documents/Ebooks/Flow/Dictionaries/LGBT'
    dictionary_name = "LGBT-Dictionary"  # You can change this to whatever dictionary name you want
    generate_epubs(csv_file_path, output_dir, dictionary_name=dictionary_name)