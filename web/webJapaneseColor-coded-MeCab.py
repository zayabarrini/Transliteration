import os
import re
from typing import Any, Dict, List

import MeCab
import pykakasi
from deep_translator import GoogleTranslator
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class JapaneseSentenceAnalyzer:
    def __init__(self):
        # Try different unidic paths
        unidic_paths = [
            '/usr/lib/x86_64-linux-gnu/mecab/dic/unidic',
            '/usr/local/lib/mecab/dic/unidic',
            '/opt/homebrew/lib/mecab/dic/unidic',  # For macOS
            os.path.expanduser('~/.local/lib/mecab/dic/unidic'),
        ]
        
        # Add the pip installed unidic path
        try:
            import unidic
            unidic_paths.insert(0, unidic.DICDIR)
        except ImportError:
            pass
        
        self.tagger = None
        for path in unidic_paths:
            try:
                if os.path.exists(path):
                    self.tagger = MeCab.Tagger(f'-d {path}')
                    print(f"Successfully loaded unidic from: {path}")
                    break
            except Exception as e:
                continue
        
        # Fallback to system dictionary
        if self.tagger is None:
            print("Warning: Could not load unidic, using default system dictionary")
            self.tagger = MeCab.Tagger()
        
        # Initialize modern pykakasi
        self.kakasi = pykakasi.kakasi()
        
        # Initialize translator
        self.translator = GoogleTranslator(source='ja', target='en')
    
    def get_part_of_speech(self, pos_info: str) -> str:
        """Extract part of speech from MeCab output"""
        if not pos_info:
            return "UNKNOWN"
        
        pos_info = pos_info.split(',')[0]
        
        pos_mapping = {
            '名詞': 'NOUN',
            '代名詞': 'PRONOUN', 
            '動詞': 'VERB',
            '形容詞': 'ADJECTIVE_I',
            '形状詞': 'ADJECTIVE_NA',
            '副詞': 'ADVERB',
            '連体詞': 'PRENOUN_ADJECTIVE',
            '接続詞': 'CONJUNCTION',
            '感動詞': 'INTERJECTION',
            '助詞': 'PARTICLE',
            '助動詞': 'AUXILIARY_VERB',
            '接頭辞': 'PREFIX',
            '接尾辞': 'SUFFIX',
            '記号': 'SYMBOL',
            '補助記号': 'PUNCTUATION'
        }
        
        return pos_mapping.get(pos_info, 'UNKNOWN')
    
    def get_particle_type(self, word: str, pos: str, sub_pos: str) -> str:
        """Determine specific particle type"""
        if pos != 'PARTICLE':
            return "None"
        
        particle_mapping = {
            'は': 'CASE_WA',
            'が': 'CASE_GA', 
            'を': 'CASE_O',
            'に': 'CASE_NI',
            'で': 'CASE_DE',
            'へ': 'CASE_E',
            'と': 'CASE_TO',
            'から': 'CASE_KARA',
            'より': 'CASE_YORI',
            'まで': 'CASE_MADE',
            'の': 'CASE_NO',
            'て': 'CONNECTIVE_TE',
            'で': 'CONNECTIVE_DE',
            'ば': 'CONNECTIVE_BA',
            'か': 'FINAL_KA',
            'ね': 'FINAL_NE',
            'よ': 'FINAL_YO',
            'わ': 'FINAL_WA',
            'も': 'CASE_MO',
            'や': 'CASE_YA',
            'とか': 'CASE_TOKA',
            'など': 'CASE_NADO'
        }
        
        return particle_mapping.get(word, 'PARTICLE_GENERIC')
    
    def get_verb_form(self, word: str, pos: str, conjugation: str) -> str:
        """Determine verb conjugation form"""
        if pos not in ['VERB', 'AUXILIARY_VERB']:
            return "None"
        
        # Simple form detection based on endings
        if word.endswith('ます'):
            return "MASU_PRESENT"
        elif word.endswith('ました'):
            return "MASU_PAST" 
        elif word.endswith('ません'):
            return "MASU_NEGATIVE"
        elif word.endswith('て'):
            return "TE_FORM"
        elif word.endswith('た') or word.endswith('だ'):
            return "TA_FORM"
        elif word.endswith('ない'):
            return "NAI_FORM"
        elif word.endswith('ば'):
            return "CONDITIONAL_BA"
        elif word.endswith('よう'):
            return "VOLITIONAL"
        elif word.endswith('られる') or word.endswith('える'):
            return "POTENTIAL"
        elif word.endswith('させる'):
            return "CAUSATIVE"
        elif word.endswith('ろ') or word.endswith('よ'):
            return "IMPERATIVE"
        
        return "DICTIONARY"
    
    def get_honorific_level(self, word: str, pos: str) -> str:
        """Determine honorific/politeness level"""
        if pos == 'VERB':
            if 'ます' in word or 'です' in word:
                return "POLITE"
            elif any(honorific in word for honorific in ['お', 'ご', 'いたし', '申し']):
                return "HUMBLE"
            elif any(respectful in word for respectful in ['れる', 'られる', 'なさる']):
                return "RESPECTFUL"
        
        return "PLAIN"
    
    def get_semantic_category(self, word: str, pos: str) -> str:
        """Determine semantic category"""
        if pos == 'NOUN':
            # Simple semantic categorization
            time_words = ['時', '時間', '日', '月', '年', '分', '秒', '朝', '晩', '夜']
            location_words = ['場所', '所', '地点', '位置', '家', '學校', '店', '駅', '空港']
            person_words = ['人', '先生', '學生', '私', 'あなた', '彼', '彼女', '子供', '大人']
            
            if any(time in word for time in time_words):
                return "TIME"
            elif any(loc in word for loc in location_words):
                return "LOCATION" 
            elif any(person in word for person in person_words):
                return "PERSON"
            else:
                return "OBJECT"
        
        elif pos == 'VERB':
            return "ACTION"
        elif pos in ['ADJECTIVE_I', 'ADJECTIVE_NA']:
            return "DESCRIPTION"
        elif pos == 'ADVERB':
            return "DESCRIPTION"
        elif pos == 'PARTICLE':
            return "GRAMMAR"
        
        return "GENERAL"
    
    def get_syntax_role(self, word: str, pos: str, particle_type: str, index: int, sentence_length: int) -> str:
        """Determine syntactic role in sentence"""
        if particle_type != "None":
            if particle_type in ['CASE_WA']:
                return "TOPIC"
            elif particle_type in ['CASE_GA']:
                return "SUBJECT"
            elif particle_type in ['CASE_O']:
                return "DIRECT_OBJECT"
            elif particle_type in ['CASE_NI']:
                return "INDIRECT_OBJECT"
            elif particle_type in ['CASE_DE']:
                return "LOCATION"
            elif particle_type in ['CASE_E']:
                return "DIRECTION"
            elif particle_type in ['CASE_KARA']:
                return "SOURCE"
            elif particle_type in ['CASE_MADE']:
                return "DESTINATION"
            elif particle_type in ['CASE_NO']:
                return "POSSESSOR"
            elif particle_type in ['FINAL_KA', 'FINAL_NE', 'FINAL_YO']:
                return "SENTENCE_ENDER"
        
        if pos == 'VERB' and index >= sentence_length - 3:  # Usually verb is near end
            return "VERB"
        elif pos in ['ADJECTIVE_I', 'ADJECTIVE_NA'] and index >= sentence_length - 3:
            return "PREDICATE"
        
        return "MODIFIER"
    
    def is_punctuation(self, word: str) -> bool:
        """Check if word is punctuation"""
        punctuation_chars = ['。', '、', '！', '？', '・', '「', '」', '『', '』', '（', '）', '『', '』', '【', '】', '…', '‥', '〃', '´', '～']
        return word in punctuation_chars
    
    def get_word_translation(self, word: str, pos: str, target_language: str = 'en') -> str:
        """Get translation for individual words using Google Translate"""
        # Skip translation for particles, punctuation, and some grammatical elements
        if pos in ['PARTICLE', 'PUNCTUATION', 'SYMBOL', 'AUXILIARY_VERB']:
            return ""
        
        # Enhanced translation dictionary for common words (fallback)
        translation_map = {
            # Pronouns
            '私': 'I', 'わたし': 'I', '僕': 'I', '俺': 'I', 'わたくし': 'I',
            'あなた': 'you', '君': 'you', 'お前': 'you', '貴方': 'you',
            '彼': 'he', '彼女': 'she',
            'これ': 'this', 'それ': 'that', 'あれ': 'that (over there)',
            'ここ': 'here', 'そこ': 'there', 'あそこ': 'over there',
            
            # Common nouns
            '人': 'person', '先生': 'teacher', '學生': 'student',
            '本': 'book', '水': 'water', '食べ物': 'food', '學校': 'school',
            '家': 'house', '車': 'car', '猫': 'cat', '犬': 'dog', '魚': 'fish',
            '仕事': 'work', '會社': 'company', '時間': 'time', '友達': 'friend',
            '子供': 'child', '大人': 'adult', '男': 'man', '女': 'woman',
            
            # Verbs
            '行く': 'go', '來る': 'come', '見る': 'see', '食べる': 'eat', '飲む': 'drink',
            '読む': 'read', '書く': 'write', '話す': 'speak', '聞く': 'hear',
            'する': 'do', 'なる': 'become', 'ある': 'exist (inanimate)', 'いる': 'exist (animate)',
            '買う': 'buy', '売る': 'sell', '作る': 'make', '使う': 'use',
            'わかる': 'understand', '知る': 'know', '思う': 'think',
            
            # Adjectives
            '大きい': 'big', '小さい': 'small', '良い': 'good', '悪い': 'bad',
            '美味しい': 'delicious', '高い': 'high/expensive', '安い': 'cheap',
            '暑い': 'hot', '寒い': 'cold', '新しい': 'new', '古い': 'old',
            '難しい': 'difficult', '易しい': 'easy', '嬉しい': 'happy', '悲しい': 'sad',
            
            # Adverbs and others
            'とても': 'very', '少し': 'a little', 'たくさん': 'many', 'すぐに': 'immediately',
            'ゆっくり': 'slowly', '早く': 'quickly',
            
            # Question words
            '何': 'what', '誰': 'who', 'どこ': 'where', 'いつ': 'when', 'なぜ': 'why', 'どう': 'how',
            
            # Numbers
            '一': 'one', '二': 'two', '三': 'three', '四': 'four', '五': 'five',
            '六': 'six', '七': 'seven', '八': 'eight', '九': 'nine', '十': 'ten',
        }
        
        # First try the translation map
        if word in translation_map:
            return translation_map[word]
        
        # Fall back to Google Translate for words not in our dictionary
        try:
            if target_language != 'en':
                self.translator.target = target_language
            translated = self.translator.translate(word)
            return translated if translated != word else ""
        except Exception as e:
            print(f"Word translation error for '{word}': {e}")
            return ""
    
    def get_transliteration(self, word: str) -> str:
        """Get romaji transliteration using modern pykakasi"""
        if self.is_punctuation(word):
            return ""
        try:
            result = self.kakasi.convert(word)
            return result[0]['hepburn'] if result else word
        except Exception as e:
            print(f"Transliteration error for '{word}': {e}")
            return word
    
    def translate_sentence(self, sentence: str, target_lang: str = 'en') -> str:
        """Translate entire sentence using Google Translate"""
        try:
            if target_lang != 'en':
                self.translator.target = target_lang
            return self.translator.translate(sentence)
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Translation not available: {sentence}"
    
    def analyze_sentence(self, sentence: str, target_language: str = 'en') -> List[Dict[str, Any]]:
        """Analyze a Japanese sentence and return detailed word information"""
        result = []
        
        # Parse with MeCab
        parsed = self.tagger.parse(sentence)
        lines = parsed.split('\n')
        
        words = []
        for line in lines:
            if line == 'EOS' or not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                word = parts[0]
                features = parts[1].split(',')
                words.append((word, features))
        
        for i, (word, features) in enumerate(words):
            # Skip punctuation entirely
            if self.is_punctuation(word):
                continue
                
            # Skip if it's empty
            if not word.strip():
                continue
                
            # Get basic POS
            pos = self.get_part_of_speech(features[0] if features else '')
            
            # Skip if it's punctuation POS
            if pos == 'PUNCTUATION':
                continue
            
            # Get particle type
            particle_type = self.get_particle_type(word, pos, features[1] if len(features) > 1 else '')
            
            # Get verb form
            verb_form = self.get_verb_form(word, pos, features[-1] if features else '')
            
            # Get honorific level
            honorific_level = self.get_honorific_level(word, pos)
            
            # Get semantic category
            semantic_category = self.get_semantic_category(word, pos)
            
            # Get syntax role
            syntax_role = self.get_syntax_role(word, pos, particle_type, i, len(words))
            
            # Get transliteration using pykakasi
            romaji_word = self.get_transliteration(word)
            
            # Get translation (only for relevant word types)
            translation = self.get_word_translation(word, pos, target_language)
            
            result.append({
                "word": word,
                "transliteration": romaji_word,
                "translation": translation,
                "syntax_role": syntax_role,
                "part_of_speech": pos,
                "particle_type": particle_type,
                "verb_form": verb_form,
                "honorific_level": honorific_level,
                "is_punctuation": False,  # We're filtering these out now
                "semantic_category": semantic_category
            })
        
        return result

