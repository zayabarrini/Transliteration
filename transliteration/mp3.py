import os
import requests
import time
import re
from urllib.parse import quote
from pathlib import Path
from deep_translator import GoogleTranslator
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Configuration for pauses (in milliseconds)
CJK_PAUSE_CONFIG = {
    'zh-CN': {'between_words': 300, 'between_chars': 150},
    'ja': {'between_words': 400, 'between_chars': 200},
    'ko': {'between_words': 300, 'between_chars': 150}
}

# Main Configuration
MARKDOWN_FILE = "/home/zaya/Documents/Gitrepos/Linktrees/Languages/WordList.md"
DOWNLOAD_DIR = "/home/zaya/Downloads"
TARGET_LANGUAGES = {
    'cjk': {'ja': 50},  # Testing with Japanese first
    'others': {}  # Add other languages here if needed
}
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2  # More conservative delay

def split_text(text, chunk_size):
    """Split text into chunks respecting word boundaries"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
def get_clean_md_content(md_file_path):
    """Read and clean markdown content"""
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove markdown headers and clean up
    content = re.sub(r'^#.*$', '', content, flags=re.MULTILINE)
    content = ' '.join(content.split())
    return content

def clean_cjk_text(text):
    """Special cleaning for CJK characters"""
    # Remove all non-CJK punctuation and symbols
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7a3]', '', text)
    return text.strip()

def split_cjk_text(text, char_limit):
    """Special splitter for Chinese/Japanese/Korean"""
    chunks = []
    current_chunk = []
    current_length = 0
    
    for char in text:
        char_length = len(char.encode('utf-8'))
        if current_length + char_length > char_limit:
            chunks.append(''.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(char)
        current_length += char_length
    
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    return chunks

def add_cjk_pauses(text, lang):
    """Insert pauses between CJK characters/words"""
    if lang not in CJK_PAUSE_CONFIG:
        return text
    
    config = CJK_PAUSE_CONFIG[lang]
    
    # For Chinese - pause between characters
    if lang == 'zh-CN':
        return ' '.join(text)  # Adds natural pauses
    
    # For Japanese - special handling for kanji/kana
    elif lang == 'ja':
        # Insert pauses after particles (を, に, で, etc.)
        particles = ['を', 'に', 'で', 'が', 'は', 'の']
        for p in particles:
            text = text.replace(p, p + ' ')
        return ' '.join(text.split())  # Normalize spaces
    
    # For Korean - pause between words
    elif lang == 'ko':
        return ' '.join(text.split())  # Adds word breaks
    
    return text

def generate_with_pauses(text, lang, output_path):
    """Generate audio with proper pauses for CJK"""
    # Add pauses to the text
    processed_text = add_cjk_pauses(text, lang)
    
    # Generate audio
    encoded_text = quote(processed_text, safe='')
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=gtx&q={encoded_text}"
    
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://translate.google.com/'
    }, timeout=10)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Add additional pauses if needed
        if lang in CJK_PAUSE_CONFIG:
            try:
                audio = AudioSegment.from_mp3(output_path)
                
                # Insert additional silent pauses
                pause_duration = CJK_PAUSE_CONFIG[lang]['between_chars']
                silent_pause = AudioSegment.silent(duration=pause_duration)
                
                # Split audio on natural pauses
                chunks = split_on_silence(
                    audio, 
                    min_silence_len=50, 
                    silence_thresh=-40,
                    keep_silence=100
                )
                
                # Recombine with additional pauses
                combined = AudioSegment.empty()
                for chunk in chunks:
                    combined += chunk + silent_pause
                
                # Save final audio
                combined.export(output_path, format="mp3")
            except Exception as e:
                print(f"Audio processing error: {str(e)}")
                return False
        
        return True
    
    print(f"HTTP {response.status_code} | URL Length: {len(url)}")
    return False

def process_cjk_language(lang, text_chunks, base_name):
    """Special processing for CJK languages with pauses"""
    output_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_{lang}.mp3")
    temp_files = []
    
    for i, chunk in enumerate(text_chunks):
        temp_file = os.path.join(DOWNLOAD_DIR, f"temp_{lang}_{i}.mp3")
        success = False
        
        for attempt in range(MAX_RETRIES):
            if generate_with_pauses(chunk, lang, temp_file):
                success = True
                break
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        if success:
            temp_files.append(temp_file)
        else:
            print(f"Failed chunk {i+1}/{len(text_chunks)}")
    
    if temp_files:
        combine_audio_files(temp_files, output_path)
        print(f"✅ Success: {output_path} ({len(temp_files)} chunks)")
        return True
    return False

def process_regular_language(lang, text_chunks, base_name):
    """Processing for non-CJK languages"""
    output_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_{lang}.mp3")
    temp_files = []
    
    for i, chunk in enumerate(text_chunks):
        temp_file = os.path.join(DOWNLOAD_DIR, f"temp_{lang}_{i}.mp3")
        encoded_text = quote(chunk, safe='')
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=gtx&q={encoded_text}"
        
        success = False
        for attempt in range(MAX_RETRIES):
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://translate.google.com/'
            }, timeout=10)
            
            if response.status_code == 200:
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                success = True
                break
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        if success:
            temp_files.append(temp_file)
        else:
            print(f"Failed chunk {i+1}/{len(text_chunks)}")
    
    if temp_files:
        combine_audio_files(temp_files, output_path)
        print(f"✅ Success: {output_path} ({len(temp_files)} chunks)")
        return True
    return False

def combine_audio_files(input_files, output_path):
    """Combine multiple audio files using simple binary concatenation"""
    with open(output_path, 'wb') as outfile:
        for filename in input_files:
            with open(filename, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(filename)  # Clean up temp file

def process_markdown_file():
    """Main processing function"""
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(MARKDOWN_FILE))[0]
    md_content = get_clean_md_content(MARKDOWN_FILE)
    
    if not md_content:
        print("No content found in the markdown file.")
        return
    
    print(f"Processing {len(md_content)} characters")
    
    # Process all CJK languages first
    for lang in TARGET_LANGUAGES.get('cjk', {}):
        print(f"\nProcessing {lang} (CJK)...")
        
        # Get chunk size for this language
        chunk_size = TARGET_LANGUAGES['cjk'][lang]
        
        # Clean and split text
        clean_text = clean_cjk_text(md_content)
        chunks = split_cjk_text(clean_text, chunk_size)
        
        # Process with special CJK handling
        if not process_cjk_language(lang, chunks, base_name):
            print(f"❌ Failed to process {lang}")
    
    # Process regular languages
    for lang in TARGET_LANGUAGES.get('others', {}):
        print(f"\nProcessing {lang}...")
        
        chunk_size = TARGET_LANGUAGES['others'][lang]
        chunks = split_text(md_content, chunk_size)
        
        if not process_regular_language(lang, chunks, base_name):
            print(f"❌ Failed to process {lang}")

if __name__ == "__main__":
    # Verify pydub/ffmpeg availability
    try:
        AudioSegment.from_mp3
    except:
        print("Installing pydub...")
        os.system("pip install pydub")
        print("Please install ffmpeg: sudo apt-get install ffmpeg")
    
    process_markdown_file()
    print("Processing complete!")