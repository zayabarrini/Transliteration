from flask import Flask, render_template_string, request
from transliteration.translationFunctions import translate_text, translate_parallel
from transliteration.transliteration import transliterate, add_furigana
from concurrent.futures import ThreadPoolExecutor
import re

app = Flask(__name__)

# Language codes and names
LANGUAGES = [
    {"code": "zh-ch", "name": "Chinese"},
    {"code": "jp", "name": "Japanese"},
    {"code": "hi", "name": "Hindi"},
    {"code": "ar", "name": "Arabic"},
    {"code": "ko", "name": "Korean"},
    {"code": "ru", "name": "Russian"},
    {"code": "de", "name": "German"},
    {"code": "fr", "name": "French"},
    {"code": "it", "name": "Italian"},
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
]

# Languages that need transliteration
TRANSLITERATION_LANGUAGES = ["jp", "ru", "hi", "ar", "ko", "zh-ch"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Text Translator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .input-form {
            margin-bottom: 30px;
        }
        textarea {
            width: 100%;
            height: 100px;
            margin-bottom: 10px;
        }
        button {
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        .result {
            margin-top: 30px;
        }
        .language-block {
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }
        h2 {
            margin-top: 0;
            color: #333;
        }
        .transliteration {
            font-style: bold;
            margin-top: 5px;
            line-height: 2;
        }
        .original {
            color: #666;
            font-weight: italic;
            margin-bottom: 5px;
        }
        ruby {
            ruby-position: under;
            margin-right: 0.2em;
        }
        rt {
            font-size: 0.7em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="input-form">
        <h1>Text Translator</h1>
        <form method="POST">
            <textarea name="text" placeholder="Enter text to translate" required>{{ input_text }}</textarea>
            <button type="submit">Translate</button>
        </form>
    </div>
    
    {% if results %}
    <div class="result">
        <h2>Translation Results</h2>
        {% for result in results %}
        <div class="language-block">
            <h3>{{ result.language }}</h3>
            <div class="original">{{ result.translation }}</div>
            {% if result.transliteration %}
            <div class="transliteration">
                {% if result.needs_html %}
                    {{ result.transliteration|safe }}
                {% else %}
                    {{ result.transliteration }}
                {% endif %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""


def process_translation(text, language_code):
    """Translate text and apply transliteration if needed."""
    translated = translate_text(text, language_code)

    transliterated = None
    needs_html = False

    if language_code in TRANSLITERATION_LANGUAGES:
        # Get full language name in lowercase for transliteration functions
        language_name = next(
            (lang["name"].lower() for lang in LANGUAGES if lang["code"] == language_code),
            language_code,
        )
        transliterated = transliterate(translated, language_name)
        if transliterated:
            needs_html = True
            transliterated = add_furigana(translated, transliterated, language_name)

    return {
        "language": next(
            (lang["name"] for lang in LANGUAGES if lang["code"] == language_code), language_code
        ),
        "translation": translated,
        "transliteration": transliterated,
        "needs_html": needs_html,  # Flag to indicate HTML content
    }


@app.route("/", methods=["GET", "POST"])
def index():
    input_text = ""
    results = []

    if request.method == "POST":
        input_text = request.form["text"]

        if input_text.strip():
            with ThreadPoolExecutor() as executor:
                # Process all translations in parallel
                futures = [
                    executor.submit(process_translation, input_text, lang["code"])
                    for lang in LANGUAGES
                ]
                results = [future.result() for future in futures]

    return render_template_string(HTML_TEMPLATE, input_text=input_text, results=results)


if __name__ == "__main__":
    app.run(debug=True)
