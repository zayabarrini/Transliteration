import re

from deep_translator import GoogleTranslator
from flask import Flask, render_template, request

app = Flask(__name__)

# Supported languages
LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "it", "name": "Italian"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ru", "name": "Russian"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "zh-cn", "name": "Chinese (Simplified)"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
    {"code": "tr", "name": "Turkish"},
    {"code": "nl", "name": "Dutch"},
    {"code": "sv", "name": "Swedish"},
    {"code": "pl", "name": "Polish"},
    {"code": "vi", "name": "Vietnamese"},
    {"code": "th", "name": "Thai"},
    {"code": "id", "name": "Indonesian"},
    {"code": "he", "name": "Hebrew"}
]

def split_into_sentences(text):
    """Split text into sentences using regex"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def translate_word_by_word(text, target_lang):
    """Translate text word by word with ruby annotations and proper spacing"""
    words = text.split()
    translated_words = []

    for word in words:
        try:
            # Skip translation if the word is just punctuation or whitespace
            if word.strip() == "":
                translated_words.append(word)
                continue

            translated = GoogleTranslator(source="auto", target=target_lang).translate(word)
            # Add non-breaking space and proper spacing
            translated_words.append(f'<ruby class="word-ruby">{translated}<rt>{word}</rt></ruby>')
        except Exception as e:
            print(f"Error translating word '{word}': {str(e)}")
            translated_words.append(f'<span class="error">{word}</span>')

    # Join with non-breaking spaces to maintain proper spacing
    return ' '.join(translated_words)

def translate_full_sentence(text, target_lang):
    """Translate full sentence as a whole"""
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"Error translating sentence '{text}': {str(e)}")
        return f"<span class='error'>Translation failed: {str(e)}</span>"

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
                    "sentences": sentence_results
                }
                
            except Exception as e:
                print(f"Error with translation: {str(e)}")
                result = {
                    "language": "Unknown",
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