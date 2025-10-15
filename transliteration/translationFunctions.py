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
    "de": "de",  # German
    "it": "it",  # Italian
    "fr": "fr",  # French
    "ru": "ru",  # Russian
    "zh-ch": "zh-CN",  # Chinese (Simplified)
    "zh-CN": "zh-CN",  # Chinese (Simplified)
    "jp": "ja",  # Japanese
    "ja": "ja",  # Japanese
    "hi": "hi",  # Hindi
    "ar": "ar",  # Arabic
    "ko": "ko",  # Korean
    "en": "en",  # English
    "es": "es",  # Spanish
    # Additional mappings for full language names
    "german": "de",
    "italian": "it",
    "french": "fr",
    "russian": "ru",
    "chinese": "zh-CN",
    "japanese": "ja",
    "hindi": "hi",
    "arabic": "ar",
    "korean": "ko",
    "english": "en",
    "spanish": "es",
}

# Add this near your other constants
LANGUAGE_STYLES = {
    "de": {"color": "#A0C4FF", "size": 16},  # German - light blue
    "it": {"color": "#BDB2FF", "size": 16},  # Italian - lavender
    "fr": {"color": "#FFC6FF", "size": 16},  # French - pink
    "ru": {"color": "#FDFFB6", "size": 16},  # Russian - pale yellow
    "zh-ch": {"color": "#CAFFBF", "size": 16},  # Chinese - mint green
    "jp": {"color": "#FFADAD", "size": 16},  # Japanese - light red
    "hi": {"color": "#FFD6A5", "size": 16},  # Hindi - peach
    "ar": {"color": "#9BF6FF", "size": 20},  # Arabic - light cyan (larger size)
    "ko": {"color": "#fae1dd", "size": 16},  # Korean - pale pink
    "en": {"color": "#fcd5ce", "size": 16},  # English - light peach
    "es": {"color": "#caffbf", "size": 16},  # Spanish - light green
}

# Precompile regex patterns
TARGET_PATTERNS = {
    # Full names
    "chinese": re.compile(r"[\u4e00-\u9fff]"),
    "russian": re.compile(r"[\u0400-\u04FF]"),
    "hindi": re.compile(r"[\u0900-\u097F]"),
    "japanese": re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF]"),
    "korean": re.compile(r"[\uAC00-\uD7AF]"),
    "arabic": re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"),
    # Short codes (point to the same patterns as full names)
    "zh-CN": re.compile(r"[\u4e00-\u9fff]"),  # Chinese
    "ru": re.compile(r"[\u0400-\u04FF]"),  # Russian
    "hi": re.compile(r"[\u0900-\u097F]"),  # Hindi
    "ja": re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF]"),  # Japanese
    "ko": re.compile(r"[\uAC00-\uD7AF]"),  # Korean
    "ar": re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"),  # Arabic
}

# Cache translator instances to avoid recreation
_translator_cache = {}


def get_translator(target_language):
    """Get or create cached translator instance"""
    lang_code = LANGUAGE_CODE_MAP.get(target_language, target_language)
    if lang_code not in _translator_cache:
        _translator_cache[lang_code] = GoogleTranslator(source="auto", target=lang_code)
    return _translator_cache[lang_code]


@lru_cache(maxsize=5000)  # Increased cache size
def translate_text(text, target_language):
    """Translate complete sentences with caching and optimized translator usage."""
    if not text.strip():
        return text

    # Quick check for very short or numeric text
    clean_text = " ".join(text.strip().split())
    if len(clean_text) < 3 or clean_text.isdigit():
        return clean_text

    try:
        translator = get_translator(target_language)
        translated = translator.translate(clean_text)
        return translated if translated and translated != clean_text else clean_text
    except Exception as e:
        print(f"Error translating text '{clean_text[:50]}...': {e}")
        return clean_text


