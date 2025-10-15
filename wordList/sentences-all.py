# CsvRT.py
import csv
import random
from datetime import datetime
import subprocess
import os
import uuid


def generate_epub(csv_file_path, output_dir="output", date=None):
    os.makedirs(output_dir, exist_ok=True)

    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    with open(csv_file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # Language mapping with names
    lang_names = {
        "de": "German",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi",
        "ch": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "pt": "Portuguese",
        "it": "Italian",
        "es": "Spanish",
        "po": "Polish",
        "gr": "Greek",
        "hb": "Hebrew",
        "en": "English",
    }

    random_number = random.randint(1, 211)
    base_name = "Milano-With-Translations"

    metadata = f"""---
title:
  - type: main
    text: Milano with Translations
  - type: subtitle
    text: Multilingual Vocabulary Builder
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
language: en
ibooks:
  version: 1.3.4
...

"""
    md_content = [metadata]

    for row in rows:
        if not row.get("en", "").strip():
            continue

        # Start with the English sentence
        sentence_block = [f"{row['en']}\n\n"]

        # Add all translations
        for lang_code, lang_name in lang_names.items():
            if lang_code != "en" and lang_code in row and row[lang_code].strip():
                sentence_block.append(f"{row[lang_code]}\n\n")

        sentence_block.append("\n---\n\n")  # Add separator between sentences
        md_content.extend(sentence_block)

    md_filename = os.path.join(output_dir, f"{base_name}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.writelines(md_content)

    epub_filename = os.path.join(output_dir, f"{base_name}.epub")
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
        f"--epub-cover-image=/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_number}.png",
    ]

    try:
        subprocess.run(pandoc_cmd, check=True)
        print(f"Successfully created {epub_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting to EPUB: {e}")


if __name__ == "__main__":
    csv_file_path = "/home/zaya/Downloads/Sentences.csv"
    output_dir = "/home/zaya/Documents/Ebooks/Flow/Grammar/Sentences"
    generate_epub(csv_file_path, output_dir)
