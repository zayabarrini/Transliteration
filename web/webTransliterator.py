import re

from deep_translator import GoogleTranslator
from flask import Flask, jsonify, render_template, request

from transliteration import (
    analyze_chinese_syntax,
    get_grammatical_classes_from_pos,
    get_pinyin_annotations,
    get_pinyin_for_word,
    is_punctuation,
    transliterate,
)

app = Flask(__name__)

# Language character ranges for detection
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
}

# Language priority for ambiguous characters (Chinese/Japanese share Kanji)
LANGUAGE_PRIORITY = ["chinese", "japanese", "korean", "hindi", "arabic", "russian"]

# Language code mapping for translation
LANGUAGE_CODE_MAP = {
    "japanese": "ja",
    "chinese": "zh-CN", 
    "korean": "ko",
    "hindi": "hi",
    "arabic": "ar",
    "russian": "ru"
}

# Target languages (languages we translate TO)
TARGET_LANGUAGES = [
    {"code": "en", "name": "English", "direction": "ltr"},
    {"code": "es", "name": "Spanish", "direction": "ltr"},
    {"code": "fr", "name": "French", "direction": "ltr"},
    {"code": "de", "name": "German", "direction": "ltr"},
    {"code": "it", "name": "Italian", "direction": "ltr"},
    {"code": "pt", "name": "Portuguese", "direction": "ltr"},
    {"code": "ru", "name": "Russian", "direction": "ltr"},
    {"code": "ja", "name": "Japanese", "direction": "ltr"},
    {"code": "ko", "name": "Korean", "direction": "ltr"},
    {"code": "zh-CN", "name": "Chinese (Simplified)", "direction": "ltr"},
    {"code": "ar", "name": "Arabic", "direction": "rtl"},
    {"code": "he", "name": "Hebrew", "direction": "rtl"},
    {"code": "fa", "name": "Persian", "direction": "rtl"},
    {"code": "ur", "name": "Urdu", "direction": "rtl"},
    {"code": "hi", "name": "Hindi", "direction": "ltr"},
    {"code": "tr", "name": "Turkish", "direction": "ltr"},
    {"code": "nl", "name": "Dutch", "direction": "ltr"},
    {"code": "sv", "name": "Swedish", "direction": "ltr"},
    {"code": "pl", "name": "Polish", "direction": "ltr"},
    {"code": "vi", "name": "Vietnamese", "direction": "ltr"},
    {"code": "th", "name": "Thai", "direction": "ltr"},
    {"code": "id", "name": "Indonesian", "direction": "ltr"}
]

def detect_language_char(char):
    """Detect which language a character belongs to"""
    char_code = ord(char)
    
    # Skip common punctuation and whitespace
    if char in ' .,!?。，！？、」「『』（）《》-—–…':
        return "punctuation"
    
    for lang, ranges in LANGUAGE_CHAR_RANGES.items():
        for start, end in ranges:
            if isinstance(start, tuple):  # Multiple ranges
                for r_start, r_end in ranges:
                    if r_start <= char_code <= r_end:
                        return lang
            else:  # Single range
                if start <= char_code <= end:
                    return lang
    
    return "latin"  # Default to latin for unrecognized characters

def detect_language_text(text):
    """Detect the primary language of a text block"""
    if not text.strip():
        return "unknown"
    
    char_languages = []
    for char in text:
        lang = detect_language_char(char)
        if lang not in ["punctuation", "latin"]:
            char_languages.append(lang)
    
    if not char_languages:
        return "latin"  # No special characters found, treat as latin
    
    # Count language occurrences
    from collections import Counter
    lang_counts = Counter(char_languages)
    
    # Handle Chinese/Japanese ambiguity with better heuristics
    if "japanese" in lang_counts and "chinese" in lang_counts:
        # If there are Japanese-specific characters, prioritize Japanese
        if contains_japanese_specific_chars(text):
            return "japanese"
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

