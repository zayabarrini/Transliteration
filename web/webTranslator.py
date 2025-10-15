from flask import Flask, render_template, request
from deep_translator import GoogleTranslator

app = Flask(__name__)

LANGUAGES = [
    {"code": "hi", "name": "Hindi"},
    {"code": "ar", "name": "Arabic"},
    {"code": "ru", "name": "Russian"},
    {"code": "de", "name": "German"},
    {"code": "fr", "name": "French"},
    {"code": "it", "name": "Italian"},
    # {'code': 'en', 'name': 'English'},
    {"code": "es", "name": "Spanish"},
]


def translate_word_by_word(text, target_lang):
    words = text.split()
    translated_words = []

    for word in words:
        try:
            # Skip translation if the word is just punctuation or whitespace
            if word.strip() == "":
                translated_words.append(word)
                continue

            translated = GoogleTranslator(source="auto", target=target_lang).translate(word)
            translated_words.append(f"<ruby>{translated}<rt>{word}</rt></ruby>")
        except Exception as e:
            print(f"Error translating word '{word}': {str(e)}")
            translated_words.append(f'<span class="error">{word}</span>')

    return " ".join(translated_words)


@app.route("/", methods=["GET", "POST"])
def translator():
    input_text = ""
    results = []

    if request.method == "POST":
        input_text = request.form["text"]

        if input_text.strip():
            for lang in LANGUAGES:
                try:
                    translation = translate_word_by_word(input_text, lang["code"])
                    results.append({"language": lang["name"], "translation": translation})
                except Exception as e:
                    print(f"Error with {lang['name']} translation: {str(e)}")
                    results.append(
                        {
                            "language": lang["name"],
                            "translation": f'<span class="error">Translation failed</span>',
                        }
                    )

    return render_template("translator.html", input_text=input_text, results=results)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
