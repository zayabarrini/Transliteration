# translationFunctions.py
import re
from functools import lru_cache
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor
import pypinyin
import pykakasi
from transliterate import translit
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as indic_transliterate
from hangul_romanize import Transliter
from hangul_romanize.rule import academic

# Map target_language to Google Translate language codes
LANGUAGE_CODE_MAP = {
    'de': 'de',        # German
    'it': 'it',        # Italian
    'fr': 'fr',        # French
    'ru': 'ru',        # Russian
    'zh-ch': 'zh-CN',  # Chinese (Simplified)
    'jp': 'ja',        # Japanese
    'hi': 'hi',        # Hindi
    'ar': 'ar',        # Arabic
    'ko': 'ko',        # Korean
    'en': 'en',        # English
    'es': 'es',        # Spanish
    
    # Additional mappings for full language names
    'german': 'de',
    'italian': 'it',
    'french': 'fr',
    'russian': 'ru',
    'chinese': 'zh-CN',
    'japanese': 'ja',
    'hindi': 'hi',
    'arabic': 'ar',
    'korean': 'ko',
    'english': 'en',
    'spanish': 'es'
}

# Add this near your other constants
LANGUAGE_STYLES = {
    'de': {'color': '#A0C4FF', 'size': 16},    # German - light blue
    'it': {'color': '#BDB2FF', 'size': 16},    # Italian - lavender
    'fr': {'color': '#FFC6FF', 'size': 16},    # French - pink
    'ru': {'color': '#FDFFB6', 'size': 16},    # Russian - pale yellow
    'zh-ch': {'color': '#CAFFBF', 'size': 16}, # Chinese - mint green
    'jp': {'color': '#FFADAD', 'size': 16},    # Japanese - light red
    'hi': {'color': '#FFD6A5', 'size': 16},    # Hindi - peach
    'ar': {'color': '#9BF6FF', 'size': 20},    # Arabic - light cyan (larger size)
    'ko': {'color': '#fae1dd', 'size': 16},    # Korean - pale pink
    'en': {'color': '#fcd5ce', 'size': 16},    # English - light peach
    'es': {'color': '#caffbf', 'size': 16}     # Spanish - light green
}

# Precompile regex patterns
TARGET_PATTERNS = {
    'chinese': re.compile(r'[\u4e00-\u9fff]'),
    'russian': re.compile(r'[\u0400-\u04FF]'),
    'hindi': re.compile(r'[\u0900-\u097F]'),
    'japanese': re.compile(r'[\u3040-\u30FF\u4E00-\u9FFF]'),
    'korean': re.compile(r'[\uAC00-\uD7AF]'),
    'arabic': re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]'),
}

@lru_cache(maxsize=1000)
def translate_text(text, target_language):
    """Translate text to target language using Google Translate with caching."""
    if not text.strip():
        return text
    
    try:
        translated = GoogleTranslator(source='auto', target=LANGUAGE_CODE_MAP[target_language]).translate(text)
        # print(f"Translated '{text}' to '{translated}' in {target_language}")
        return translated if translated else text
    except Exception as e:
        print(f"Error translating text: {e}")
        return text

def translate_parallel(lines, target_language):
    """Translate lines in parallel using ThreadPoolExecutor."""
    print(f"Translating lines to {target_language}...")
    with ThreadPoolExecutor() as executor:
        translated_lines = list(executor.map(
            lambda line: translate_text(line.strip(), target_language) if line.strip() and not re.match(r'^\d+$', line.strip()) and not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()) else line,
            lines
        ))
    return translated_lines

def normalize_language(language):
    """Normalize language input to standard language code."""
    language = language.lower().strip()
    return LANGUAGE_CODE_MAP.get(language, language)

def transliterate(input_text, language):
    """Transliterate text based on the target language."""
    if not input_text.strip():
        return input_text
    
    language = normalize_language(language)

    if language == "zh-CN":
        return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.NORMAL))
    elif language == "ja":
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")  # Hiragana to Romaji
        kakasi.setMode("K", "a")  # Katakana to Romaji
        kakasi.setMode("J", "a")  # Kanji to Romaji
        converter = kakasi.getConverter()
        return converter.do(input_text)
    elif language == "ru":
        return translit(input_text, 'ru', reversed=True)
    elif language == "hi":
        return indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
    elif language == "ko":
        transliter = Transliter(rule=academic)
        return transliter.translit(input_text)
    else:
        return input_text  # For languages without a need for transliteration