#!/usr/bin/env python3
import re
import sys

import chardet
import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub


class EPUBTTSFilter:
    def __init__(self):
        # Chinese characters regex: [^\u4E00-\u9FFF\s,]
        self.chinese_regex = re.compile(r'[^\u4E00-\u9FFF\s,]')
        
        # Russian characters regex: [^\u0400-\u04FF\s,]
        self.russian_regex = re.compile(r'[^\u0400-\u04FF\s,]')
        
        # Combined regex to detect language
        self.chinese_detector = re.compile(r'[\u4E00-\u9FFF]')
        self.russian_detector = re.compile(r'[\u0400-\u04FF]')
    
    def extract_text_from_epub(self, epub_path):
        """Extract clean text from EPUB file"""
        try:
            book = epub.read_epub(epub_path)
            text_content = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    clean_text = ' '.join(lines)
                    
                    if clean_text:
                        text_content.append(clean_text)
            
            return ' '.join(text_content)
        except Exception as e:
            print(f"Error reading EPUB: {e}")
            return ""
    
    def detect_language(self, text):
        """Detect if text is primarily Chinese or Russian"""
        chinese_chars = len(self.chinese_detector.findall(text))
        russian_chars = len(self.russian_detector.findall(text))
        total_non_space = len(re.findall(r'\S', text))
        
        if total_non_space == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_non_space
        russian_ratio = russian_chars / total_non_space
        
        if chinese_ratio > 0.3:
            return "chinese"
        elif russian_ratio > 0.3:
            return "russian"
        else:
            return "unknown"
    
    def filter_text(self, text, language):
        """Filter text based on language"""
        if language == "chinese":
            # Keep only Chinese characters, spaces, and commas
            filtered = self.chinese_regex.sub('', text)
        elif language == "russian":
            # Keep only Russian characters, spaces, and commas
            filtered = self.russian_regex.sub('', text)
        else:
            # If unknown, return original text
            return text
        
        # Clean up extra spaces
        filtered = re.sub(r'\s+', ' ', filtered).strip()
        return filtered
    
    def process_epub(self, epub_path, output_file=None):
        """Main function to process EPUB file"""
        print(f"Processing: {epub_path}")
        
        # Extract text from EPUB
        raw_text = self.extract_text_from_epub(epub_path)
        if not raw_text:
            print("No text extracted from EPUB")
            return
        
        print(f"Extracted {len(raw_text)} characters")
        
        # Detect language
        language = self.detect_language(raw_text)
        print(f"Detected language: {language}")
        
        # Filter text based on language
        filtered_text = self.filter_text(raw_text, language)
        
        print(f"Filtered to {len(filtered_text)} characters")
        
        # Save or display results
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(filtered_text)
            print(f"Filtered text saved to: {output_file}")
        else:
            # Print first 500 characters as preview
            preview = filtered_text[:500] + "..." if len(filtered_text) > 500 else filtered_text
            print(f"\nPreview:\n{preview}")
        
        return filtered_text, language

def main():
    if len(sys.argv) < 2:
        print("Usage: python epub_tts_filter.py <epub_file> [output_file]")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    processor = EPUBTTSFilter()
    processor.process_epub(epub_file, output_file)

if __name__ == "__main__":
    main()