# transliteration/__init__.py

# 1. First import from other modules (non-circular dependencies)
from .translationFunctions import (
    translate_text,
    translate_parallel,
    LANGUAGE_CODE_MAP,
    LANGUAGE_STYLES,
    TARGET_PATTERNS,
)
from .filter_language_characters import filter_language_characters

# 2. Then import from transliteration.py (using relative import)
from .transliteration import (
    transliterate,
    add_furigana,
    is_latin,
    transliterate_for_subtitles,
    format_transliteration,
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
