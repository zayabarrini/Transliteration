import re
import shutil
import sys
from bs4 import BeautifulSoup
from epubManagementNew import extract_epub, create_epub, find_content_folder, get_content_files
import os

# Enhanced multilingual sentence splitting regex
SPLIT_REGEX = re.compile(r'''
    (?<!\w\.\w.)          # Don't split after abbreviations like U.S.A.
    (?<![A-Z][a-z]\.)    # Don't split after abbreviations like Dr.
    (?<=[.!?…:;。！？])     # Split after sentence-ending punctuation (including CJK)
    (?:\s+|(?=[’”"'»›”])) # Followed by whitespace or closing quotes
    (?![.!?…:;。！？])      # But not if it's another sentence ender
''', re.VERBOSE)

def should_split(sentence: str) -> bool:
    """Check if a sentence should be split (length >=15 chars and contains spaces)"""
    return len(sentence) >= 15 and ' ' in sentence

def strip_internal_tags(html_content):
    """Remove all internal tags within paragraphs, preserving only text content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for p in soup.find_all('p'):
        # Get all text content, stripping tags
        clean_text = p.get_text(' ', strip=True)
        # Replace the paragraph with clean text
        p.string = clean_text
    
    return soup

def split_paragraphs(soup):
    """Split paragraphs at sentence boundaries"""
    paragraphs = soup.find_all('p')
    
    for p in paragraphs:
        text = p.get_text()
        # Skip if too short
        if len(text) < 15:
            continue
            
        # Split sentences using our enhanced regex
        sentences = SPLIT_REGEX.split(text)
        
        # Only split if we have multiple sentences that meet criteria
        if len(sentences) > 1 and any(should_split(s) for s in sentences):
            # Clear original paragraph and keep first sentence
            p.string = sentences[0].strip()
            
            # Add remaining sentences as new paragraphs after current one
            current = p
            for sentence in sentences[1:]:
                if should_split(sentence.strip()):
                    new_p = soup.new_tag('p')
                    new_p.string = sentence.strip()
                    current.insert_after(new_p)
                    current = new_p
    
    return soup

def process_html_file(file_path: str):
    """Process individual HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = strip_internal_tags(f.read())
    
    processed_soup = split_paragraphs(soup)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(processed_soup))

def process_epub(epub_path: str, output_path: str):
    """Process entire EPUB file"""
    temp_dir = 'temp_epub'
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