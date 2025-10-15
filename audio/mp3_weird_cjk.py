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
    "zh-CN": {"between_words": 300, "between_chars": 150},
    "ja": {"between_words": 400, "between_chars": 200},
    "ko": {"between_words": 300, "between_chars": 150},
}

# Configuration
MARKDOWN_FILE = "/home/zaya/Documents/Gitrepos/Linktrees/Languages/WordList.md"
DOWNLOAD_DIR = "/home/zaya/Downloads"
# TARGET_LANGUAGES = ["de", "it", "fr", "ru", "zh-CN", "ja", "hi", "ar", "ko", "en", "es"]  # Test with Russian first
# TARGET_LANGUAGES = {
#     'cjk': {'zh-CN': 50, 'ja': 50, 'ko': 50},  # 50 char limit for CJK
#     'others': {'de': 200, 'fr': 200}  # Higher limit for others
# }
TARGET_LANGUAGES = {
    "cjk": {"ja": 50},  # 50 char limit for CJK
}
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2  # More conservative delay


def add_cjk_pauses(text, lang):
    """Insert pauses between CJK characters/words"""
    if lang not in CJK_PAUSE_CONFIG:
        return text

    config = CJK_PAUSE_CONFIG[lang]

    # For Chinese - pause between characters
    if lang == "zh-CN":
        return " ".join(text)  # Adds natural pauses

    # For Japanese - special handling for kanji/kana
    elif lang == "ja":
        # Insert pauses after particles (を, に, で, etc.)
        particles = ["を", "に", "で", "が", "は", "の"]
        for p in particles:
            text = text.replace(p, p + " ")
        return " ".join(text.split())  # Normalize spaces

    # For Korean - pause between words
    elif lang == "ko":
        return " ".join(text.split())  # Adds word breaks

    return text


def generate_with_pauses(text, lang, output_path):
    """Generate audio with proper pauses for CJK"""
    # Add pauses to the text
    processed_text = add_cjk_pauses(text, lang)

    # Generate audio as before
    encoded_text = quote(processed_text, safe="")
    url = (
        f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=gtx&q={encoded_text}"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://translate.google.com/",
        },
    )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)

        # Add additional pauses if needed
        if lang in CJK_PAUSE_CONFIG:
            audio = AudioSegment.from_mp3(output_path)

            # Insert additional silent pauses
            pause_duration = CJK_PAUSE_CONFIG[lang]["between_chars"]
            silent_pause = AudioSegment.silent(duration=pause_duration)

            # Split audio on natural pauses
            chunks = split_on_silence(audio, min_silence_len=50, silence_thresh=-40)

            # Recombine with additional pauses
            combined = AudioSegment.empty()
            for chunk in chunks:
                combined += chunk + silent_pause

            # Save final audio
            combined.export(output_path, format="mp3")

        return True
    return False


def get_clean_md_content(md_file_path):
    """Read and clean markdown content"""
    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove markdown headers and clean up
    content = re.sub(r"^#.*$", "", content, flags=re.MULTILINE)
    content = " ".join(content.split())
    return content


