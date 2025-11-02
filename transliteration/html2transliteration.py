import os
import shutil

from bs4 import BeautifulSoup, NavigableString  # For HTML parsing

from transliteration.add_css import (  # Import from our new module
    add_css_link,
    get_css_file,
)
from transliteration.transliteration import (
    add_furigana,
    get_pinyin_annotations,
    is_latin,
    transliterate,
)


def contains_chinese(text):
    """Check if text contains Chinese characters"""
    import re

    chinese_pattern = re.compile(r"[\u4e00-\u9fff]")
    return bool(chinese_pattern.search(text))


def process_html_content(soup, language):
    """Recursively process all text nodes in the HTML and add transliteration."""
    from bs4 import BeautifulSoup, NavigableString

    for element in soup.find_all(string=True):
        if element.parent and element.parent.name in ["script", "style", "ruby", "rt"]:
            continue

        text = element.strip()
        if not text:
            continue

        # For Chinese language processing, only apply dual display to text with Chinese characters
        if language.lower() == "chinese":
            if contains_chinese(text):
                # This is Chinese text - apply dual display
                dual_display = get_pinyin_annotations(text, color_coded=True)
                element.replace_with(dual_display)
            else:
                # This is non-Chinese text - leave it as is or apply simple processing
                # You can choose to leave it untouched or add minimal processing
                continue  # Skip processing for non-Chinese text
        else:
            # Handle other languages
            transliterated_text = transliterate(text, language)
            furigana_content = add_furigana(text, transliterated_text, language)
            if furigana_content != text:
                element.replace_with(furigana_content)

import re
from collections import Counter

LANGUAGE_CHAR_RANGES = {
    "korean": [(0xAC00, 0xD7AF)],  # Hangul syllables
    "arabic": [(0x0600, 0x06FF)],   # Basic Arabic
    "russian": [(0x0400, 0x04FF)],  # Cyrillic
    "hindi": [(0x0900, 0x097F)],    # Devanagari (Hindi)
    "japanese": [
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana  
        (0x4E00, 0x9FFF),  # Kanji/Chinese characters
    ],
    "chinese": [(0x4E00, 0x9FFF)],  # Chinese characters
    "latin": [(0x0041, 0x007A), (0x00C0, 0x02AF)],  # Basic Latin + extended
}

# Language priority for ambiguous characters (Chinese/Japanese share Kanji)
LANGUAGE_PRIORITY = ["chinese", "japanese", "korean", "hindi", "arabic", "russian", "latin"]

def detect_language_char(char):
    """Detect which language a character belongs to"""
    char_code = ord(char)
    
    # Skip common punctuation and whitespace
    if char in ' .,!?。，！？、」「『』（）《》-—–…':
        return "punctuation"
    
    for lang, ranges in LANGUAGE_CHAR_RANGES.items():
        for start, end in ranges:
            if start <= char_code <= end:
                return lang
    
    return "unknown"

def detect_language_text(text):
    """Detect the primary language of a text block"""
    if not text.strip():
        return "unknown"
    
    char_languages = []
    for char in text:
        lang = detect_language_char(char)
        if lang not in ["punctuation", "unknown"]:
            char_languages.append(lang)
    
    if not char_languages:
        return "unknown"
    
    # Count language occurrences
    lang_counts = Counter(char_languages)
    
    # Handle Chinese/Japanese ambiguity with better heuristics
    if "japanese" in lang_counts and "chinese" in lang_counts:
        # If there are Japanese-specific characters, prioritize Japanese
        if contains_japanese_specific_chars(text):
            return "japanese"
        # If there are Chinese-specific patterns, prioritize Chinese
        elif contains_chinese_specific_patterns(text):
            return "chinese"
        # Default to the majority
        elif lang_counts["japanese"] > lang_counts["chinese"]:
            return "japanese"
        else:
            return "chinese"
    
    # For single language or clear majority
    primary_lang = lang_counts.most_common(1)[0][0]
    
    # Double-check Chinese/Japanese if detected
    if primary_lang == "japanese" and not contains_japanese_specific_chars(text) and contains_chinese_specific_patterns(text):
        return "chinese"
    elif primary_lang == "chinese" and contains_japanese_specific_chars(text):
        return "japanese"
    
    return primary_lang

def contains_japanese_specific_chars(text):
    """Check for Japanese-specific characters"""
    # Hiragana and Katakana are uniquely Japanese
    hiragana_range = (0x3040, 0x309F)
    katakana_range = (0x30A0, 0x30FF)
    # Japanese punctuation and symbols
    japanese_punct = "・「」『』〜"
    
    for char in text:
        code = ord(char)
        if (hiragana_range[0] <= code <= hiragana_range[1] or 
            katakana_range[0] <= code <= katakana_range[1] or
            char in japanese_punct):
            return True
    return False

