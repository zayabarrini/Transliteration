# modified_japanese.py
import re
import pykakasi

class JapaneseTransliterator:
    def __init__(self):
        self.kks = pykakasi.kakasi()
        # Define Japanese punctuation
        self.punctuation = {' ', '。', '、', '！', '？', '「', '」', '『', '』', '（', '）', '・'}
    
    def convert(self, text):
        if not text:
            return [{"orig": "", "hepburn": ""}]
        
        result = []
        # First get the full conversion
        full_conversion = self.kks.convert(text)
        
        for item in full_conversion:
            # Clean the romaji (remove pitch numbers)
            clean_romaji = re.sub(r'\d', '', item['hepburn']).strip()
            result.append({
                "orig": item['orig'],
                "hepburn": clean_romaji if clean_romaji else item['orig']
            })
        
        return result