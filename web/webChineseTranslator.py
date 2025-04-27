from flask import Flask, render_template, request
import jieba
from pypinyin import pinyin, Style
import fugashi
import pykakasi
from deep_translator import GoogleTranslator
import time

app = Flask(__name__)

# Initialize analyzers
kks = pykakasi.kakasi()

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
    words = jieba.lcut(text)
    pinyin_result = [' '.join([p[0] for p in pinyin(word, style=Style.TONE)]) for word in words]
    translations = []

    for word in words:
        try:
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            translation = translator.translate(word, src='zh-cn', dest='en')
            translations.append(translation)
        except Exception as e:
            print(f"Translation failed for '{word}': {str(e)}")
            translations.append(word)  # Fallback to original word if translation fails
    
    result = []
    for word, pinyin_word, translation in zip(words, pinyin_result, translations):
        result.append({
            'word': word,
            'transliteration': pinyin_word,
            'translation': translation
        })
    return result

def process_japanese(text):
    translator = get_translator()
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
            'translation': translation
        })
    return result

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        language = request.form['language']
        
        try:
            if language == 'chinese':
                result = process_chinese(text)
                lang_name = "Chinese"
            elif language == 'japanese':
                result = process_japanese(text)
                lang_name = "Japanese"
            else:
                result = []
                lang_name = ""
            
            return render_template('ChineseTranslator.html', 
                                result=result, 
                                original_text=text,
                                lang_name=lang_name)
        except Exception as e:
            return render_template('ChineseTranslator.html', 
                                 error=f"An error occurred: {str(e)}")
    
    return render_template('ChineseTranslator.html')

if __name__ == '__main__':
    app.run(debug=True, port=5003)