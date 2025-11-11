import re

from deep_translator import GoogleTranslator
from flask import Flask, render_template, request

app = Flask(__name__)

# Supported languages with direction information
LANGUAGES = [
    {"code": "en", "name": "English", "direction": "ltr"},
    {"code": "es", "name": "Spanish", "direction": "ltr"},
    {"code": "fr", "name": "French", "direction": "ltr"},
    {"code": "de", "name": "German", "direction": "ltr"},
    {"code": "it", "name": "Italian", "direction": "ltr"},
    {"code": "pt", "name": "Portuguese", "direction": "ltr"},
    {"code": "ru", "name": "Russian", "direction": "ltr"},
    {"code": "ja", "name": "Japanese", "direction": "ltr"},
    {"code": "ko", "name": "Korean", "direction": "ltr"},
    {"code": "zh-cn", "name": "Chinese (Simplified)", "direction": "ltr"},
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
    """Split text into sentences using regex, treating \n as sentence boundaries"""
    # Split on sentence endings OR line breaks followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+|(?<=\n)\s*', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def translate_word_by_word(text, target_lang):
    """Translate text word by word with ruby annotations"""
    words = text.split()
    translated_words = []

    for word in words:
        try:
            # Skip translation if the word is just punctuation or whitespace
            if word.strip() == "":
                translated_words.append(word)
                continue

            translated = GoogleTranslator(source="auto", target=target_lang).translate(word)
            # Use span with class for better styling control
            translated_words.append(f'<span class="word-ruby"><ruby>{translated}<rt>{word}</rt></ruby></span>')
        except Exception as e:
            print(f"Error translating word '{word}': {str(e)}")
            translated_words.append(f'<span class="error">{word}</span>')

    return ' '.join(translated_words)

def translate_full_sentence(text, target_lang):
    """Translate full sentence as a whole"""
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"Error translating sentence '{text}': {str(e)}")
        return f"<span class='error'>Translation failed: {str(e)}</span>"

def get_language_direction(lang_code):
    """Get text direction for a language code"""
    lang = next((l for l in LANGUAGES if l["code"] == lang_code), None)
    return lang["direction"] if lang else "ltr"

def get_language_class(lang_code):
    """Get CSS class for language-specific styling"""
    if lang_code in ["ar", "he", "fa", "ur"]:
        return "rtl-language"
    elif lang_code in ["ja", "ko", "zh-cn"]:
        return "cjk-language"
    else:
        return "ltr-language"

@app.route("/", methods=["GET", "POST"])
def translator():
    input_text = ""
    result = None
    selected_lang = ""

    if request.method == "POST":
        input_text = request.form["text"]
        selected_lang = request.form["target_lang"]

        if input_text.strip() and selected_lang:
            try:
                lang_name = next((lang["name"] for lang in LANGUAGES if lang["code"] == selected_lang), selected_lang)
                sentences = split_into_sentences(input_text)
                sentence_results = []
                
                for sentence in sentences:
                    word_by_word = translate_word_by_word(sentence, selected_lang)
                    full_translation = translate_full_sentence(sentence, selected_lang)
                    
                    sentence_results.append({
                        "original": sentence,
                        "word_by_word": word_by_word,
                        "full_translation": full_translation
                    })
                
                result = {
                    "language": lang_name,
                    "language_class": get_language_class(selected_lang),
                    "text_direction": get_language_direction(selected_lang),
                    "sentences": sentence_results
                }
                
            except Exception as e:
                print(f"Error with translation: {str(e)}")
                result = {
                    "language": "Unknown",
                    "language_class": "ltr-language",
                    "text_direction": "ltr",
                    "sentences": [{
                        "original": input_text,
                        "word_by_word": f'<span class="error">Translation failed</span>',
                        "full_translation": f'<span class="error">Translation failed: {str(e)}</span>'
                    }]
                }

    return render_template(
        "translator2language.html", 
        input_text=input_text, 
        result=result,
        languages=LANGUAGES,
        selected_lang=selected_lang
    )

if __name__ == "__main__":
    app.run(debug=True, port=5006)