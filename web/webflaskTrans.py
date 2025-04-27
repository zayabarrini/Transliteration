from flask import Flask, render_template_string, request
from transliteration.translationFunctions import translate_text, translate_parallel
from transliteration.transliteration import transliterate, add_furigana
from concurrent.futures import ThreadPoolExecutor
import re

app = Flask(__name__)

# Language codes and names
LANGUAGES = [
    # {'code': 'zh-ch', 'name': 'Chinese'},
    # {'code': 'jp', 'name': 'Japanese'},
    # {'code': 'ko', 'name': 'Korean'},
    {'code': 'hi', 'name': 'Hindi'},
    {'code': 'ar', 'name': 'Arabic'},
    {'code': 'ru', 'name': 'Russian'},
    {'code': 'de', 'name': 'German'},
    {'code': 'fr', 'name': 'French'},
    {'code': 'it', 'name': 'Italian'},
    {'code': 'en', 'name': 'English'},
    {'code': 'es', 'name': 'Spanish'}
]

# Languages that need transliteration
TRANSLITERATION_LANGUAGES = ['jp', 'ru', 'hi', 'ar', 'ko', 'zh-ch']

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Text Translator</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles3.css') }}">
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

def add_word_translation(original_text, translated_words):
    """
    Create ruby annotations with translations above each word
    Example: <ruby><rt>translation</rt>original</ruby>
    """
    tokens = re.findall(r'(\w+|\s+|[^\w\s])', original_text)
    output = []
    word_index = 0
    
    for token in tokens:
        if not token.strip() or not token.isalpha():
            output.append(token)
            continue
            
        if word_index < len(translated_words):
            output.append(f'<ruby><rt>{token}</rt>{translated_words[word_index]}</ruby>')
            word_index += 1
        else:
            output.append(token)
    
    return ''.join(output)

def process_translation(text, language_code):
    """Process text to show word-by-word translations"""
    # Get full translation
    full_translation = translate_text(text, language_code)
    
    # Get word-by-word translation
    tokens = re.findall(r'(\w+|\s+|[^\w\s])', text)
    translated_words = translate_parallel(tokens, language_code)
    
    # Create annotated HTML
    annotated_html = add_word_translation(text, translated_words)
    
    return {
        'language': next(lang['name'] for lang in LANGUAGES if lang['code'] == language_code),
        'translation': full_translation,
        'transliteration': annotated_html,
        'needs_html': True
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    input_text = ""
    results = []
    
    if request.method == 'POST':
        input_text = request.form['text']
        
        if input_text.strip():
            with ThreadPoolExecutor() as executor:
                # Process all translations in parallel
                futures = [executor.submit(process_translation, input_text, lang['code']) 
                          for lang in LANGUAGES]
                results = [future.result() for future in futures]
    
    return render_template_string(HTML_TEMPLATE, input_text=input_text, results=results)

if __name__ == '__main__':
    app.run(debug=True, port=5002)