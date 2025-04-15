import requests
import time
from pydub import AudioSegment
from pydub.silence import split_on_silence
from mp3_common import *

# CJK Configuration
CJK_PAUSE_CONFIG = {
    'zh-CN': {'between_words': 300, 'between_chars': 150},
    'ja': {'between_words': 400, 'between_chars': 200},
    'ko': {'between_words': 300, 'between_chars': 150}
}
TARGET_LANGUAGES = {'ja': 50, 'zh-CN': 50, 'ko': 50}
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2

def clean_cjk_text(text):
    """Special cleaning for CJK characters"""
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7a3]', '', text)
    return text.strip()

def split_cjk_text(text, char_limit):
    """Special splitter for CJK languages"""
    return [text[i:i+char_limit] for i in range(0, len(text), char_limit)]

def add_cjk_pauses(text, lang):
    """Insert pauses between CJK characters"""
    if lang not in CJK_PAUSE_CONFIG:
        return text
    
    if lang == 'ja':
        particles = ['を', 'に', 'で', 'が', 'は', 'の']
        for p in particles:
            text = text.replace(p, p + ' ')
    return ' '.join(text.split())

def generate_with_pauses(text, lang, output_path):
    """Generate audio with proper pauses"""
    processed_text = add_cjk_pauses(text, lang)
    encoded_text = quote(processed_text, safe='')
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=gtx&q={encoded_text}"
    
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://translate.google.com/'
    }, timeout=10)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        if lang in CJK_PAUSE_CONFIG:
            try:
                audio = AudioSegment.from_mp3(output_path)
                pause = AudioSegment.silent(duration=CJK_PAUSE_CONFIG[lang]['between_chars'])
                chunks = split_on_silence(audio, min_silence_len=50, silence_thresh=-40, keep_silence=100)
                combined = AudioSegment.empty()
                for chunk in chunks:
                    combined += chunk + pause
                combined.export(output_path, format="mp3")
            except Exception as e:
                print(f"Audio processing error: {str(e)}")
                return False
        return True
    return False

def process_cjk_language(lang, text_chunks, base_name):
    """Process CJK language with pauses"""
    output_path = f"{DOWNLOAD_DIR}/{base_name}_{lang}.mp3"
    temp_files = []
    
    for i, chunk in enumerate(text_chunks):
        temp_file = f"{DOWNLOAD_DIR}/temp_{lang}_{i}.mp3"
        if generate_with_pauses(chunk, lang, temp_file):
            temp_files.append(temp_file)
    
    if temp_files:
        combine_audio_files(temp_files, output_path)
        print(f"✅ Created: {output_path}")

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(MARKDOWN_FILE))[0]
    content = clean_cjk_text(get_clean_md_content(MARKDOWN_FILE))
    
    for lang, chunk_size in TARGET_LANGUAGES.items():
        chunks = split_cjk_text(content, chunk_size)
        process_cjk_language(lang, chunks, base_name)

if __name__ == "__main__":
    main()