#!/usr/bin/env python3
"""
Generate categorized EPUB dictionaries from CSV with category/subcategory structure.
Includes transliteration (pinyin for Chinese, romaji for Japanese).
Uses category as main header and subcategory as subheader in TOC.
"""

import csv
import os
import random
import subprocess
import uuid
from collections import defaultdict
from datetime import datetime

import pykakasi  # For Japanese romanization
from pypinyin import Style, pinyin  # For Chinese transliteration


def generate_epubs(csv_file_path, output_dir="output", date=None, dictionary_name="Dictionary"):
    """
    Generate EPUB dictionaries from a CSV file using category/subcategory hierarchy
    with transliteration support for Chinese and Japanese.

    Args:
        csv_file_path (str): Path to the CSV file
        output_dir (str): Output directory for EPUB files
        date (str): Date string in YYYY-MM-DD format (optional)
        dictionary_name (str): Name of the dictionary to use in titles
    """
    os.makedirs(output_dir, exist_ok=True)

    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    # Initialize Japanese romanization converter
    kakasi = pykakasi.kakasi()
    kakasi.setMode("H", "a")  # Hiragana to romaji
    kakasi.setMode("K", "a")  # Katakana to romaji
    kakasi.setMode("J", "a")  # Kanji to romaji
    kakasi.setMode("r", "Hepburn")  # Use Hepburn romanization
    kakasi.setMode("s", True)  # Add space between words
    kakasi.setMode("C", True)  # Capitalize first letter
    converter = kakasi.getConverter()

    with open(csv_file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # Languages that need special transliteration handling
    cj_languages = ["zh", "ja"]
    other_languages = ["ar", "hi", "ko", "ru", "de", "fr", "it", "es", "po", "gr", "hb"]
    languages = cj_languages + other_languages
    
    lang_names = {
        "de": "German",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "pt": "Portuguese",
        "it": "Italian",
        "es": "Spanish",
        "po": "Polish",
        "gr": "Greek",
        "hb": "Hebrew",
    }
    
    random_number = random.randint(1, 211)

    for language in languages:
        if not any(row.get(language, "").strip() for row in rows):
            continue

        # Generate both versions (translated and non-translated)
        for version in ["", "-en"]:
            is_translated = version == "-en"
            base_name = f"{dictionary_name}-{language}{version}-category-cj"
            
            # Group words by category and subcategory
            categorized_words = defaultdict(lambda: defaultdict(list))
            
            for row in rows:
                word_text = row.get(language, "").strip()
                if not word_text:
                    continue
                    
                if row.get("en", "").startswith("#"):
                    continue
                    
                category = row.get("category", "Uncategorized").strip() or "Uncategorized"
                subcategory = row.get("subcategory", "General").strip() or "General"
                
                # Handle transliteration for Chinese and Japanese
                if language == "zh":
                    # Generate pinyin transliteration
                    pinyin_word = " ".join([p[0] for p in pinyin(word_text, style=Style.TONE)])
                    
                    if is_translated:
                        english = row.get("en", "").strip()
                        content = f'<ruby>{word_text}<rt class="translation">{english}</rt><rt>{pinyin_word}</rt></ruby>'
                    else:
                        content = f"<ruby>{word_text}<rt>{pinyin_word}</rt></ruby>"
                        
                elif language == "ja":
                    # Generate romaji transliteration
                    romaji_word = converter.do(word_text)
                    
                    if is_translated:
                        english = row.get("en", "").strip()
                        content = f'<ruby>{word_text}<rt class="translation">{english}</rt><rt>{romaji_word}</rt></ruby>'
                    else:
                        content = f"<ruby>{word_text}<rt>{romaji_word}</rt></ruby>"
                        
                else:
                    # Other languages - standard handling
                    if is_translated:
                        english = row.get("en", "").strip()
                        content = f'<ruby>{word_text}<rt>{english}</rt></ruby>'
                    else:
                        content = word_text
                        
                categorized_words[category][subcategory].append(content)

            # Build markdown content with hierarchical structure
            md_content = []
            
            # Metadata header
            metadata = f"""---
title:
  - type: main
    text: {dictionary_name} {lang_names[language]}{' with English' if is_translated else ''}
  - type: subtitle
    text: Categorized Vocabulary Builder with Transliteration
creator:
  - role: author
    text: Zaya Barrini
  - role: editor
    text: Zaya Barrini
date: {date}
cover-image: /home/zaya/Downloads/Zayas/zayaweb/apps/web/static/css/img/Bing/bing{random_number}.png
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
            md_content.append(metadata)
            md_content.append("\n")
            
            # Generate TOC structure with categories as H1 and subcategories as H2
            for category, subcategories in sorted(categorized_words.items()):
                md_content.append(f"# {category}\n\n")
                
                for subcategory, words in sorted(subcategories.items()):
                    md_content.append(f"## {subcategory}\n\n")
                    
                    # Format words based on language
                    if language == "ar":
                        # Arabic uses dots as separators
                        formatted_words = ". ".join(words)
                    else:
                        # Other languages use commas
                        formatted_words = ", ".join(words)
                    
                    md_content.append(f"{formatted_words}\n\n")
                    
                    # Add page break after each subcategory for better readability
                    md_content.append('\\newpage\n\n')

            # Write markdown file
            md_filename = os.path.join(output_dir, f"{base_name}.md")
            with open(md_filename, "w", encoding="utf-8") as md_file:
                md_file.writelines(md_content)

            # Convert to EPUB
            epub_filename = os.path.join(output_dir, f"{base_name}.epub")
            
            # Use appropriate CSS - for CJ languages use the enhanced CSS
            if language == "ar":
                css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/styles3-ar.css"
            elif language in ["zh", "ja"]:
                css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/styles4.css"
            else:
                css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/styles3.css"

            pandoc_cmd = [
                "pandoc",
                "-s",
                md_filename,
                "-o",
                epub_filename,
                "--toc",
                "--toc-depth=2",
                f"--css={css_path}",
                f"--epub-cover-image=/home/zaya/Downloads/Zayas/zayaweb/apps/web/static/css/img/Bing/bing{random_number}.png",
            ]

            try:
                subprocess.run(pandoc_cmd, check=True)
                print(f"Successfully created {epub_filename}")
                os.remove(md_filename)
                print(f"Removed temporary file: {md_filename}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting to EPUB: {e}")


if __name__ == "__main__":
    csv_file_path = "/home/zaya/Downloads/vocabulary_template.csv"
    output_dir = "/home/zaya/Downloads/Zayas/ZayasBooks/categorized_cj"
    dictionary_name = "Vocabulary-Categories"
    generate_epubs(csv_file_path, output_dir, dictionary_name=dictionary_name)