# Initialize analyzer
analyzer = JapaneseSentenceAnalyzer()

# Target languages without direction property
TARGET_LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "it", "name": "Italian"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ru", "name": "Russian"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "zh-CN", "name": "Chinese (Simplified)"},
    {"code": "ar", "name": "Arabic"},
    {"code": "he", "name": "Hebrew"},
    {"code": "fa", "name": "Persian"},
    {"code": "ur", "name": "Urdu"},
    {"code": "hi", "name": "Hindi"},
    {"code": "tr", "name": "Turkish"},
    {"code": "nl", "name": "Dutch"},
    {"code": "sv", "name": "Swedish"},
    {"code": "pl", "name": "Polish"},
    {"code": "vi", "name": "Vietnamese"},
    {"code": "th", "name": "Thai"},
    {"code": "id", "name": "Indonesian"}
]

@app.route('/')
def index():
    return render_template('color-coded-japanese-MeCab.html', 
                         target_languages=TARGET_LANGUAGES,
                         selected_target_lang='en')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    sentences = data.get('sentences', [])
    target_language = data.get('target_language', 'en')
    
    results = []
    for sentence in sentences:
        if sentence.strip():
            analysis = analyzer.analyze_sentence(sentence.strip(), target_language)
            # Get proper sentence translation
            translated_sentence = analyzer.translate_sentence(sentence.strip(), target_language)
            
            results.append({
                'original': sentence,
                'translated': translated_sentence,
                'analysis': analysis
            })
    
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True, port=5010, host='0.0.0.0')