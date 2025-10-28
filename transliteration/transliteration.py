import os
import re
import sys
from pathlib import Path

language_map = {
    "ja": "japanese",
    "jp": "japanese",
    "ko": "korean",
    "kr": "korean",
    "zh-cn": "chinese",
    "zh-CN": "chinese",
    "hi": "hindi",
    "in": "hindi",
    "ar": "arabic",
    "ru": "russian",
}

# Android-specific path setup
if "com.termux" in os.environ.get("PREFIX", ""):
    # Termux environment
    sys.path.insert(0, "/data/data/com.termux/files/home/transliteration")
    BASE_DIR = Path("/data/data/com.termux/files/home/transliteration")
else:
    BASE_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(BASE_DIR))
# Import modified versions
try:
    from modified.modified_hangul import Transliter as CustomTransliter
    from modified.modified_kakasi import Kakasi as CustomKakasi
    from modified.modified_pyarabic import custom_utf82latin as custom_arabic
except ImportError:
    # Fallback to original versions if modified not found
    CustomKakasi = None
    CustomTransliter = None
    custom_arabic = None

# Import original libraries
import pykakasi as original_pykakasi
import pypinyin
from hangul_romanize import Transliter as OriginalTransliter

# from pyarabic import trans as original_pyarabic
from hangul_romanize.rule import academic

# Apply monkey patches if custom versions exist
if CustomKakasi:
    original_pykakasi.kakasi = lambda: CustomKakasi()

if CustomTransliter:

    def patched_transliter_init(self, rule=None):
        CustomTransliter.__init__(self, rule or academic)

    OriginalTransliter.__init__ = patched_transliter_init

# if custom_arabic and not hasattr(original_pyarabic, 'custom_utf82latin'):
#     original_pyarabic.custom_utf82latin = custom_arabic

# Android-friendly imports with fallbacks
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as indic_transliterate
except ImportError:

    def indic_transliterate(text, *args, **kwargs):
        return text  # Fallback


try:
    import jieba
except ImportError:

    def jieba_cut(text):
        return [text]  # Simple fallback

    jieba = type("", (), {"cut": jieba_cut})()


def format_transliteration(text):
    # Add spaces after commas and periods
    text = re.sub(r"([,.])", r"\1 ", text)

    # Add spaces around hyphens
    text = re.sub(r"([a-zA-Z])-([a-zA-Z])", r"\1 - \2", text)

    # Break long sentences into smaller chunks
    sentences = re.split(r"(?<=[。！？])", text)
    formatted_text = "\n".join([s.strip() for s in sentences if s.strip()])

    return formatted_text


def is_latin(token):
    """Check if a token contains only Latin characters, numbers, or basic punctuation."""
    return bool(re.fullmatch(r'^[\w\s.,;:!?\'"()\-–—\[\]{}@#$%^&*+=/\\|~<>]+$', token, re.UNICODE))


# def tokenize_text(text):
#     """Tokenize the text into words and symbols."""
#     # Use a regex to split the text into words and symbols
#     tokens = re.findall(r'\w+|\W+', text)
#     return tokens
def tokenize_text(text):
    # Tokenize the text into words and non-words (punctuation, spaces, etc.)
    tokens = re.findall(r"\w+|\W+", text)

    # Initialize a list to store the corrected tokens
    corrected_tokens = []

    for token in tokens:
        if re.match(r"\W+", token):  # Check if the token is punctuation
            if corrected_tokens:  # If there is a previous word, append punctuation to it
                corrected_tokens[-1] += token
            else:  # If no previous word exists, add the punctuation as a standalone token
                corrected_tokens.append(token)
        else:  # If the token is a word, add it to the list
            corrected_tokens.append(token)

    return corrected_tokens


