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

# Source languages (languages we transliterate FROM)
SOURCE_LANGUAGES = [
    {"code": "ja", "name": "Japanese", "direction": "ltr"},
    {"code": "ko", "name": "Korean", "direction": "ltr"},
    {"code": "zh-CN", "name": "Chinese", "direction": "ltr"},
    {"code": "hi", "name": "Hindi", "direction": "ltr"},
    {"code": "ar", "name": "Arabic", "direction": "rtl"},
    {"code": "ru", "name": "Russian", "direction": "ltr"},
]

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

def split_into_sentences(text):
    """Split text into sentences"""
    sentences = re.split(r'(?<=[.!?。！؟؟])\s+', text)
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

def process_word_breakdown(text, source_lang, target_lang):
    """Process text for word-by-word breakdown with translation and transliteration"""
    if source_lang == "zh-CN":
        return process_chinese_breakdown(text, target_lang)
    elif source_lang == "ja":
        return process_japanese_breakdown(text, target_lang)
    else:
        return process_other_language_breakdown(text, source_lang, target_lang)

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

def process_other_language_breakdown(text, source_lang, target_lang):
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
            translation = GoogleTranslator(source=source_lang, target=target_lang).translate(token)
        except Exception as e:
            translation = f"[Error: {str(e)}]"
        
        # Get transliteration
        try:
            transliteration_result = transliterate(token, source_lang)
            
            if source_lang == "ko" and isinstance(transliteration_result, list):
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

def translate_full_sentence(text, source_lang, target_lang):
    """Translate full sentence"""
    try:
        # Handle Chinese language code properly
        if source_lang == "zh-CN":
            source_lang = "zh-CN"
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        return translated
    except Exception as e:
        return f"Translation error: {str(e)}"

def get_language_direction(lang_code):
    """Get text direction for language"""
    # Check source languages first
    lang = next((l for l in SOURCE_LANGUAGES if l["code"] == lang_code), None)
    if not lang:
        # Check target languages
        lang = next((l for l in TARGET_LANGUAGES if l["code"] == lang_code), None)
    return lang["direction"] if lang else "ltr"

@app.route("/", methods=["GET", "POST"])
def transliterator():
    input_text = ""
    result = None
    selected_source_lang = ""
    selected_target_lang = "en"  # Default to English

    if request.method == "POST":
        input_text = request.form["text"]
        selected_source_lang = request.form["source_lang"]
        selected_target_lang = request.form["target_lang"]

        if input_text.strip() and selected_source_lang and selected_target_lang:
            try:
                sentences = split_into_sentences(input_text)
                sentence_results = []
                
                for sentence in sentences:
                    word_breakdown = process_word_breakdown(sentence, selected_source_lang, selected_target_lang)
                    full_translation = translate_full_sentence(sentence, selected_source_lang, selected_target_lang)
                    
                    sentence_results.append({
                        "original": sentence,
                        "word_breakdown": word_breakdown,
                        "full_translation": full_translation
                    })
                
                result = {
                    "source_language": selected_source_lang,
                    "target_language": selected_target_lang,
                    "source_language_name": next((lang["name"] for lang in SOURCE_LANGUAGES if lang["code"] == selected_source_lang), selected_source_lang),
                    "target_language_name": next((lang["name"] for lang in TARGET_LANGUAGES if lang["code"] == selected_target_lang), selected_target_lang),
                    "text_direction": get_language_direction(selected_source_lang),
                    "sentences": sentence_results
                }
                
            except Exception as e:
                print(f"Error processing text: {str(e)}")
                result = {
                    "error": str(e),
                    "source_language": selected_source_lang,
                    "target_language": selected_target_lang,
                    "text_direction": "ltr",
                    "sentences": []
                }

    return render_template(
        "translator2transliteration.html", 
        input_text=input_text, 
        result=result,
        source_languages=SOURCE_LANGUAGES,
        target_languages=TARGET_LANGUAGES,
        selected_source_lang=selected_source_lang,
        selected_target_lang=selected_target_lang
    )

@app.route("/api/transliterate", methods=["POST"])
def api_transliterate():
    """API endpoint for transliteration only"""
    data = request.json
    text = data.get("text", "")
    language = data.get("language", "")
    
    if not text or not language:
        return jsonify({"error": "Text and language are required"}), 400
    
    try:
        result = transliterate(text, language)
        return jsonify({"transliteration": str(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5007)