def split_into_sentences(text):
    """Split text into sentences"""
    sentences = re.split(r'(?<=[.!?。！？])\s+', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def should_process_word(word):
    """Check if word should be processed (not space/punctuation)"""
    if not word.strip():
        return False
    if is_punctuation(word):
        return False
    if word.isspace():
        return False
    return True

def process_word_breakdown(text, detected_lang, target_lang):
    """Process text for word-by-word breakdown with translation and transliteration"""
    if detected_lang == "chinese":
        return process_chinese_breakdown(text, target_lang)
    elif detected_lang == "japanese":
        return process_japanese_breakdown(text, target_lang)
    else:
        return process_other_language_breakdown(text, detected_lang, target_lang)

def process_japanese_breakdown(text, target_lang):
    """Process Japanese text using pykakasi segmentation for both transliteration and translation"""
    result = []
    
    try:
        import pykakasi
        kks = pykakasi.kakasi()
        analyzed = kks.convert(text)
        
        for item in analyzed:
            original = item.get("orig", "")
            romaji = item.get("hepburn", "")
            
            if not should_process_word(original):
                # Add non-processable items directly
                result.append({
                    "word": original,
                    "translation": "",
                    "transliteration": "",
                    "processable": False
                })
                continue
            
            # Get translation for the segmented word
            try:
                translation = GoogleTranslator(source="ja", target=target_lang).translate(original)
            except Exception as e:
                translation = f"[Error: {str(e)}]"
            
            result.append({
                "word": original,
                "translation": translation,
                "transliteration": romaji,
                "processable": True
            })
            
    except Exception as e:
        print(f"Error in Japanese processing: {e}")
        # Fallback: simple word splitting
        return process_other_language_breakdown(text, "ja", target_lang)
    
    return result

def process_chinese_breakdown(text, target_lang):
    """Process Chinese text with detailed breakdown"""
    result = []
    
    # Use jieba for Chinese word segmentation
    import jieba.posseg as pseg
    words = list(pseg.cut(text))
    
    for word, pos in words:
        if not should_process_word(word):
            # Add non-processable items directly
            result.append({
                "word": word,
                "translation": "",
                "transliteration": "",
                "syntax": "",
                "pos": "punct",
                "grammatical_class": "",
                "processable": False
            })
        else:
            # Get translation
            try:
                translation = GoogleTranslator(source="zh-CN", target=target_lang).translate(word)
            except Exception as e:
                translation = f"[Error: {str(e)}]"
            
            # Get pinyin transliteration
            transliteration = get_pinyin_for_word(word)
            
            # Get syntax and grammatical class
            syntax_analysis = analyze_chinese_syntax(word)
            if syntax_analysis:
                syntax = syntax_analysis[0][1] if len(syntax_analysis) > 0 else ""
                grammatical_class = get_grammatical_classes_from_pos(pos)
            else:
                syntax = ""
                grammatical_class = get_grammatical_classes_from_pos(pos)
            
            result.append({
                "word": word,
                "translation": translation,
                "transliteration": transliteration,
                "syntax": syntax,
                "pos": pos,
                "grammatical_class": grammatical_class,
                "processable": True
            })
    
    return result

def process_other_language_breakdown(text, detected_lang, target_lang):
    """Process other languages word by word"""
    result = []
    
    # Tokenize while preserving spaces and punctuation
    tokens = re.findall(r'\S+|\s+', text)
    
    for token in tokens:
        if not should_process_word(token):
            # Add spaces and punctuation directly
            result.append({
                "word": token,
                "translation": "",
                "transliteration": "",
                "processable": False
            })
            continue
        
        # Get translation
        try:
            source_code = LANGUAGE_CODE_MAP.get(detected_lang, detected_lang)
            translation = GoogleTranslator(source=source_code, target=target_lang).translate(token)
        except Exception as e:
            translation = f"[Error: {str(e)}]"
        
        # Get transliteration
        try:
            transliteration_result = transliterate(token, detected_lang)
            
            if detected_lang == "korean" and isinstance(transliteration_result, list):
                transliteration = " ".join([trans for char, trans in transliteration_result])
            else:
                transliteration = str(transliteration_result)
                
        except Exception as e:
            transliteration = f"[Error: {str(e)}]"
        
        result.append({
            "word": token,
            "translation": translation,
            "transliteration": transliteration,
            "processable": True
        })
    
    return result

def translate_full_sentence(text, detected_lang, target_lang):
    """Translate full sentence"""
    try:
        source_code = LANGUAGE_CODE_MAP.get(detected_lang, detected_lang)
        translated = GoogleTranslator(source=source_code, target=target_lang).translate(text)
        return translated
    except Exception as e:
        return f"Translation error: {str(e)}"

def get_language_direction(lang_code):
    """Get text direction for language"""
    # Check if it's a detected language name
    if lang_code in LANGUAGE_CHAR_RANGES:
        if lang_code in ["arabic"]:
            return "rtl"
        return "ltr"
    
    # Check target languages
    lang = next((l for l in TARGET_LANGUAGES if l["code"] == lang_code), None)
    return lang["direction"] if lang else "ltr"

@app.route("/", methods=["GET", "POST"])
def transliterator():
    input_text = ""
    result = None
    selected_target_lang = "en"  # Default to English

    if request.method == "POST":
        input_text = request.form["text"]
        selected_target_lang = request.form["target_lang"]

        if input_text.strip() and selected_target_lang:
            try:
                # Detect language from input text
                detected_lang = detect_language_text(input_text)
                
                sentences = split_into_sentences(input_text)
                sentence_results = []
                
                for sentence in sentences:
                    # Detect language for each sentence (in case of mixed content)
                    sentence_lang = detect_language_text(sentence)
                    word_breakdown = process_word_breakdown(sentence, sentence_lang, selected_target_lang)
                    full_translation = translate_full_sentence(sentence, sentence_lang, selected_target_lang)
                    
                    sentence_results.append({
                        "original": sentence,
                        "word_breakdown": word_breakdown,
                        "full_translation": full_translation,
                        "detected_language": sentence_lang
                    })
                
                result = {
                    "detected_language": detected_lang,
                    "target_language": selected_target_lang,
                    "detected_language_name": detected_lang.title(),
                    "target_language_name": next((lang["name"] for lang in TARGET_LANGUAGES if lang["code"] == selected_target_lang), selected_target_lang),
                    "text_direction": get_language_direction(detected_lang),
                    "sentences": sentence_results
                }
                
            except Exception as e:
                print(f"Error processing text: {str(e)}")
                result = {
                    "error": str(e),
                    "detected_language": "unknown",
                    "target_language": selected_target_lang,
                    "text_direction": "ltr",
                    "sentences": []
                }

    return render_template(
        "translator2transliteration.html", 
        input_text=input_text, 
        result=result,
        target_languages=TARGET_LANGUAGES,
        selected_target_lang=selected_target_lang
    )

@app.route("/api/transliterate", methods=["POST"])
def api_transliterate():
    """API endpoint for transliteration only"""
    data = request.json
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    try:
        detected_lang = detect_language_text(text)
        result = transliterate(text, detected_lang)
        return jsonify({
            "transliteration": str(result),
            "detected_language": detected_lang
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5009)