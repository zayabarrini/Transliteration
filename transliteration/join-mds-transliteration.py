import re
import time
from deep_translator import GoogleTranslator  # For translation (if needed)
import pypinyin  # For Chinese Pinyin
import pykakasi  # For Japanese Romaji
from transliterate import translit  # For Russian
from indic_transliteration import sanscript  # For Hindi
from indic_transliteration.sanscript import transliterate as indic_transliterate
from hangul_romanize import Transliter  # For Korean
from hangul_romanize.rule import academic

# Map target_language to Google Translate language codes (not used here but kept for consistency)
LANGUAGE_CODE_MAP = {
    "chinese": "zh-CN",
    "japanese": "ja",
    "russian": "ru",
    "hindi": "hi",
    "arabic": "ar",
    "korean": "ko",
}

# Precompile regex patterns
TARGET_PATTERNS = {
    "chinese": re.compile(r"[\u4e00-\u9fff]"),
    "russian": re.compile(r"[\u0400-\u04FF]"),
    "hindi": re.compile(r"[\u0900-\u097F]"),
    "japanese": re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF]"),
    "korean": re.compile(r"[\uAC00-\uD7AF]"),
    "arabic": re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"),
}


# Function to read a file
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


# Function to write a file
def write_file(file_path, lines):
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# Function to transliterate text
def transliterate(input_text, language):
    if language == "chinese":
        return " ".join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.TONE3))
    elif language == "japanese":
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")  # Hiragana to Romaji
        kakasi.setMode("K", "a")  # Katakana to Romaji
        kakasi.setMode("J", "a")  # Kanji to Romaji
        converter = kakasi.getConverter()
        return converter.do(input_text)
    elif language == "russian":
        return translit(input_text, "ru", reversed=True)
    elif language == "hindi":
        return indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
    elif language == "korean":
        transliter = Transliter(rule=academic)
        return transliter.translit(input_text)
    else:
        return input_text  # For languages without a need for transliteration


# Function to process files
def process_file(input_base, input_language, target_language, enable_transliteration=False):
    start_time = time.time()

    # Read the input files
    base_lines = read_file(input_base)
    language_lines = read_file(input_language)

    # Prepare output lines
    output_lines_v1 = []  # Original + Target Language
    output_lines_v2 = []  # Original + Target Language + Transliteration
    output_lines_v3 = []  # Only Target Language (no Latin characters)

    # Combine and process lines
    for base_line, lang_line in zip(base_lines, language_lines):
        # Skip SRT timestamps and line numbers
        if re.match(r"^\d+$", base_line.strip()) or re.match(
            r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$", base_line.strip()
        ):
            output_lines_v1.append(base_line)
            output_lines_v2.append(base_line)
            output_lines_v3.append(base_line)
            continue

        # Add original and target language lines to Version 1
        output_lines_v1.append(base_line)
        output_lines_v1.append(lang_line)

        # Add original, target language, and transliterated lines to Version 2
        output_lines_v2.append(base_line)
        output_lines_v2.append(lang_line)
        if enable_transliteration:
            line_without_headers = re.sub(r"^#+\s*", "", lang_line.strip())
            transliterated_line = transliterate(line_without_headers, target_language)
            # transliterated_line = transliterate(lang_line.strip(), target_language)
            output_lines_v2.append(transliterated_line + "\n\n")

        # Add only target language lines to Version 3
        if TARGET_PATTERNS.get(target_language).search(lang_line):
            output_lines_v3.append(lang_line)

    # Write output files
    base_name = input_base.replace(".md", "")
    write_file(f"{base_name}_{target_language}_v1.md", output_lines_v1)
    if enable_transliteration:
        write_file(f"{base_name}_{target_language}_transliterated.md", output_lines_v2)
    write_file(f"{base_name}_{target_language}_no_latin.md", output_lines_v3)

    # Print processing time
    end_time = time.time()
    processing_time = end_time - start_time
    print(f"Time to process {input_base}: {processing_time:.2f} seconds")


# Main function
if __name__ == "__main__":
    input_base = "/home/zaya/Documents/Ebooks/Transliteration/Favorite-movies-3.md"  # Latin version
    input_language = "/home/zaya/Documents/Ebooks/Transliteration/Russian-Favorite-Movies-3.0.md"  # Target language version
    target_language = "russian"  # Target language
    process_file(input_base, input_language, target_language, enable_transliteration=True)
