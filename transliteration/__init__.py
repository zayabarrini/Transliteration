# transliteration/__init__.py

# 1. First import from other modules (non-circular dependencies)
from .filter_language_characters import filter_language_characters
from .translationFunctions import (
    LANGUAGE_CODE_MAP,
    LANGUAGE_STYLES,
    TARGET_PATTERNS,
    translate_parallel,
    translate_text,
)

# 2. Then import from transliteration.py (using relative import)
from .transliteration import (
    add_furigana,
    analyze_chinese_syntax,
    format_transliteration,
    get_grammatical_classes_from_pos,
    get_pinyin_annotations,
    get_pinyin_for_word,
    is_latin,
    is_punctuation,
    transliterate,
    transliterate_for_subtitles,
)

# 3. Explicit exports
__all__ = [
    "translate_text",
    "translate_parallel",
    "LANGUAGE_CODE_MAP",
    "LANGUAGE_STYLES",
    "TARGET_PATTERNS",
    "filter_language_characters",
    "transliterate",
    "add_furigana",
    "is_latin" "transliterate_for_subtitles",
]