# Batch translation function for better performance
def batch_translate_texts(texts, target_language):
    """Translate multiple texts in a batch for better performance"""
    if not texts:
        return []

    translator = get_translator(target_language)
    results = []

    for text in texts:
        if not text.strip():
            results.append(text)
            continue

        clean_text = " ".join(text.strip().split())
        if len(clean_text) < 3 or clean_text.isdigit():
            results.append(clean_text)
            continue

        try:
            translated = translator.translate(clean_text)
            results.append(translated if translated and translated != clean_text else clean_text)
        except Exception as e:
            print(f"Error in batch translation: {e}")
            results.append(clean_text)

    return results


def translate_parallel(tokens, target_language):
    """Translate individual words without caching."""
    print(f"Translating {len(tokens)} tokens to {target_language}...")

    # Filter out non-translatable tokens first
    translatable_tokens = []
    token_indices = []

    for i, token in enumerate(tokens):
        if token.strip() and token.isalpha() and len(token) > 1:
            translatable_tokens.append(token)
            token_indices.append(i)

    if not translatable_tokens:
        return tokens

    def translate_batch(batch_tokens):
        translator = get_translator(target_language)
        translated_batch = []
        for token in batch_tokens:
            try:
                translated = translator.translate(token)
                translated_batch.append(translated if translated else token)
            except Exception:
                translated_batch.append(token)
        return translated_batch

    # Process in smaller batches to avoid timeouts
    batch_size = 50
    translated_tokens = []

    for i in range(0, len(translatable_tokens), batch_size):
        batch = translatable_tokens[i : i + batch_size]
        translated_batch = translate_batch(batch)
        translated_tokens.extend(translated_batch)

    # Reconstruct the full list
    result = list(tokens)
    for idx, translated in zip(token_indices, translated_tokens):
        result[idx] = translated

    return result


def normalize_language(language):
    """Normalize language input to standard language code."""
    language = language.lower().strip()
    return LANGUAGE_CODE_MAP.get(language, language)


# Cache transliteration tools
_transliteration_tools = {}


def get_transliteration_tool(language):
    """Get cached transliteration tool"""
    if language not in _transliteration_tools:
        if language == "zh-CN":
            _transliteration_tools[language] = lambda text: " ".join(
                pypinyin.lazy_pinyin(text, style=pypinyin.Style.TONE)
            )
        elif language == "ja":
            kks = pykakasi.kakasi()

            # Modern pykakasi doesn't need setMode, it automatically handles all Japanese scripts
            def transliterate_japanese(text):
                result = kks.convert(text)
                return " ".join(item["hepburn"] for item in result)

            _transliteration_tools[language] = transliterate_japanese
        elif language == "ru":
            _transliteration_tools[language] = lambda text: translit(text, "ru", reversed=True)
        elif language == "hi":

            def transliterate_hindi(text):
                # First transliterate
                transliterated = indic_transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
                # Fix spacing issues - remove extra spaces between syllables
                # Join syllables properly and clean up spacing
                words = transliterated.split()
                cleaned_words = []
                for word in words:
                    # Remove excessive internal spacing while preserving word boundaries
                    cleaned_word = " ".join(word.split())  # Normalize internal spaces
                    cleaned_words.append(cleaned_word)
                return " ".join(cleaned_words)

            _transliteration_tools[language] = transliterate_hindi
        elif language == "ar":
            from modified.modified_pyarabic import custom_utf82latin as custom_arabic

            _transliteration_tools[language] = custom_arabic
        elif language == "ko":
            transliter = Transliter(rule=academic)
            _transliteration_tools[language] = transliter.translit
        else:
            _transliteration_tools[language] = lambda text: text

    return _transliteration_tools[language]


@lru_cache(maxsize=5000)
def transliterate(input_text, language):
    """Transliterate text based on the target language with caching."""
    if not input_text.strip():
        return input_text

    language = normalize_language(language)
    transliteration_tool = get_transliteration_tool(language)

    try:
        return transliteration_tool(input_text)
    except Exception as e:
        print(f"Error transliterating text: {e}")
        return input_text
