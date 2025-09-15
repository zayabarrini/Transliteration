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
    
    
    # for language in ['de', 'ru', 'ar', 'hi', 'ch', 'ja', 'ko', 'fr', 'pt', 'it', 'es', 'po', 'gr', 'hb']:
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
            
            for row in rows:
                if not row.get('en', '').strip():
                    continue
                    
                # Add the sentence in the target language
                if is_translated:
                    sentence = f"{row['en']} \n\n {row[language]} \n\n"
                else:
                    sentence = f"{row[language]}\n\n"
                
                md_content.append(sentence)
            
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
                os.remove(md_filename)
                print(f"Removed temporary file: {md_filename}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting to EPUB: {e}")

if __name__ == "__main__":
    csv_file_path = '/home/zaya/Downloads/ZayasTimeline.csv'
    output_dir = '/home/zaya/Documents/Ebooks/Flow/Dictionaries/ZayasTimeline'
    dictionary_name = "ZayasTimeline"  # You can change this to whatever dictionary name you want
    generate_epubs(csv_file_path, output_dir, dictionary_name=dictionary_name)