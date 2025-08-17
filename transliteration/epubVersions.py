from transliteration.epubTransliteration import SUPPORTED_LANGUAGES
from transliteration.epub_no_original import process_epub as remove_original
from transliteration.epubTransliteration import process_epub as transliterate_epub
import os
import ebooklib
from ebooklib import epub
import langdetect
from bs4 import BeautifulSoup

def get_language_from_epub(epub_path: str) -> str:
    """Try to get language from EPUB using multiple methods with priority."""
    # Method 0: Check filename for language hints
    filename = os.path.basename(epub_path).lower()
    if '-ja.' in filename or '_ja.' in filename:
        return 'japanese'

    try:
        book = epub.read_epub(epub_path)
        
        # Method 1: Check HTML lang attributes in content
        lang_counts = {}
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    # Check both lang attributes and xml:lang
                    for elem in soup.find_all(attrs={"lang": True}):
                        lang = elem['lang'].lower()
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    for elem in soup.find_all(attrs={"xml:lang": True}):
                        lang = elem['xml:lang'].lower()
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                except Exception as e:
                    continue
        
        if lang_counts:
            most_common = max(lang_counts.items(), key=lambda x: x[1])[0]
            if mapped := map_language_code(most_common):
                return mapped

        # Method 2: Check EPUB metadata
        if book.get_metadata('DC', 'language'):
            lang = book.get_metadata('DC', 'language')[0][0].lower()
            if mapped := map_language_code(lang):
                return mapped

        # Method 3: Character-based analysis
        japanese_chars = 0
        total_chars = 0
        samples_checked = 0
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT and samples_checked < 3:
                try:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    
                    # More efficient character checking
                    japanese_in_sample = sum(1 for char in text if is_japanese_char(char))
                    japanese_chars += japanese_in_sample
                    total_chars += len(text)
                    samples_checked += 1
                    
                    # Early exit if we find significant Japanese content
                    if total_chars > 100 and (japanese_chars / total_chars) > 0.1:
                        return 'japanese'
                except Exception as e:
                    continue
        
        # Final check after sampling
        if total_chars > 0 and (japanese_chars / total_chars) > 0.05:  # Lowered threshold to 5%
            return 'japanese'

    except Exception as e:
        print(f"Error processing EPUB: {e}")
    
    return None

def map_language_code(lang_code: str) -> str:
    """Map language codes to our supported language names."""
    lang_map = {
        'japanese': 'japanese',
        'korean': 'korean',
        'chinese': 'chinese',
        'hindi': 'hindi',
        'arabic': 'arabic',
        'russian': 'russian',
        'ja': 'japanese',
        'jp': 'japanese',
        'jpn': 'japanese',
        'ko': 'korean',
        'kor': 'korean',
        'zh': 'chinese',
        'chi': 'chinese',
        'hi': 'hindi',
        'hin': 'hindi',
        'ar': 'arabic',
        'ara': 'arabic',
        'ru': 'russian',
        'rus': 'russian'
    }
    return lang_map.get(lang_code.lower(), None)

def is_japanese_char(char: str) -> bool:
    """Check if character is Japanese (hiragana, katakana, or kanji)"""
    return any([
        0x3040 <= ord(char) <= 0x309F,  # Hiragana
        0x30A0 <= ord(char) <= 0x30FF,  # Katakana
        0x4E00 <= ord(char) <= 0x9FFF,  # CJK Unified Ideographs
    ])
def process_folder(folder_path: str):
    for filename in os.listdir(folder_path):
        if filename.endswith('.epub'):
            epub_path = os.path.join(folder_path, filename)
            language = get_language_from_epub(epub_path)
            
            # Option 1: Remove original text
            # epub_path_no_original = remove_original(epub_path)
            # print(f"Processing {epub_path} for language: {language}")

            if language in SUPPORTED_LANGUAGES:
                # Option 2: Transliterate
                transliterate_epub(epub_path, language)
                # Option : Transliterate no_original
                # transliterate_epub(epub_path_no_original)


if __name__ == "__main__":
    process_folder("/home/zaya/Documents/Ebooks/Lacan/1-27/db/trans")
    # process_folder("/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks")

