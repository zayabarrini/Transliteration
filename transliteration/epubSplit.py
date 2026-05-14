import os
import re
import shutil
import sys

from bs4 import BeautifulSoup

from transliteration.epubManagementNew import (
    create_epub,
    extract_epub,
    find_content_folder,
    get_content_files,
)

# Enhanced multilingual sentence splitting regex
# Fixed multilingual sentence splitting regex
SPLIT_REGEX = re.compile(
    r"""
    # Match sentence-ending punctuation in Chinese/Japanese/Korean
    ([。！？…])           # CJK sentence enders
    \s*                  # Optional whitespace (including none)
    (?=[^)}\]])          # Not followed by closing brackets
    |
    # Western sentence endings with whitespace
    (?<=[.!?])           # Western punctuation
    (?:\s+|$)            # Followed by whitespace or end
    |
    # Colon/semicolon/em dash with whitespace
    (?<=[:;—])           # Colon, semicolon, or em dash
    (?:\s+)              # Followed by whitespace
    """,
    re.VERBOSE,
)


def should_split(sentence: str) -> bool:
    """Check if a sentence should be split (length >=15 chars and contains spaces)"""
    return len(sentence) >= 15 and " " in sentence


def strip_internal_tags(html_content):
    """Remove all internal tags within paragraphs, preserving only text content"""
    soup = BeautifulSoup(html_content, "html.parser")

    for p in soup.find_all("p"):
        # Get all text content, stripping tags
        clean_text = p.get_text(" ", strip=True)
        # Replace the paragraph with clean text
        p.string = clean_text

    return soup


def split_paragraphs(soup):
    """Split paragraphs at sentence boundaries"""
    paragraphs = soup.find_all("p")

    for p in paragraphs:
        text = p.get_text()
        # Skip if too short
        if len(text) < 15:
            continue

        # Better sentence splitting for mixed Chinese/Western text
        sentences = []
        current_sentence = []
        
        for char in text:
            current_sentence.append(char)
            # Check for sentence boundaries in Chinese
            if char in '。！？…、,，:;；' and len(current_sentence) > 1:
                sentences.append(''.join(current_sentence).strip())
                current_sentence = []
            # Check for Western punctuation followed by space or end of string/paragraph
            elif char in '.!?' and len(current_sentence) > 1:
                # Look ahead to see if next char is space or end
                next_idx = len(''.join(current_sentence))
                if next_idx >= len(text) or text[next_idx] in ' \t\n\r':
                    sentences.append(''.join(current_sentence).strip())
                    current_sentence = []
            # Handle semicolons and em dashes when followed by space
            elif char in ':;—' and len(current_sentence) > 1:
                next_idx = len(''.join(current_sentence))
                if next_idx < len(text) and text[next_idx] in ' \t\n\r':
                    sentences.append(''.join(current_sentence).strip())
                    current_sentence = []
        
        # Add any remaining text
        if current_sentence:
            sentences.append(''.join(current_sentence).strip())
        
        # Remove empty sentences
        sentences = [s for s in sentences if s]

        # Only split if we have multiple sentences
        if len(sentences) > 1:
            # Clear original paragraph and keep first sentence
            p.string = sentences[0]
            
            # Add remaining sentences as new paragraphs
            current = p
            for sentence in sentences[1:]:
                if sentence.strip():
                    new_p = soup.new_tag("p")
                    new_p.string = sentence.strip()
                    current.insert_after(new_p)
                    current = new_p

    return soup

def process_html_file(file_path: str):
    """Process individual HTML file"""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = strip_internal_tags(f.read())

    processed_soup = split_paragraphs(soup)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(processed_soup))


def process_epub(epub_path: str, output_path: str):
    """Process entire EPUB file"""
    temp_dir = "temp_epub"
    try:
        extract_epub(epub_path, temp_dir)

        text_folder = find_content_folder(temp_dir)
        for html_file in get_content_files(text_folder):
            process_html_file(html_file)

        create_epub(temp_dir, output_path)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python epub_phrase_splitter.py input.epub output.epub")
        sys.exit(1)

    input_epub = sys.argv[1]
    output_epub = sys.argv[2]

    process_epub(input_epub, output_epub)