def contains_chinese_specific_patterns(text):
    """Check for Chinese-specific patterns"""
    # Chinese punctuation
    chinese_punct = "。，！？《》【】"
    # Common Chinese characters not typically used in Japanese
    chinese_specific_chars = "这那为个说国们着么"
    
    if any(punct in text for punct in chinese_punct):
        return True
    
    if any(char in text for char in chinese_specific_chars):
        return True
    
    return False

def segment_text_by_language(text):
    """Segment text into language-specific blocks"""
    if not text.strip():
        return []
    
    # First, detect the primary language of the entire text block
    primary_lang = detect_language_text(text)
    
    # If it's clearly one language, treat it as a single segment
    if primary_lang not in ["unknown", "punctuation"]:
        return [(text, primary_lang)]
    
    # Fallback: character-level segmentation for truly mixed content
    segments = []
    current_segment = ""
    current_lang = None
    
    for char in text:
        char_lang = detect_language_char(char)
        
        # Treat punctuation as continuing the current segment
        if char_lang == "punctuation":
            current_segment += char
            continue
        
        if current_lang is None:
            current_lang = char_lang
            current_segment = char
        elif current_lang == char_lang:
            current_segment += char
        else:
            # Language changed, save current segment
            if current_segment.strip():
                segments.append((current_segment, current_lang))
            current_segment = char
            current_lang = char_lang
    
    # Add the final segment
    if current_segment.strip():
        segments.append((current_segment, current_lang))
    
    return segments

def process_html_content_multilingual(soup, default_language=None):
    """Process HTML content with automatic language detection and transliteration"""
    from bs4 import BeautifulSoup, NavigableString, Tag
    
    for element in soup.find_all(string=True):
        if element.parent and element.parent.name in ["script", "style", "ruby", "rt"]:
            continue
        
        text = element.strip()
        if not text:
            continue
        
        # Skip if text is too short or doesn't need processing
        if len(text) < 2 or text.isascii():
            continue
        
        # Segment text by language
        segments = segment_text_by_language(text)
        
        if len(segments) == 1:
            # Single language text
            segment_text, detected_lang = segments[0]
            if detected_lang not in ["unknown", "punctuation", "latin"]:
                processed_content = process_segment(segment_text, detected_lang)
                if processed_content != segment_text:
                    # Ensure we're replacing with proper HTML
                    if isinstance(processed_content, str):
                        # Parse the HTML string and replace
                        try:
                            processed_soup = BeautifulSoup(processed_content, 'html.parser')
                            if processed_soup.find():
                                # If it contains HTML tags, replace with the parsed content
                                element.replace_with(processed_soup)
                            else:
                                # Plain text replacement
                                element.replace_with(processed_content)
                        except:
                            # Fallback: plain text replacement
                            element.replace_with(processed_content)
                    else:
                        # Already a BeautifulSoup object
                        element.replace_with(processed_content)
        
        elif len(segments) > 1:
            # Mixed language text - process each segment
            processed_segments = []
            for segment_text, detected_lang in segments:
                if detected_lang in ["unknown", "punctuation"]:
                    processed_segments.append(segment_text)
                elif detected_lang == "latin":
                    # Keep Latin text as-is
                    processed_segments.append(segment_text)
                else:
                    processed_segment = process_segment(segment_text, detected_lang)
                    processed_segments.append(processed_segment)
            
            # Combine processed segments - handle both strings and BeautifulSoup objects
            combined_content = soup.new_tag("span")
            for segment in processed_segments:
                if isinstance(segment, (Tag, NavigableString)):
                    # Already a BeautifulSoup object
                    combined_content.append(segment)
                elif isinstance(segment, str):
                    # Plain text or HTML string
                    try:
                        # Try to parse as HTML
                        segment_soup = BeautifulSoup(segment, 'html.parser')
                        if segment_soup.find():
                            # Contains HTML tags, append all children
                            for child in segment_soup.contents:
                                combined_content.append(child)
                        else:
                            # Plain text
                            combined_content.append(segment)
                    except:
                        # Fallback: append as plain text
                        combined_content.append(segment)
                else:
                    # Unknown type, convert to string
                    combined_content.append(str(segment))
            
            # Replace the original element with our combined content
            element.replace_with(combined_content)

