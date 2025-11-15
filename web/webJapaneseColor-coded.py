import re
import time

import pykakasi
from deep_translator import GoogleTranslator
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Initialize pykakasi for Japanese romanization
kks = pykakasi.kakasi()

def get_translator():
    return GoogleTranslator(source='ja', target='en')

def is_punctuation(char):
    return char in '、。！？「」『』・'

def group_into_sentences(word_list):
    sentences = []
    current_sentence = []
    
    for word in word_list:
        current_sentence.append(word)
        if word['word'] in '。！？' or word['word'] in ['。', '！', '？']:
            if current_sentence:
                sentences.append(current_sentence)
            current_sentence = []
    
    if current_sentence:
        sentences.append(current_sentence)
    
    return sentences

# Comprehensive Japanese analysis with all markers
def analyze_japanese_word(word, romaji_word, translation):
    """Analyze a Japanese word and assign comprehensive markers"""
    
    # Default analysis
    analysis = {
        "word": word,
        "transliteration": romaji_word,
        "translation": translation,
        "syntax_role": "UNKNOWN",
        "part_of_speech": "UNKNOWN",
        "particle_type": "NONE",
        "verb_form": "NONE",
        "honorific_level": "NEUTRAL",
        "is_punctuation": is_punctuation(word),
        "semantic_category": "GENERAL"
    }
    
    # Skip punctuation analysis
    if is_punctuation(word):
        analysis.update({
            "syntax_role": "PUNCTUATION",
            "part_of_speech": "PUNCTUATION",
            "semantic_category": "PUNCTUATION"
        })
        return analysis
    
    # Particle detection and classification
    particles = {
        'は': {'syntax': 'TOPIC', 'particle': 'CASE_WA'},
        'が': {'syntax': 'SUBJECT', 'particle': 'CASE_GA'},
        'を': {'syntax': 'DIRECT_OBJECT', 'particle': 'CASE_O'},
        'に': {'syntax': 'INDIRECT_OBJECT', 'particle': 'CASE_NI'},
        'で': {'syntax': 'LOCATION', 'particle': 'CASE_DE'},
        'へ': {'syntax': 'DIRECTION', 'particle': 'CASE_E'},
        'と': {'syntax': 'CONJUNCTION', 'particle': 'CASE_TO'},
        'から': {'syntax': 'SOURCE', 'particle': 'CASE_KARA'},
        'まで': {'syntax': 'LIMIT', 'particle': 'CASE_MADE'},
        'より': {'syntax': 'COMPARISON', 'particle': 'CASE_YORI'},
        'の': {'syntax': 'POSSESSOR', 'particle': 'CASE_NO'},
        'て': {'syntax': 'CONJUNCTION', 'particle': 'CONNECTIVE_TE'},
        'で': {'syntax': 'CONJUNCTION', 'particle': 'CONNECTIVE_DE'},
        'ば': {'syntax': 'CONJUNCTION', 'particle': 'CONNECTIVE_BA'},
        'か': {'syntax': 'SENTENCE_ENDER', 'particle': 'FINAL_KA'},
        'ね': {'syntax': 'SENTENCE_ENDER', 'particle': 'FINAL_NE'},
        'よ': {'syntax': 'SENTENCE_ENDER', 'particle': 'FINAL_YO'},
        'わ': {'syntax': 'SENTENCE_ENDER', 'particle': 'FINAL_WA'}
    }
    
    if word in particles:
        analysis.update({
            'syntax_role': particles[word]['syntax'],
            'part_of_speech': 'PARTICLE',
            'particle_type': particles[word]['particle']
        })
        return analysis
    
    # Verb form detection
    verb_patterns = [
        (r'.*ます$', 'MASU_PRESENT', 'POLITE'),
        (r'.*ました$', 'MASU_PAST', 'POLITE'),
        (r'.*ません$', 'MASU_NEGATIVE', 'POLITE'),
        (r'.*て$', 'TE_FORM', 'PLAIN'),
        (r'.*た$', 'TA_FORM', 'PLAIN'),
        (r'.*ない$', 'NAI_FORM', 'PLAIN'),
        (r'.*よう$', 'VOLITIONAL', 'PLAIN'),
        (r'.*ろ$', 'IMPERATIVE', 'PLAIN'),
        (r'.*れ$', 'IMPERATIVE', 'PLAIN'),
        (r'.*ば$', 'CONDITIONAL_BA', 'PLAIN'),
        (r'.*たら$', 'CONDITIONAL_TARA', 'PLAIN'),
        (r'.*られる$', 'POTENTIAL', 'PLAIN'),
        (r'.*れる$', 'POTENTIAL', 'PLAIN'),
        (r'.*される$', 'CAUSATIVE', 'PLAIN'),
        (r'.*させる$', 'CAUSATIVE', 'PLAIN')
    ]
    
    for pattern, form, honorific in verb_patterns:
        if re.match(pattern, word):
            analysis.update({
                'part_of_speech': 'VERB',
                'syntax_role': 'VERB',
                'verb_form': form,
                'honorific_level': honorific,
                'semantic_category': 'ACTION'
            })
            return analysis
    
    # Adjective detection
    if word.endswith('い') and len(word) > 1:
        analysis.update({
            'part_of_speech': 'ADJECTIVE_I',
            'syntax_role': 'DESCRIPTION',
            'semantic_category': 'DESCRIPTION'
        })
        return analysis
    
    if word.endswith('な') and len(word) > 1:
        analysis.update({
            'part_of_speech': 'ADJECTIVE_NA', 
            'syntax_role': 'DESCRIPTION',
            'semantic_category': 'DESCRIPTION'
        })
        return analysis
    
    # Noun detection (default for unclassified words)
    analysis.update({
        'part_of_speech': 'NOUN',
        'syntax_role': 'SUBJECT',  # Default assumption
        'semantic_category': 'OBJECT'
    })
    
    # Time words
    time_words = ['今日', '昨日', '明日', '時', '分', '秒', '月', '火', '水', '木', '金', '土', '日']
    if word in time_words:
        analysis['semantic_category'] = 'TIME'
    
    # Location words  
    location_words = ['ここ', 'そこ', 'あそこ', 'どこ', '中', '上', '下', '前', '後']
    if word in location_words:
        analysis['semantic_category'] = 'LOCATION'
    
    # Person words
    person_words = ['私', 'あなた', '彼', '彼女', '人', '先生', '学生']
    if word in person_words:
        analysis['semantic_category'] = 'PERSON'
    
    # Question words
    question_words = ['何', '誰', 'どこ', 'いつ', 'なぜ', 'どうして', 'どの']
    if word in question_words:
        analysis['semantic_category'] = 'QUESTION'
        analysis['syntax_role'] = 'QUESTION'
    
    return analysis

