import sys
import os
import re
from pathlib import Path

language_map = {
    'ja': 'japanese',
    'jp': 'japanese',
    'ko': 'korean',
    'kr': 'korean',
    'zh-cn': 'chinese',
    'zh-CN': 'chinese',
    'hi': 'hindi',
    'in': 'hindi',
    'ar': 'arabic',
    'ru': 'russian',
}

# Android-specific path setup
if 'com.termux' in os.environ.get('PREFIX', ''):
    # Termux environment
    sys.path.insert(0, '/data/data/com.termux/files/home/transliteration')
    BASE_DIR = Path('/data/data/com.termux/files/home/transliteration')
else:
    BASE_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(BASE_DIR))
# Import modified versions
try:
    from modified.modified_kakasi import Kakasi as CustomKakasi
    from modified.modified_hangul import Transliter as CustomTransliter 
    from modified.modified_pyarabic import custom_utf82latin as custom_arabic
except ImportError:
    # Fallback to original versions if modified not found
    CustomKakasi = None
    CustomTransliter = None
    custom_arabic = None

# Import original libraries
import pykakasi as original_pykakasi
from hangul_romanize import Transliter as OriginalTransliter
# from pyarabic import trans as original_pyarabic
from hangul_romanize.rule import academic
import pypinyin

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
    jieba = type('', (), {'cut': jieba_cut})()

def format_transliteration(text):
    # Add spaces after commas and periods
    text = re.sub(r'([,.])', r'\1 ', text)
    
    # Add spaces around hyphens
    text = re.sub(r'([a-zA-Z])-([a-zA-Z])', r'\1 - \2', text)
    
    # Break long sentences into smaller chunks
    sentences = re.split(r'(?<=[。！？])', text)
    formatted_text = '\n'.join([s.strip() for s in sentences if s.strip()])
    
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
    tokens = re.findall(r'\w+|\W+', text)
    
    # Initialize a list to store the corrected tokens
    corrected_tokens = []
    
    for token in tokens:
        if re.match(r'\W+', token):  # Check if the token is punctuation
            if corrected_tokens:  # If there is a previous word, append punctuation to it
                corrected_tokens[-1] += token
            else:  # If no previous word exists, add the punctuation as a standalone token
                corrected_tokens.append(token)
        else:  # If the token is a word, add it to the list
            corrected_tokens.append(token)
    
    return corrected_tokens

def append_punctuation_to_previous_word(segmented_words):
    # List of punctuation marks to handle
    punctuation_marks = ['。', '，', '！', '？', '、', '「', '」', '『', '』', '（', '）', '《', '》', '.', ',', '!', '?']
    
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

def get_pinyin_annotations(text):
    from pypinyin import lazy_pinyin, Style, load_phrases_dict
    import re
    
    # Custom phrase corrections
    load_phrases_dict({
        "什么": [["shén"], ["me"]],
        "怎么": [["zěn"], ["me"]],
        "明白": [["míng"], ["bai"]]
    })
    
    # Complete exclusion set
    exclude_chars = {
        ' ', '.', ',', '!', '?', '。', '，', '！', '？', '、',
        '「', '」', '『', '』', '（', '）', '《', '》', '“', '”',
        '‘', '’', '…', '—', '：', ':', '；', ';', '～', '°', 'º'
    }

    # Get pinyin with word grouping
    pinyin_list = lazy_pinyin(
        text,
        style=Style.TONE,
        neutral_tone_with_five=True,
        errors=lambda x: [x] if x in exclude_chars else [''],
        strict=False
    )
    
    # Build proper ruby annotations
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        
        if char in exclude_chars:
            result.append(char)
            i += 1
        elif re.match(r'^[\u4e00-\u9fff]$', char):
            # Handle multi-character words
            word = char
            while i+1 < len(text) and re.match(r'^[\u4e00-\u9fff]$', text[i+1]):
                word += text[i+1]
                i += 1
            
            # Get pinyin for the entire word
            word_pinyin = lazy_pinyin(
                word,
                style=Style.TONE,
                neutral_tone_with_five=True
            )
            
            # Annotate each character
            for c, py in zip(word, word_pinyin):
                if py and py != c:
                    result.append(f'<ruby>{c}<rt>{py}</rt></ruby>')
                else:
                    result.append(c)
            
            i += 1
        else:
            result.append(char)
            i += 1
    
    return ''.join(result)

