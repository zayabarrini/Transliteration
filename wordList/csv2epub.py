# TagSystemCJ.py
import csv
import os
import random
import subprocess
import uuid
from datetime import datetime

import jieba.posseg as pseg
from pypinyin import Style, pinyin  # For Chinese transliteration


def analyze_chinese_syntax(text):
    """Simple syntax analysis for Chinese words"""
    
    # Complete exclusion set for punctuation
    EXCLUDE_CHARS = {
        " ", ".", ",", "!", "?", "。", "，", "！", "？", "、", 
        "「", "」", "『", "』", "（", "）", "《", "》", "“", "”", 
        "‘", "’", "…", "—", "：", ":", "；", ";", "～", "°", "º"
    }
    
    def is_punctuation(word):
        return word in EXCLUDE_CHARS
    
    if is_punctuation(text):
        return "PUNCT"
    
    words = list(pseg.cut(text))
    if not words:
        return "X"
    
    word, pos = words[0]  # Take first word for single character/word analysis
    
    # Enhanced heuristic rules based on POS tags
    if pos.startswith("v"):  # Verbs (v, vd, vn, etc.)
        return "V"
    elif pos.startswith("n"):  # Nouns
        return "N"
    elif pos.startswith("a"):  # Adjectives
        return "ADJ"
    elif pos.startswith("d"):  # Adverbs
        return "ADV"
    elif pos in ["r", "nh", "nr"]:  # Pronouns, names
        return "PRON"
    elif pos in ["c", "p", "cc"]:  # Conjunctions, prepositions
        return "CONJ" if pos in ["c", "cc"] else "PREP"
    elif pos in ["m", "q"]:  # Numbers, quantifiers
        return "NUM"
    elif pos in ["u", "y", "e"]:  # Auxiliary, modal particles
        return "PART"
    else:
        return "X"

def generate_triple_annotation_epub(csv_file_path, output_dir="output", dictionary_name="Dictionary"):
    """
    Generate EPUB with triple annotation (translation, word, pinyin) and syntax tags
    
    Args:
        csv_file_path (str): Path to the CSV file with 'en' and 'ch' columns
        output_dir (str): Output directory for EPUB files
        dictionary_name (str): Name of the dictionary
    """
    os.makedirs(output_dir, exist_ok=True)
    date = datetime.today().strftime("%Y-%m-%d")
    random_number = random.randint(1, 211)

    # Read CSV data
    items = []
    current_header = ""
    
    with open(csv_file_path, "r", encoding="utf-8") as csvfile:
        # Use comma as delimiter and skip the header row
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            en_text = row.get('en', '').strip()
            ch_text = row.get('ch', '').strip()
            
            # Skip empty rows
            if not en_text and not ch_text:
                continue
            
            # Check if this is a header row (starts with #)
            if en_text.startswith('#') or ch_text.startswith('#'):
                # Use the English text as header, removing the # symbol
                header_text = en_text.lstrip('#').strip() if en_text.startswith('#') else ch_text.lstrip('#').strip()
                if header_text:
                    current_header = header_text
                continue
            
            # Skip rows where Chinese text is missing
            if not ch_text:
                continue
            
            # Process Chinese word
            syntax_tag = analyze_chinese_syntax(ch_text)
            
            # Generate pinyin
            try:
                pinyin_text = " ".join([p[0] for p in pinyin(ch_text, style=Style.TONE)])
            except:
                pinyin_text = ""  # Fallback for words that can't be transliterated
            
            items.append({
                'header': current_header,
                'translation': en_text,
                'word': ch_text,
                'transliteration': pinyin_text,
                'syntax': syntax_tag
            })

    # Generate metadata
    metadata = f"""---
title:
  - type: main
    text: {dictionary_name} Chinese with Syntax Tags
  - type: subtitle
    text: Vocabulary Builder with Color-Coded Syntax
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
language: zh
ibooks:
  version: 1.3.4
...
"""

    # Generate markdown content
    md_content = [metadata]
    
    current_header = ""
    for item in items:
        # Add header if it changed
        if item['header'] != current_header:
            if current_header:  # Add spacing before new header
                md_content.append("\n")
            md_content.append(f"# {item['header']}\n\n")
            current_header = item['header']
        
        # Create the triple annotation with syntax class
        ruby_content = f"""<ruby>
    <span class="translation">{item['translation']}</span>
    <span class="word-token {item['syntax'].lower()}">{item['word']}</span>
    <rt class="pinyin">{item['transliteration']}</rt>
</ruby>"""
        
        md_content.append(ruby_content + "  \n")
        
    # Write markdown file
    md_filename = os.path.join(output_dir, f"{dictionary_name}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.writelines(md_content)

    # Convert to EPUB
    epub_filename = os.path.join(output_dir, f"{dictionary_name}.epub")
    css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/styles-ccc-csv.css"

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
        # Remove temporary markdown file
        os.remove(md_filename)
        print(f"Removed temporary file: {md_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting to EPUB: {e}")
    except FileNotFoundError:
        print("Pandoc not found. Please install pandoc to generate EPUB files.")

if __name__ == "__main__":
    csv_file_path = "/home/zaya/Downloads/ch.csv"  # Change this to your CSV path
    output_dir = "/home/zaya/Downloads/"
    dictionary_name = "Parts_of_Speech_db-tags-ch"
    
    # Use the full version with syntax analysis
    generate_triple_annotation_epub(csv_file_path, output_dir, dictionary_name=dictionary_name)