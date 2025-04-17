import sys
import os
import re
from pathlib import Path

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
from pyarabic import trans as original_pyarabic
from hangul_romanize.rule import academic
import pypinyin

# Apply monkey patches if custom versions exist
if CustomKakasi:
    original_pykakasi.kakasi = lambda: CustomKakasi()

if CustomTransliter:
    def patched_transliter_init(self, rule=None):
        CustomTransliter.__init__(self, rule or academic)
    OriginalTransliter.__init__ = patched_transliter_init

if custom_arabic and not hasattr(original_pyarabic, 'custom_utf82latin'):
    original_pyarabic.custom_utf82latin = custom_arabic

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
    """Check if a token contains only Latin characters."""
    return bool(re.match(r'^[A-Za-z0-9\s\W_]+$', token))

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
        style=Style.NORMAL,
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
                style=Style.NORMAL,
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
    if not text:
        return ""
    # tokens = text
    exclude_chars = [' ', '.', ',', '!', '?', '。', '，', '！', '？', '、', '「', '」', '『', '』', '（', '）', '《', '》']
    if language == "japanese":
        trans_words = [item['hepburn'] for item in transliteration]
    elif language == "korean":
        trans_words = transliteration  # Use the list of tuples directly
    else:
        trans_words = transliteration.split()
    
    furigana_text = []
    trans_index = 0
    if language == "japanese":
        segmented_chars = [item['orig'] for item in transliteration]
        # segmented_chars = list(token)
        for char in segmented_chars:
            if trans_index < len(trans_words):
                romaji = trans_words[trans_index]
                trans_index += 1
                if char in exclude_chars:
                    furigana_text.append(char)
                else:
                    furigana_text.append(f"<ruby>{char}<rt>{romaji}</rt></ruby>")
    elif language == "korean":
        # Process each character in the token
        for [char, trans] in trans_words:
            if char in exclude_chars:
                furigana_text.append(char)
            else:
                furigana_text.append(f"<ruby>{char}<rt>{trans}</rt></ruby>")
    elif language == "chinese":
        pinyin = get_pinyin_annotations(text)
        print(pinyin)
        return pinyin
        # tokens = tokenize_text(text)
        # for token in tokens:
        #     if is_latin(token):
        #         furigana_text.append(f"<ruby>{token}</ruby>")
        #     else:
        #         segmented_words = list(jieba.cut(token))
        #         corrected_words = append_punctuation_to_previous_word(segmented_words)
 
        #         for word in corrected_words:
        #             num_syllables = len(word)
        #             pinyin = ' '.join(trans_words[trans_index:trans_index + num_syllables])
        #             pinyin = re.sub(r'[^\w\s]', '', pinyin)
        #             trans_index += num_syllables
        #             furigana_text.append(f"<ruby>{word}<rt>{pinyin}</rt></ruby>")
    elif language in ["hindi", "arabic", "russian"]:
        segmented_words = text.split()
        for word in segmented_words:
            if trans_index < len(trans_words):
                translit = trans_words[trans_index]
                trans_index += 1
                furigana_text.append(f"<ruby>{word}<rt>{translit}</rt></ruby>")
            else:
                furigana_text.append(f"<ruby>{word}</ruby>")
        return ' '.join(furigana_text)
    
    return ''.join(furigana_text)

# Function to transliterate text
def transliterate(input_text, language):
    if sys.getsizeof(input_text) > 1_000_000:  # 1MB
        return "Input too large" 
    if not input_text:
        return ""
    if language == "chinese":
        # return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.NORMAL))
        return get_pinyin_annotations(input_text)
    elif language == "japanese":
        print("It's Japanese")
        kakasi = original_pykakasi.kakasi()  # Will use patched version
        return kakasi.convert(input_text)
        # kakasi = original_pykakasi.kakasi()
        # kakasi.setMode("H", "a")  # Hiragana to Romaji
        # kakasi.setMode("K", "a")  # Katakana to Romaji
        # kakasi.setMode("J", "a")  # Kanji to Romaji
        # converter = kakasi.getConverter()
    elif language == "russian":
        import transliterate
        return transliterate.translit(input_text, 'ru', reversed=True)
    elif language == "hindi":
        result = indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return result
    elif language == "arabic":
        return original_pyarabic.custom_utf82latin(input_text)  # Will use patched version
    elif language == "korean":
        transliter = OriginalTransliter(rule=academic)  # Explicit rule
        result = transliter.translit(input_text)
        return result
    else:
        return input_text