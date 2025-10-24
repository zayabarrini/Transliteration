#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import tempfile


class EPUBTTSFilter:
    def __init__(self):
        # Chinese characters regex: [^\u4E00-\u9FFF\s,]
        self.chinese_regex = re.compile(r'[^\u4E00-\u9FFF\s,]')
        
        # Russian characters regex: [^\u0400-\u04FF\s,]
        self.russian_regex = re.compile(r'[^\u0400-\u04FF\s,]')
        
        # Combined regex to detect language
        self.chinese_detector = re.compile(r'[\u4E00-\u9FFF]')
        self.russian_detector = re.compile(r'[\u0400-\u04FF]')
    
    def extract_text_from_epub(self, epub_path):
        """Extract clean text from EPUB file"""
        try:
            import ebooklib
            from bs4 import BeautifulSoup
            from ebooklib import epub
            
            book = epub.read_epub(epub_path)
            text_content = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    clean_text = ' '.join(lines)
                    
                    if clean_text:
                        text_content.append(clean_text)
            
            return ' '.join(text_content)
        except Exception as e:
            print(f"Error reading EPUB: {e}")
            return ""
    
    def detect_language(self, text):
        """Detect if text is primarily Chinese or Russian"""
        chinese_chars = len(self.chinese_detector.findall(text))
        russian_chars = len(self.russian_detector.findall(text))
        total_non_space = len(re.findall(r'\S', text))
        
        if total_non_space == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_non_space
        russian_ratio = russian_chars / total_non_space
        
        if chinese_ratio > 0.3:
            return "chinese"
        elif russian_ratio > 0.3:
            return "russian"
        else:
            return "unknown"
    
    def filter_text(self, text, language):
        """Filter text based on language"""
        if language == "chinese":
            # Keep only Chinese characters, spaces, and commas
            filtered = self.chinese_regex.sub('', text)
        elif language == "russian":
            # Keep only Russian characters, spaces, and commas
            filtered = self.russian_regex.sub('', text)
        else:
            # If unknown, return original text
            return text
        
        # Clean up extra spaces
        filtered = re.sub(r'\s+', ' ', filtered).strip()
        return filtered
    
    def contains_chinese(self, text):
        """Check if text contains Chinese characters"""
        return bool(re.search(r'[\u4E00-\u9FFF]', text))

class EPUBTTSReader:
    def __init__(self):
        self.filter = EPUBTTSFilter()
        self.setup_tts()
    
    def setup_tts(self):
        """Setup TTS engine based on available options"""
        self.tts_engines = []
        
        # Check for available TTS engines with correct command names
        if self.check_engine('espeak-ng'):
            self.tts_engines.append('espeak-ng')
        elif self.check_engine('espeak'):  # Fallback to espeak if available
            self.tts_engines.append('espeak')
            
        if self.check_engine('festival'):
            self.tts_engines.append('festival')
        if self.check_engine('mimic'):
            self.tts_engines.append('mimic')
        if self.check_engine('mimic3'):
            self.tts_engines.append('mimic3')
        
        print(f"Available TTS engines: {self.tts_engines}")
    
    def check_engine(self, engine):
        """Check if TTS engine is available"""
        try:
            if engine in ['espeak', 'espeak-ng']:
                result = subprocess.run([engine, '--version'], capture_output=True, text=True)
                return result.returncode == 0
            elif engine == 'festival':
                result = subprocess.run(['festival', '--version'], capture_output=True, text=True)
                return result.returncode == 0
            elif engine in ['mimic', 'mimic3']:
                result = subprocess.run([engine, '--version'], capture_output=True, text=True)
                return result.returncode == 0
        except:
            return False
    
    def get_voice_for_language(self, text, engine):
        """Get appropriate voice for the detected language"""
        if self.filter.contains_chinese(text):
            if engine in ['espeak', 'espeak-ng']:
                return 'zh'  # Chinese voice
            else:
                return None  # Use default voice
        else:
            if engine in ['espeak', 'espeak-ng']:
                return 'ru'  # Russian voice
            else:
                return None  # Use default voice
    
    def speak_text(self, text, engine='espeak-ng'):
        """Speak text using selected TTS engine"""
        if not text.strip():
            print("No text to speak")
            return
        
        try:
            voice = self.get_voice_for_language(text, engine)
            
            if engine in ['espeak', 'espeak-ng']:
                cmd = [engine]
                if voice:
                    cmd.extend(['-v', voice])
                # Limit text length and remove problematic characters
                clean_text = text[:200].replace('"', '').replace("'", "")
                cmd.append(clean_text)
                subprocess.run(cmd)
                
            elif engine == 'festival':
                # Festival needs text in a file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(text[:500])  # Limit text length
                    temp_file = f.name
                
                try:
                    subprocess.run(['festival', '--tts', temp_file], check=True)
                finally:
                    os.unlink(temp_file)
                    
            elif engine in ['mimic', 'mimic3']:
                # Mimic can handle longer text
                clean_text = text[:1000].replace('"', '').replace("'", "")
                subprocess.run([engine, '-t', clean_text])
                
            else:
                print(f"Unsupported TTS engine: {engine}")
                
        except Exception as e:
            print(f"TTS error with {engine}: {e}")
    
    def read_epub_aloud(self, epub_path, engine=None):
        """Read filtered EPUB content aloud"""
        if engine is None:
            engine = self.tts_engines[0] if self.tts_engines else 'espeak-ng'
        
        if engine not in self.tts_engines:
            print(f"Engine {engine} not available. Available: {self.tts_engines}")
            return
        
        filtered_text, language = self.filter_epub(epub_path)
        
        if not filtered_text:
            print("No text to read")
            return
        
        print(f"Reading {language} text aloud using {engine}...")
        print("Press Ctrl+C to stop\n")
        
        # Read in smaller chunks to avoid issues
        sentences = re.split(r'[.!?。！？]', filtered_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        for i, sentence in enumerate(sentences):
            if i >= 10:  # Limit for testing
                print("\nStopping after 10 sentences for demo. Remove this limit for full reading.")
                break
                
            print(f"[{i+1}/{len(sentences)}] {sentence[:80]}...")
            self.speak_text(sentence, engine)
    
    def filter_epub(self, epub_path):
        """Filter EPUB and return text with language"""
        print(f"Processing: {epub_path}")
        
        # Extract text from EPUB
        raw_text = self.filter.extract_text_from_epub(epub_path)
        if not raw_text:
            print("No text extracted from EPUB")
            return None, None
        
        print(f"Extracted {len(raw_text)} characters")
        
        # Detect language
        language = self.filter.detect_language(raw_text)
        print(f"Detected language: {language}")
        
        # Filter text based on language
        filtered_text = self.filter.filter_text(raw_text, language)
        
        print(f"Filtered to {len(filtered_text)} characters")
        
        # Print preview
        preview = filtered_text[:500] + "..." if len(filtered_text) > 500 else filtered_text
        print(f"\nPreview:\n{preview}\n")
        
        return filtered_text, language

def main():
    if len(sys.argv) < 2:
        print("Usage: python epub_tts_reader.py <epub_file> [tts_engine]")
        print("Available engines: espeak-ng, festival, mimic")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    tts_engine = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if file exists
    if not os.path.exists(epub_file):
        print(f"File not found: {epub_file}")
        sys.exit(1)
    
    reader = EPUBTTSReader()
    reader.read_epub_aloud(epub_file, tts_engine)

if __name__ == "__main__":
    main()