from flask import Flask, render_template, request
import jieba
import jieba.posseg as pseg
from pypinyin import pinyin, Style
import fugashi
import pykakasi
from deep_translator import GoogleTranslator
import time

app = Flask(__name__)

# Initialize analyzers
kks = pykakasi.kakasi()

# Complete exclusion set for punctuation
EXCLUDE_CHARS = {
    ' ', '.', ',', '!', '?', '。', '，', '！', '？', '、',
    '「', '」', '『', '』', '（', '）', '《', '》', '“', '”',
    '‘', '’', '…', '—', '：', ':', '；', ';', '～', '°', 'º'
}

def is_punctuation(word):
    """Check if a word is punctuation"""
    return word in EXCLUDE_CHARS

def analyze_chinese_syntax(text):
    """Improved POS-based syntax analysis for Chinese"""
    words = list(pseg.cut(text))
    syntax_data = []
    
    for i, (word, pos) in enumerate(words):
        # Skip punctuation in syntax analysis
        if is_punctuation(word):
            syntax_data.append((word, 'PUNCT', pos))
            continue
            
        # Enhanced heuristic rules based on POS tags
        if pos.startswith('v'):  # Verbs (v, vd, vn, etc.)
            category = 'V'
        elif pos in ['r', 'nh', 'nr'] and i == 0:  # First person/name often subject
            category = 'S'
        elif pos in ['r', 'nh', 'nr'] and i > 0 and syntax_data:  
            # Check previous word to determine if this is subject or object
            prev_syntax = syntax_data[-1][1] if syntax_data else ''
            if prev_syntax in ['V', 'P']:  # After verb or preposition, likely object
                category = 'O'
            else:
                category = 'S'
        elif pos.startswith('n') and i > 0:  # Nouns after first position
            prev_syntax = syntax_data[-1][1] if syntax_data else ''
            if prev_syntax == 'V':  # Object after verb
                category = 'O'
            elif prev_syntax in ['P', 'C']:  # After preposition/conjunction
                category = 'O'
            else:
                category = 'S' if i == 0 else 'O'
        elif pos.startswith('n') and i == 0:  # First noun is likely subject
            category = 'S'
        elif pos in ['d', 'a', 'b']:  # Adverbs, adjectives, other modifiers
            category = 'A'
        elif pos in ['c', 'p', 'cc']:  # Conjunctions, prepositions
            category = 'C' if pos in ['c', 'cc'] else 'P'
        elif pos in ['u', 'y', 'e']:  # Auxiliary, modal particles
            category = 'P'
        elif pos in ['m', 'q']:  # Numbers, quantifiers
            category = 'A'  # Treat as adjunct/modifier
        elif pos in ['f', 's']:  # Direction, place
            category = 'A'
        else:
            category = 'X'  # Other
            
        syntax_data.append((word, category, pos))
    
    return syntax_data

def get_translator():
    # Initialize translator with retry logic
    max_retries = 3
    for i in range(max_retries):
        try:
            translator = GoogleTranslator()
            # Test the translator
            translator.translate("test", src='en', dest='es')
            return translator
        except:
            if i < max_retries - 1:
                time.sleep(1)  # wait before retrying
                continue
            raise Exception("Failed to initialize translator after multiple attempts")

def process_chinese(text):
    translator = get_translator()
    
    # Get full text translation
    try:
        full_translation = translator.translate(text, src='zh-cn', dest='en')
    except Exception as e:
        print(f"Full translation failed: {str(e)}")
        full_translation = "Translation unavailable"
    
    # Use POS-based syntax analysis
    syntax_analysis = analyze_chinese_syntax(text)
    words = [item[0] for item in syntax_analysis]
    syntax_categories = [item[1] for item in syntax_analysis]
    pos_tags = [item[2] for item in syntax_analysis]
    
    pinyin_result = []
    for word in words:
        if is_punctuation(word):
            pinyin_result.append('')  # No pinyin for punctuation
        else:
            pinyin_result.append(' '.join([p[0] for p in pinyin(word, style=Style.TONE)]))
    
    translations = []

    for word in words:
        if is_punctuation(word):
            translations.append('')  # No translation for punctuation
        else:
            try:
                # Add delay to avoid rate limiting
                time.sleep(0.5)
                translation = translator.translate(word, src='zh-cn', dest='en')
                translations.append(translation)
            except Exception as e:
                print(f"Translation failed for '{word}': {str(e)}")
                translations.append(word)  # Fallback to original word if translation fails
    
    result = []
    for word, pinyin_word, translation, syntax, pos in zip(words, pinyin_result, translations, syntax_categories, pos_tags):
        result.append({
            'word': word,
            'transliteration': pinyin_word,
            'translation': translation,
            'syntax': syntax,
            'pos': pos,
            'is_punctuation': is_punctuation(word)
        })
    
    return result, full_translation

def process_japanese(text):
    translator = get_translator()
    
    # Get full text translation
    try:
        full_translation = translator.translate(text, src='ja', dest='en')
    except Exception as e:
        print(f"Full translation failed: {str(e)}")
        full_translation = "Translation unavailable"
        
    tagger = fugashi.Tagger()
    words = [word.surface for word in tagger(text)]
    romaji = [kks.convert(word)[0]['hepburn'] for word in words]
    translations = []
    
    for word in words:
        try:
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            translation = translator.translate(word, src='ja', dest='en')
            translations.append(translation)
        except Exception as e:
            print(f"Translation failed for '{word}': {str(e)}")
            translations.append(word)  # Fallback to original word if translation fails
    
    result = []
    for word, romaji_word, translation in zip(words, romaji, translations):
        result.append({
            'word': word,
            'transliteration': romaji_word,
            'translation': translation,
            'syntax': 'X',  # Default for Japanese for now
            'pos': 'Unknown',
            'is_punctuation': is_punctuation(word)
        })
    
    return result, full_translation

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        language = request.form['language']
        
        try:
            if language == 'chinese':
                result, full_translation = process_chinese(text)
                lang_name = "Chinese"
            elif language == 'japanese':
                result, full_translation = process_japanese(text)
                lang_name = "Japanese"
            else:
                result = []
                full_translation = ""
                lang_name = ""
            
            return render_template('color-coded-chinese.html', 
                                result=result, 
                                original_text=text,
                                lang_name=lang_name,
                                full_translation=full_translation)
        except Exception as e:
            return render_template('color-coded-chinese.html', 
                                 error=f"An error occurred: {str(e)}")
    
    return render_template('color-coded-chinese.html')

if __name__ == '__main__':
    app.run(debug=True, port=5007)