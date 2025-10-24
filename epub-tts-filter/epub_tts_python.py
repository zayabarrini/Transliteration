#!/usr/bin/env python3
import pyttsx3
from epub_tts_reader import EPUBTTSFilter


class PythonTTSReader:
    def __init__(self):
        self.filter = EPUBTTSFilter()
        self.engine = pyttsx3.init()
        
        # Set Russian voice if available
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'russian' in voice.name.lower() or 'ru' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
    
    def read_epub_aloud(self, epub_path):
        filtered_text, language = self.filter_epub(epub_path)
        
        if not filtered_text:
            return
        
        print(f"Reading {language} text using pyttsx3...")
        
        # Read in chunks
        sentences = filtered_text.split('.')
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                print(f"[{i+1}/{len(sentences)}] {sentence[:80]}...")
                self.engine.say(sentence.strip())
                self.engine.runAndWait()
    
    def filter_epub(self, epub_path):
        return self.filter.filter_epub(epub_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python epub_tts_python.py <epub_file>")
        sys.exit(1)
    
    reader = PythonTTSReader()
    reader.read_epub_aloud(sys.argv[1])