def append_punctuation_to_previous_word(segmented_words):
    # List of punctuation marks to handle
    punctuation_marks = [
        "。",
        "，",
        "！",
        "？",
        "、",
        "「",
        "」",
        "『",
        "』",
        "（",
        "）",
        "《",
        "》",
        ".",
        ",",
        "!",
        "?",
    ]

    # Initialize a new list to store the corrected tokens
    corrected_words = []

    for word in segmented_words:
        if word in punctuation_marks:  # Check if the word is punctuation
            if corrected_words:  # If there is a previous word, append punctuation to it
                corrected_words[-1] += word
            else:  # If no previous word exists, add the punctuation as a standalone token
                corrected_words.append(word)
        else:  # If the word is not punctuation, add it to the list
            corrected_words.append(word)

    return corrected_words


import re

import jieba
import jieba.posseg as pseg
from pypinyin import Style, lazy_pinyin, pinyin

EXCLUDE_CHARS = {
    " ",
    ".",
    ",",
    "!",
    "?",
    "。",
    "，",
    "！",
    "？",
    "、",
    "「",
    "」",
    "『",
    "』",
    "（",
    "）",
    "《",
    "》",
    "“",
    "”",
    "‘",
    "’",
    "…",
    "—",
    "：",
    ":",
    "；",
    ";",
    "～",
    "°",
    "º",
}


def is_punctuation(word):
    """Check if a word is punctuation"""
    return word in EXCLUDE_CHARS


def analyze_chinese_syntax(text):
    """Improved POS-based syntax analysis for Chinese"""
    words = list(pseg.cut(text))
    syntax_data = []

    for i, (word, pos) in enumerate(words):
        # Skip punctuation in syntax analysis
        if is_punctuation(word):
            syntax_data.append((word, "PUNCT", pos))
            continue

        # Enhanced heuristic rules based on POS tags
        if pos.startswith("v"):  # Verbs (v, vd, vn, etc.)
            category = "V"
        elif pos in ["r", "nh", "nr"] and i == 0:  # First person/name often subject
            category = "S"
        elif pos in ["r", "nh", "nr"] and i > 0 and syntax_data:
            # Check previous word to determine if this is subject or object
            prev_syntax = syntax_data[-1][1] if syntax_data else ""
            if prev_syntax in ["V", "P"]:  # After verb or preposition, likely object
                category = "O"
            else:
                category = "S"
        elif pos.startswith("n") and i > 0:  # Nouns after first position
            prev_syntax = syntax_data[-1][1] if syntax_data else ""
            if prev_syntax == "V":  # Object after verb
                category = "O"
            elif prev_syntax in ["P", "C"]:  # After preposition/conjunction
                category = "O"
            else:
                category = "S" if i == 0 else "O"
        elif pos.startswith("n") and i == 0:  # First noun is likely subject
            category = "S"
        elif pos in ["d", "a", "b"]:  # Adverbs, adjectives, other modifiers
            category = "A"
        elif pos in ["c", "p", "cc"]:  # Conjunctions, prepositions
            category = "C" if pos in ["c", "cc"] else "P"
        elif pos in ["u", "y", "e"]:  # Auxiliary, modal particles
            category = "P"
        elif pos in ["m", "q"]:  # Numbers, quantifiers
            category = "A"  # Treat as adjunct/modifier
        elif pos in ["f", "s"]:  # Direction, place
            category = "A"
        else:
            category = "X"  # Other

        syntax_data.append((word, category, pos))

    return syntax_data


def get_pinyin_for_word(word):
    """Get pinyin for a word, handling multi-character words properly"""
    if is_punctuation(word):
        return ""

    # For multi-character words, join the pinyin with spaces
    pinyin_list = lazy_pinyin(word, style=Style.TONE, neutral_tone_with_five=True, strict=False)
    return " ".join(pinyin_list)


