import requests
import time
from mp3_common import *

# Configuration
MARKDOWN_FILE = "/home/zaya/Documents/Gitrepos/Linktrees/Languages/WordList.md"
DOWNLOAD_DIR = "/home/zaya/Downloads"
TARGET_LANGUAGES = {'de': 200, 'fr': 200, 'es': 200}  # Example regular languages
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 1

def generate_audio_chunk(text, lang, output_path):
    """Generate audio chunk for regular languages"""
    for attempt in range(MAX_RETRIES):
        try:
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=gtx&q={quote(text)}"
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://translate.google.com/'
            }, timeout=10)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
        time.sleep(DELAY_BETWEEN_REQUESTS)
    return False

def process_language(lang, text_chunks, base_name):
    """Process a regular language"""
    output_path = f"{DOWNLOAD_DIR}/{base_name}_{lang}.mp3"
    temp_files = []
    
    for i, chunk in enumerate(text_chunks):
        temp_file = f"{DOWNLOAD_DIR}/temp_{lang}_{i}.mp3"
        if generate_audio_chunk(chunk, lang, temp_file):
            temp_files.append(temp_file)
    
    if temp_files:
        combine_audio_files(temp_files, output_path)
        print(f"✅ Created: {output_path}")

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(MARKDOWN_FILE))[0]
    content = get_clean_md_content(MARKDOWN_FILE)
    
    for lang, chunk_size in TARGET_LANGUAGES.items():
        chunks = split_text(content, chunk_size)
        process_language(lang, chunks, base_name)

if __name__ == "__main__":
    main()