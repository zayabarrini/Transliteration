# app.py
from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
import spacy
from spacy import displacy
import re

app = Flask(__name__)

# Load spaCy Hindi model (you'll need to download it first: python -m spacy download hi)
try:
    nlp = spacy.load("hi_core_news_sm")
except OSError:
    # Fallback if model is not available
    nlp = None

def analyze_hindi_syntax(text):
    """Analyze Hindi text and return syntax elements with translations"""
    if not nlp:
        return []  # Return empty list if spaCy model is not available
    
    doc = nlp(text)
    results = []
    
    for token in doc:
        # Determine syntax function based on dependency tag
        if token.dep_ in ["nsubj", "nsubj:pass"]:
            syntax_func = "S"  # Subject
        elif token.dep_ in ["obj", "iobj", "dobj"]:
            syntax_func = "O"  # Object
        elif token.dep_ in ["root", "acl", "advcl"] and token.pos_ == "VERB":
            syntax_func = "V"  # Verb
        elif token.dep_ in ["obl", "advmod"]:
            syntax_func = "A"  # Adjunct
        elif token.dep_ in ["cc", "mark"]:
            syntax_func = "C"  # Conjunction
        elif token.dep_ in ["case", "adp"]:
            syntax_func = "P"  # Pre/Postposition
        else:
            syntax_func = "X"  # Other
        
        # Get translation for the token
        try:
            translation = GoogleTranslator(source='auto', target='en').translate(token.text)
        except:
            translation = token.text  # Fallback to original text if translation fails
        
        results.append({
            'token': token.text,
            'syntax_function': syntax_func,
            'translation': translation,
            'pos': token.pos_,
            'dep': token.dep_
        })
    
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    analysis_results = []
    input_text = ""
    
    if request.method == 'POST':
        input_text = request.form.get('text', '')
        if input_text.strip():
            analysis_results = analyze_hindi_syntax(input_text)
    
    return render_template('Hindi.html', 
                         results=analysis_results, 
                         input_text=input_text)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    text = data.get('text', '')
    
    if text.strip():
        analysis_results = analyze_hindi_syntax(text)
        return jsonify({
            'success': True,
            'results': analysis_results
        })
    else:
        return jsonify({
            'success': False,
            'error': 'No text provided'
        })

if __name__ == '__main__':
    app.run(debug=True, port=5005)