def get_pinyin_annotations(text, color_coded=False):
    """Get pinyin annotations with word-level grouping and optional color-coding"""
    from pypinyin import Style, lazy_pinyin, load_phrases_dict

    # Custom phrase corrections
    load_phrases_dict(
        {"什么": [["shén"], ["me"]], "怎么": [["zěn"], ["me"]], "明白": [["míng"], ["bai"]]}
    )

    # Perform syntax analysis to get word groupings
    syntax_analysis = analyze_chinese_syntax(text)

    # Build both versions
    result = []
    clean_version = []  # Initialize for both modes

    for word, syntax, pos in syntax_analysis:
        if is_punctuation(word):
            # Add punctuation directly to both versions
            result.append(word)
            clean_version.append(word)
        else:
            # Get pinyin for the entire word
            word_pinyin = get_pinyin_for_word(word)

            # Always add to clean version
            clean_version.append(word)

            if color_coded:
                # Color-coded mode
                if word_pinyin and word_pinyin != word:
                    result.append(
                        f'<ruby class="{syntax}"><rt>{syntax}</rt><span class="word-token">{word}</span><rt class="pinyin">{word_pinyin}</rt></ruby>'
                    )
                else:
                    result.append(f'<span class="{syntax}">{word}</span>')
            else:
                # Simple mode: just word with pinyin
                if word_pinyin and word_pinyin != word:
                    result.append(f"<ruby>{word}<rt>{word_pinyin}</rt></ruby>")
                else:
                    result.append(word)

    # Create the dual display structure
    clean_div = f'<div class="clean-version">{"".join(clean_version)}</div>'
    trans_div = f'<div class="transliterated-version">{"".join(result)}</div>'

    return f'<div class="chinese-dual-display">{clean_div}{trans_div}</div>'


def process_chinese_advanced(text):
    """Advanced processing with full syntax analysis (for detailed breakdown)"""
    # Use POS-based syntax analysis
    syntax_analysis = analyze_chinese_syntax(text)

    result = []
    for word, syntax, pos in syntax_analysis:
        if is_punctuation(word):
            result.append(
                {
                    "word": word,
                    "transliteration": "",
                    "syntax": syntax,
                    "pos": pos,
                    "is_punctuation": True,
                }
            )
        else:
            pinyin_word = get_pinyin_for_word(word)
            result.append(
                {
                    "word": word,
                    "transliteration": pinyin_word,
                    "syntax": syntax,
                    "pos": pos,
                    "is_punctuation": False,
                }
            )

    return result


def process_japanese_segment(text, soup):
    """Process a segment of Japanese text into ruby annotations"""
    import pykakasi

    kks = pykakasi.kakasi()
    analyzed = kks.convert(text)

    container = soup.new_tag("span")

    for item in analyzed:
        original = item.get("orig", "")
        romaji = item["hepburn"]  # Use Latin transliteration

        if not original.strip():
            container.append(original)
        else:
            ruby_tag = soup.new_tag("ruby")
            ruby_tag.append(original)
            rt_tag = soup.new_tag("rt")
            rt_tag.string = romaji
            ruby_tag.append(rt_tag)
            container.append(ruby_tag)

    return container