def process_japanese(text):
    translator = get_translator()

    # Get full text translation
    try:
        full_translation = translator.translate(text)
    except Exception as e:
        print(f"Full translation failed: {str(e)}")
        full_translation = "Translation unavailable"

    # Use pykakasi for segmentation and transliteration
    try:
        analyzed = kks.convert(text)
        
        words = []
        romaji = []
        
        for item in analyzed:
            original = item.get("orig", "")
            hepburn_romaji = item.get("hepburn", "")
            
            words.append(original)
            romaji.append(hepburn_romaji)
            
    except Exception as e:
        print(f"pykakasi processing failed: {str(e)}")
        # Fallback: simple character splitting
        words = list(text)
        romaji = [""] * len(words)

    # Get word translations and comprehensive analysis
    analyzed_words = []
    for word, romaji_word in zip(words, romaji):
        if is_punctuation(word) or word.isspace():
            analyzed_words.append(analyze_japanese_word(word, romaji_word, ""))
            continue
            
        try:
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            translation = translator.translate(word)
            analysis = analyze_japanese_word(word, romaji_word, translation)
            analyzed_words.append(analysis)
        except Exception as e:
            print(f"Translation failed for '{word}': {str(e)}")
            analysis = analyze_japanese_word(word, romaji_word, word)
            analyzed_words.append(analysis)

    # Group into sentences
    sentences = group_into_sentences(analyzed_words)
    
    return sentences, full_translation

@app.route('/')
def index():
    return render_template('color-coded-japanese.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'})
    
    try:
        sentences, full_translation = process_japanese(text)
        
        return jsonify({
            'success': True,
            'sentences': sentences,
            'full_translation': full_translation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5008)