# Function to add furigana to text
def add_furigana(text, transliteration, language):
    language = language.lower()
    language = language_map.get(language, language)    
    if not text:
        return ""
    # tokens = text
    exclude_chars = [' ', '.', ',', '!', '?', '。', '，', '-', '！', '？', '、', '「', '」', '『', '』', '（', '）', '《', '》']
    if language == "japanese":
        trans_words = [item['hepburn'] for item in transliteration]
    elif language == "korean":
        trans_words = transliteration  # Use the list of tuples directly
    else:
       trans_words = transliteration.split()
    
    furigana_text = []
    trans_index = 0
    if language == "japanese":
        # Ensure we have valid transliteration data
        if not isinstance(transliteration, list):
            transliteration = [{"orig": c, "hepburn": c} for c in text]
            
        # Get original characters and romaji readings
        segmented_chars = []
        trans_words = []
        
        for item in transliteration:
            if isinstance(item, dict) and 'orig' in item and 'hepburn' in item:
                segmented_chars.append(item['orig'])
                trans_words.append(item['hepburn'])
            else:
                # Fallback for invalid items
                char = item.get('orig', '') if isinstance(item, dict) else str(item)
                segmented_chars.append(char)
                trans_words.append(char)
        
        # Generate furigana
        trans_index = 0
        for char in segmented_chars:
            if trans_index < len(trans_words):
                romaji = trans_words[trans_index]
                trans_index += 1
                if char.strip() == '' or char in exclude_chars:
                    furigana_text.append(char)
                else:
                    # Clean up romaji (remove numbers representing pitch accents)
                    clean_romaji = re.sub(r'\d', '', romaji).strip()
                    if not clean_romaji:
                        clean_romaji = char
                    furigana_text.append(f"<ruby>{char}<rt>{clean_romaji}</rt></ruby>")
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
        pinyin = get_pinyin_annotations(text)
        return pinyin
    elif language in ["hindi", "arabic", "russian"]:
        segmented_words = text.split()
        language_excludes = {
            "hindi": ['।', '॥', '़', '्'],  # Hindi-specific characters
            "arabic": ['ـ', 'َ', 'ُ', 'ِ', 'ّ', 'ْ'],  # Arabic diacritics
            "russian": ['«', '»', '—', '…']  # Russian-specific punctuation
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
                clean_translit = ''.join([c for c in translit if c not in exclude_chars])
                
                # Only apply ruby if we have non-excluded characters
                if any(c not in exclude_chars for c in word):
                    furigana_text.append(f"<ruby>{word}<rt>{clean_translit}</rt></ruby>")
                else:
                    furigana_text.append(word)
            else:
                # Fallback if no transliteration available
                furigana_text.append(word)
        
        return ' '.join(furigana_text)
    
    return ''.join(furigana_text)

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
        return get_pinyin_annotations(input_text)
    elif language == "japanese":
        try:
            from modified.modified_kakasi import Kakasi
            kakasi = Kakasi()
            result = kakasi.convert(input_text)
            
            # Validate the result structure
            if not isinstance(result, list):
                raise ValueError("Unexpected result format from Kakasi")
                
            for item in result:
                if not isinstance(item, dict) or 'orig' not in item or 'hepburn' not in item:
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
            return ru_translit(input_text, 'ru', reversed=True)
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
        if isinstance(raw_transliteration, list) and all(isinstance(x, dict) for x in raw_transliteration):
            # Join the hepburn romanizations with spaces
            translit_text = ' '.join(item.get('hepburn', '') for item in raw_transliteration)
        else:
            translit_text = str(raw_transliteration)
            
    elif language == "korean":
        # For Korean, we get a list of [char, trans] pairs
        if isinstance(raw_transliteration, list) and all(isinstance(x, list) and len(x) == 2 for x in raw_transliteration):
            translit_text = ' '.join(trans for [char, trans] in raw_transliteration)
        else:
            translit_text = str(raw_transliteration)
            
    elif language == "chinese":
        # For Chinese, we already get properly formatted pinyin from get_pinyin_annotations
        translit_text = raw_transliteration
        
    elif language in ["hindi", "arabic", "russian"]:
        # For these languages, we get a space-separated string
        translit_text = ' '.join(list(str(raw_transliteration)))
        
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
    text = re.sub(r'([,.!?])([^\s])', r'\1 \2', text)
    
    # Remove duplicate spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Capitalize first letter of each sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    text = ' '.join(sentence[0].upper() + sentence[1:] if sentence else '' 
                   for sentence in sentences)
    
    return text