# Function to add furigana to text
def add_furigana(text, transliteration, language):
    language = language.lower()
    language = language_map.get(language, language)
    if not text:
        return ""
    # tokens = text
    exclude_chars = [
        " ",
        ".",
        ",",
        "!",
        "?",
        "。",
        "，",
        "-",
        "！",
        "？",
        "、",
        "「",
        "」",
        "『",
        "』",
        "（",
        "）",
        "《",
        "》",
    ]
    # if language == "japanese":
    #     trans_words = [item['hepburn'] for item in transliteration]
    # el
    if language == "korean":
        trans_words = transliteration  # Use the list of tuples directly
    # else:
    #    trans_words = transliteration.split()

    # if language == "japanese" and is_english(text):
    #     return text

    furigana_text = []
    trans_index = 0
    if language == "japanese":
        # Japanese character ranges: Hiragana, Katakana, Kanji, and whitespace
        japanese_pattern = re.compile(r"([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\s]+)")

        # Split text into Japanese and non-Japanese segments
        segments = japanese_pattern.split(text)

        # If no Japanese text found, return original
        if len(segments) == 1:
            return text
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("", "html.parser")
        result = []

        for segment in segments:
            if not segment:
                continue

            # Check if this segment is Japanese
            if japanese_pattern.fullmatch(segment):
                # Process Japanese text
                ruby_segment = process_japanese_segment(segment, soup)
                result.append(ruby_segment)
            else:
                # Keep non-Japanese as-is
                result.append(segment)

        # Combine all segments
        if len(result) == 1:
            return result[0]
        else:
            combined = soup.new_tag("span")
            for item in result:
                if isinstance(item, str):
                    combined.append(item)
                else:
                    combined.append(item)
            return combined
    elif language == "korean":
        # trans_words should already be a list of (char, trans) tuples
        # Ensure we have valid data
        if not isinstance(trans_words, list):
            trans_words = [(c, c) for c in text]

        for char, trans in trans_words:
            if char in exclude_chars:
                furigana_text.append(char)
            else:
                # Clean up the transliteration if needed
                clean_trans = trans.strip()
                if not clean_trans:
                    clean_trans = char
                furigana_text.append(f"<ruby>{char}<rt>{clean_trans}</rt></ruby>")
    elif language == "chinese":
        # pinyin = get_pinyin_annotations(text)
        # return pinyin
        return transliteration
    elif language in ["hindi", "arabic", "russian"]:
        segmented_words = text.split()
        language_excludes = {
            "hindi": ["।", "॥", "़", "्"],  # Hindi-specific characters
            "arabic": ["ـ", "َ", "ُ", "ِ", "ّ", "ْ"],  # Arabic diacritics
            "russian": ["«", "»", "—", "…"],  # Russian-specific punctuation
        }
        exclude_chars = exclude_chars + language_excludes.get(language, [])
        for word in segmented_words:
            # Skip pure punctuation words
            if all(char in exclude_chars for char in word):
                furigana_text.append(word)
                continue

            if trans_index < len(trans_words):
                # Get the transliteration for this word
                translit = trans_words[trans_index]
                trans_index += 1

                # Remove excluded characters from the transliteration
                clean_translit = "".join([c for c in translit if c not in exclude_chars])

                # Only apply ruby if we have non-excluded characters
                if any(c not in exclude_chars for c in word):
                    furigana_text.append(f"<ruby>{word}<rt>{clean_translit}</rt></ruby>")
                else:
                    furigana_text.append(word)
            else:
                # Fallback if no transliteration available
                furigana_text.append(word)

        return " ".join(furigana_text)

    return "".join(furigana_text)


def transliterate_chinese(text, mode="color"):
    """
    Main function for Chinese transliteration

    Args:
        text: Chinese text to transliterate
        mode: 'simple' for basic pinyin, 'color' for color-coded syntax/POS
    """
    return get_pinyin_annotations(text, color_coded=(mode == "color"))


# Function to transliterate text
def transliterate(input_text, language):
    language = language.lower()
    language = language_map.get(language, language)
    if sys.getsizeof(input_text) > 1_000_000:  # 1MB
        return "Input too large"
    if not input_text:
        return ""
    if language == "chinese":
        # return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.TONE))
        return transliterate_chinese(input_text)
    elif language == "japanese":
        import pykakasi as original_pykakasi

        test_kakasi = original_pykakasi.kakasi()
        result = test_kakasi.convert(input_text)
        # print(f"Transliteration result: {[{'orig': item['orig'], 'trans': item['hira'] or item['hepburn']} for item in result]}")
        return [{"orig": item["orig"], "trans": item["hepburn"]} for item in result]

        try:
            from modified.modified_kakasi import Kakasi

            kakasi = Kakasi()
            result = kakasi.convert(input_text)

            # Validate the result structure
            if not isinstance(result, list):
                raise ValueError("Unexpected result format from Kakasi")

            for item in result:
                if not isinstance(item, dict) or "orig" not in item or "hepburn" not in item:
                    raise ValueError("Invalid item structure in Kakasi result")

            return result
        except Exception as e:
            print(f"Japanese transliteration error: {e}")
            # Fallback: return each character with itself as reading
            return [{"orig": c, "hepburn": c} for c in input_text]
    elif language == "russian":
        try:
            # Using the modified version of the transliterate library
            from modified.modified_russian import translit as ru_translit

            # Transliterate from Cyrillic to Latin
            return ru_translit(input_text, "ru", reversed=True)
        except Exception as e:
            print(f"Error in Russian transliteration: {e}")
            return input_text
    elif language == "hindi":
        result = indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return result
    elif language == "arabic":
        # return original_pyarabic.custom_utf82latin(input_text)  # Will use patched version
        from modified.modified_pyarabic import custom_utf82latin as custom_arabic

        return custom_arabic(input_text)
    elif language == "korean":
        from modified.modified_hangul import Transliter as KoreanTransliter

        try:
            transliter = KoreanTransliter(rule=academic)  # Using academic transliteration rule
            result = transliter.translit(input_text)
            # Ensure we're returning a list of (char, trans) tuples
            if result and isinstance(result[0], tuple) and len(result[0]) == 2:
                return result
            else:
                # Fallback: return characters with themselves as transliteration
                return [(c, c) for c in input_text]
        except Exception as e:
            print(f"Korean transliteration error: {e}")
            # Fallback: return characters with themselves as transliteration
            return [(c, c) for c in input_text]
    else:
        return input_text


