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

# Common abbreviations that shouldn't trigger splits (Western)
COMMON_ABBREVIATIONS = {
    'mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'hon', 'st', 'ave', 'blvd',
    'inc', 'corp', 'ltd', 'co', 'etc', 'e.g', 'i.e', 'vs', 'fig', 'p',
    'pp', 'vol', 'ed', 'trans', 'ca', 'al', 'cf', 'c.f', 'op', 'cit',
    'ibid', 'id', 'loc', 'e.g.', 'i.e.', 'viz', 'sc', 'no', 'esp'
}

# Pattern for Roman numerals (e.g., IV, IX, XII)
ROMAN_NUMERAL_PATTERN = re.compile(r'^[IVXLCDM]+$', re.IGNORECASE)

# Pattern for common reference patterns like [1], (1), [a], [注1], [3]
REFERENCE_PATTERN = re.compile(r'^[\[]?[\d\w注附][\]\)]?$|^[\(\[]\d+[\]\)]$')

def is_abbreviation(word: str) -> bool:
    """Check if a word is a common abbreviation or acronym"""
    word_lower = word.lower().rstrip('.')
    
    # Check common abbreviations
    if word_lower in COMMON_ABBREVIATIONS:
        return True
    
    # Check for single-letter abbreviations (e.g., "U.S.", "U.K.")
    if len(word_lower) == 1 and word_lower.isalpha():
        return True
    
    # Check for acronyms with multiple capital letters (e.g., "USA", "UNESCO")
    if word.isupper() and len(word) >= 2 and word.isalpha():
        return True
    
    # Check for Roman numerals
    if ROMAN_NUMERAL_PATTERN.match(word.upper()):
        return True
    
    return False

def is_number_with_period(token: str, text: str, pos: int) -> bool:
    """Check if a period is part of a number (e.g., 1.2, 3.14, 4.5.6)"""
    # Look for pattern like number. or .number
    if re.match(r'^\d+\.$', token):  # "123." 
        return True
    if re.search(r'\d\.\d', text[max(0, pos-3):min(len(text), pos+4)]):  # "1.2"
        return True
    return False

def is_reference_marker(token: str) -> bool:
    """Check if a token is a reference marker like [1], (3), [注1]"""
    return bool(REFERENCE_PATTERN.match(token.strip()))

def should_split_at_period(text: str, period_pos: int) -> bool:
    """Determine if a period should be treated as a sentence boundary"""
    # Look at the context before the period
    start = max(0, period_pos - 20)
    before_text = text[start:period_pos]
    
    # Split into words/tokens
    words = re.findall(r'[^\s]+', before_text)
    
    if not words:
        return True
    
    # Check last word/token before period
    last_token = words[-1]
    
    # Don't split if it's an abbreviation
    if is_abbreviation(last_token):
        return False
    
    # Don't split if it's a number with decimal
    if is_number_with_period(last_token, text, period_pos):
        return False
    
    # Don't split if it's a reference marker (like "[1]" before period)
    if is_reference_marker(last_token):
        return False
    
    # Check for ellipsis "..." - don't split
    if period_pos >= 2 and text[period_pos-2:period_pos+1] == '..':
        return False
    
    return True



def split_paragraphs(soup):
    """Split paragraphs at sentence boundaries with abbreviation/reference protection"""
    paragraphs = soup.find_all("p")

    for p in paragraphs:
        text = p.get_text()
        # Skip if too short
        if len(text) < 15:
            continue

        sentences = []
        current_sentence = []
        i = 0
        
        while i < len(text):
            current_sentence.append(text[i])
            
            # Check for Chinese sentence enders (always split)
            if text[i] in '。！？…':
                sentences.append(''.join(current_sentence).strip())
                current_sentence = []
            
            # Check for Western punctuation
            elif text[i] in '.!?':
                # For periods, check if it's a real sentence boundary
                if text[i] == '.':
                    if should_split_at_period(text, i):
                        # Check if next char is whitespace or end
                        if i + 1 >= len(text) or text[i+1] in ' \t\n\r':
                            sentences.append(''.join(current_sentence).strip())
                            current_sentence = []
                    # If not a real boundary, just continue
                else:  # ! or ?
                    if i + 1 >= len(text) or text[i+1] in ' \t\n\r':
                        sentences.append(''.join(current_sentence).strip())
                        current_sentence = []
            
            # Handle semicolons and em dashes when followed by space
            elif text[i] in ':;—' and i + 1 < len(text) and text[i+1] in ' \t\n\r':
                # But don't split if it's part of a reference like "[1]:"
                if not (len(current_sentence) > 2 and 
                        ''.join(current_sentence[-3:]).startswith('[')):
                    sentences.append(''.join(current_sentence).strip())
                    current_sentence = []
            
            i += 1
        
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
                if sentence.strip() and len(sentence.strip()) > 5:  # Avoid tiny fragments
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