def process_segment(text, language):
    """Process a text segment with the specified language"""
    try:
        if language == "chinese":
            print("Processing Chinese text segment:", text)
            chinese_result = get_pinyin_annotations(text, color_coded=True)
            from bs4 import BeautifulSoup
            return BeautifulSoup(chinese_result, 'html.parser')      
        elif language == "japanese":
            transliterated = transliterate(text, "japanese")
            return add_furigana(text, transliterated, "japanese")
        
        elif language == "korean":
            transliterated = transliterate(text, "korean")
            return add_furigana(text, transliterated, "korean")
        
        elif language == "hindi":
            transliterated = transliterate(text, "hindi")
            return add_furigana(text, transliterated, "hindi")
        
        elif language == "arabic":
            transliterated = transliterate(text, "arabic")
            return add_furigana(text, transliterated, "arabic")
        
        elif language == "russian":
            transliterated = transliterate(text, "russian")
            return add_furigana(text, transliterated, "russian")
        
        else:
            return text  # Return original for unsupported languages
    
    except Exception as e:
        print(f"Error processing {language} text '{text}': {e}")
        return text  # Fallback to original text
    
# def process_html_content(soup, language, keep_translations=True):
#     for element in soup.descendants:
#         if not (isinstance(element, NavigableString) and element.strip()):
#             continue

#         parent = getattr(element, 'parent', None)
#         if not parent or not hasattr(parent, 'name') or parent.name in ['script', 'style', 'ruby', 'rt']:
#             continue

#         # Get previous element sibling
#         prev = getattr(parent, 'previous_sibling', None)
#         while prev and not (hasattr(prev, 'name') and isinstance(prev.name, str)):
#             prev = getattr(prev, 'previous_sibling', None)

#         # Check conditions
#         should_transliterate = False
#         try:
#             if keep_translations:
#                 if 'dir' in parent.attrs or (prev and prev.get('lang') != parent.get('lang')):
#                     should_transliterate = True
#             else:
#                 if prev and ('dir' in prev.attrs or prev.get('lang') != parent.get('lang')):
#                     if getattr(prev, 'name', None) not in ['head', 'meta', 'title', 'link']:
#                         should_transliterate = True
#         except AttributeError:
#             continue

#         if not should_transliterate or is_latin(element):
#             continue

#         try:
#             transliterated_text = transliterate(element, language)
#             element.replace_with(add_furigana(element, transliterated_text, language))
#         except Exception as e:
#             print(f"Error processing element: {e}")
#             continue


def process_file(input_file, language, enable_transliteration, epub_folder=None):
    """
    Processes an HTML or XHTML file for transliteration and CSS styling.

    Args:
        input_file (str): Path to the input HTML/XHTML file.
        language (str): Target language for transliteration.
        enable_transliteration (bool): Whether to enable transliteration.
        css_file (str, optional): Path to the CSS file to be added. Defaults to None.
    """
    print(f"Processing {input_file} for {language} with transliteration: {enable_transliteration}")

    # Read the input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse content
    # Parse content - use XML parser for XHTML and XML, HTML parser for others
    if input_file.endswith((".xhtml", ".xml")):
        parser = "lxml-xml"
    else:
        parser = "html.parser"
    soup = BeautifulSoup(content, parser)

    # Apply transliteration if enabled
    if enable_transliteration:
        # process_html_content_multilingual(soup, language)
        process_html_content(soup, language)

    # Add CSS if epub_folder is provided
    if epub_folder:
        css_rel_path = get_css_file(language, epub_folder)
        add_css_link(soup, css_rel_path)

    # Determine output filename (retain the original extension)
    base_name, ext = os.path.splitext(input_file)
    output_filename = f"{base_name}{ext}"

    # Save the modified content
    with open(output_filename, "w", encoding="utf-8") as f:
        if input_file.endswith((".xhtml", ".xml")):
            f.write(soup.prettify(formatter=None))  # Preserve XML formatting for XHTML
        else:
            f.write(soup.prettify(formatter=None))  # Standard HTML formatting

    print(f"Saved transliterated file: {output_filename}")


def process_folder(html_folder, target_language, enable_transliteration=True, epub_folder=None):
    """
    Processes all HTML files in the specified folder.
    """

    for filename in os.listdir(html_folder):
        if filename.lower().endswith((".html", ".htm", ".xhtml", ".xml")):
            input_filename = os.path.join(html_folder, filename)
            process_file(input_filename, target_language, enable_transliteration, epub_folder)


if __name__ == "__main__":
    # Define the folder containing HTML files
    html_folder = "/home/zaya/Downloads/Harry Potter シリーズ全7巻 (J.K. Rowling) (Z-Library)-trans/OEBPS/Text"  # Update this path to your folder containing HTML files
    target_language = "japanese"  # Target language (e.g., 'chinese', 'japanese', etc.)
    process_folder(html_folder, target_language)
