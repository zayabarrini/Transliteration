import sqlite3
import hashlib
import json
from datetime import datetime, timedelta

class TranslationCache:
    def __init__(self, db_path="translation_cache.db", max_size=100000):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY,
                text_hash TEXT UNIQUE,
                original_text TEXT,
                translated_text TEXT,
                target_lang TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_hash ON translations(text_hash)')
        conn.commit()
        conn.close()
    
    def _get_hash(self, text, lang):
        return hashlib.md5(f"{text}_{lang}".encode('utf-8')).hexdigest()
    
    def get(self, text, lang):
        text_hash = self._get_hash(text, lang)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'SELECT translated_text FROM translations WHERE text_hash = ?',
            (text_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set(self, text, lang, translated):
        text_hash = self._get_hash(text, lang)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'INSERT OR REPLACE INTO translations (text_hash, original_text, translated_text, target_lang) VALUES (?, ?, ?, ?)',
            (text_hash, text, translated, lang)
        )
        conn.commit()
        conn.close()

# Global cache instance
_translation_cache = TranslationCache()

def translate_text_optimized(text, target_language):
    """Optimized translation with persistent caching"""
    if not text.strip():
        return text
    
    clean_text = ' '.join(text.strip().split())
    if len(clean_text) < 3 or clean_text.isdigit():
        return clean_text
    
    # Check cache first
    cached = _translation_cache.get(clean_text, target_language)
    if cached:
        return cached
    
    # Batch translation for better performance
    results = batch_translate_texts_optimized([clean_text], target_language)
    translated = results[0] if results else clean_text
    
    # Cache the result
    _translation_cache.set(clean_text, target_language, translated)
    return translated