def transliterate_for_subtitles(text, language):
    """
    Transliterates text specifically for subtitles, handling language-specific formatting.
    Returns the transliterated text ready to be appended below the original text.
    """
    language = language.lower()
    language = language_map.get(language, language)

    if not text:
        return ""

    # First get the raw transliteration
    raw_transliteration = transliterate(text, language)

    # Language-specific processing
    if language == "japanese":
        # For Japanese, we get a list of dicts from kakasi
        if isinstance(raw_transliteration, list) and all(
            isinstance(x, dict) for x in raw_transliteration
        ):
            # Join the hepburn romanizations with spaces
            translit_text = " ".join(item.get("hepburn", "") for item in raw_transliteration)
        else:
            translit_text = str(raw_transliteration)

    elif language == "korean":
        # For Korean, we get a list of [char, trans] pairs
        if isinstance(raw_transliteration, list) and all(
            isinstance(x, list) and len(x) == 2 for x in raw_transliteration
        ):
            translit_text = " ".join(trans for [char, trans] in raw_transliteration)
        else:
            translit_text = str(raw_transliteration)

    elif language == "chinese":
        # For Chinese, we already get properly formatted pinyin from get_pinyin_annotations
        translit_text = raw_transliteration

    elif language in ["hindi", "arabic", "russian"]:
        # For these languages, we get a space-separated string
        translit_text = " ".join(list(str(raw_transliteration)))

    else:
        # Default case for unsupported languages
        translit_text = ""

    # Clean up the transliterated text for subtitles
    # translit_text = translit_text.strip()

    # Formatting improvements
    # translit_text = format_transliteration(translit_text)

    return translit_text


def format_transliteration(text):
    """
    Formats transliterated text for better readability in subtitles.
    """
    # Add spaces after commas and periods if they're missing
    text = re.sub(r"([,.!?])([^\s])", r"\1 \2", text)

    # Remove duplicate spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Capitalize first letter of each sentence
    sentences = re.split(r"(?<=[.!?])\s+", text)
    text = " ".join(
        sentence[0].upper() + sentence[1:] if sentence else "" for sentence in sentences
    )

    return text


# Main function to test transliterate
if __name__ == "__main__":
    # Example usage
    input_text = "Testing Japanese"
    language = "japanese"
    result = transliterate(input_text, language)
    print(result)

    sample_text = "我喜欢学习中文。"

    # Simple mode
    simple_result = transliterate_chinese(sample_text, "simple")
    print("Simple mode:")
    print(simple_result)

    # Color-coded mode
    color_result = transliterate_chinese(sample_text, "color")
    print("\nColor-coded mode:")
    print(color_result)

    # Advanced analysis
    detailed_analysis = process_chinese_advanced(sample_text)
    print("\nDetailed analysis:")
    for item in detailed_analysis:
        print(
            f"Word: {item['word']}, Pinyin: {item['transliteration']}, Syntax: {item['syntax']}, POS: {item['pos']}"
        )