def split_text(text, chunk_size):
    """Split text into chunks respecting word boundaries"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# def generate_audio_chunk(text, language, output_path):
#     """Generate and save audio chunk using Google Translate TTS"""
#     for attempt in range(MAX_RETRIES):
#         try:
#             tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={requests.utils.quote(text)}&tl={language}&client=tw-ob"
#             response = requests.get(tts_url, headers={
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#             })

#             if response.status_code == 200:
#                 with open(output_path, 'wb') as f:
#                     f.write(response.content)
#                 return True
#             print(f"Attempt {attempt + 1} failed: HTTP {response.status_code}")
#         except Exception as e:
#             print(f"Attempt {attempt + 1} error: {str(e)}")

#         time.sleep(DELAY_BETWEEN_REQUESTS)

#     return False


def combine_audio_files(input_files, output_path):
    """Combine multiple audio files using simple binary concatenation"""
    with open(output_path, "wb") as outfile:
        for filename in input_files:
            with open(filename, "rb") as infile:
                outfile.write(infile.read())
            os.remove(filename)  # Clean up temp file


def clean_text(text):
    """Special cleaning for CJK texts"""
    # Remove problematic characters
    text = re.sub(r'[<>"{}|\\^\[\]`]', "", text)
    # Normalize spaces
    return " ".join(text.split())


def clean_cjk_text(text):
    """Special cleaning for CJK characters"""
    # Remove all non-CJK punctuation and symbols
    text = re.sub(r"[^\w\s\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7a3]", "", text)
    return text.strip()


def split_cjk_text(text, char_limit):
    """Special splitter for Chinese/Japanese/Korean"""
    chunks = []
    current_chunk = []
    current_length = 0

    for char in text:
        char_length = len(char.encode("utf-8"))
        if current_length + char_length > char_limit:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(char)
        current_length += char_length

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


def generate_audio_chunk(text, lang, output_path):
    """Ultra-conservative TTS generation"""
    text = clean_cjk_text(text) if lang in TARGET_LANGUAGES["cjk"] else text
    encoded_text = quote(text, safe="")

    try:
        # Use the newer Google TTS API endpoint
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=gtx&q={encoded_text}"

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://translate.google.com/",
            },
            timeout=10,
        )

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        print(f"HTTP {response.status_code} | Chunk length: {len(text)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    return False


def process_cjk_language(lang, text_chunks, base_name):
    """Special processing for CJK languages"""
    output_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_{lang}.mp3")
    temp_files = []

    for i, chunk in enumerate(text_chunks):
        temp_file = os.path.join(DOWNLOAD_DIR, f"temp_{lang}_{i}.mp3")

        # Generate with pauses
        if generate_with_pauses(chunk, lang, temp_file):
            temp_files.append(temp_file)
        else:
            print(f"Failed to generate chunk {i+1}")

    if temp_files:
        combine_audio_files(temp_files, output_path)
        print(f"✅ Successfully created: {output_path}")
        return True
    return False


def process_language(lang, base_name, translation):
    """Process each language separately"""
    output_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_{lang}.mp3")
    temp_files = []
    chunk_size = TARGET_LANGUAGES["cjk"].get(lang, 200)

    if lang in TARGET_LANGUAGES["cjk"]:
        chunks = [translation[i : i + chunk_size] for i in range(0, len(translation), chunk_size)]
    else:
        chunks = split_text(translation, chunk_size)

    for i, chunk in enumerate(chunks):
        temp_file = os.path.join(DOWNLOAD_DIR, f"temp_{lang}_{i}.mp3")
        success = False

        for attempt in range(MAX_RETRIES):
            if generate_audio_chunk(chunk, lang, temp_file):
                success = True
                break
            time.sleep(DELAY_BETWEEN_REQUESTS)

        if success:
            temp_files.append(temp_file)
        else:
            print(f"Failed chunk {i+1} (length: {len(chunk)})")

    if temp_files:
        combine_audio_files(temp_files, output_path)
        print(f"✅ Success: {output_path} ({len(temp_files)} chunks)")
        return True
    return False


def process_markdown_file():
    """Main function to process the markdown file"""
    import re
    import time

    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(MARKDOWN_FILE))[0]
    md_content = get_clean_md_content(MARKDOWN_FILE)

    if not md_content:
        print("No content found in the markdown file.")
        return

    print(f"Processing {len(md_content)} characters")

    for lang_group in TARGET_LANGUAGES.values():
        for lang in lang_group:
            output_filename = f"{base_name}_{lang}.mp3"
            output_path = os.path.join(DOWNLOAD_DIR, output_filename)

            print(f"Processing {lang} -> {output_path}")

            # Translate the content
            # translator = GoogleTranslator(source="auto", target=lang)
            # try:
            #     translation = translator.translate(md_content)
            # except Exception as e:
            #     print(f"Translation failed: {str(e)}")
            #     continue

            if not process_language(lang, base_name, md_content):
                print(f"❌ Failed to process {lang}")


if __name__ == "__main__":
    process_markdown_file()
    print("Processing complete!")
