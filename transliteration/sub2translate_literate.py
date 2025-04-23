import re
import csv
import time
import sys
import os
import zipfile
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from transliteration.translationFunctions import translate_text, translate_parallel, TARGET_PATTERNS, LANGUAGE_CODE_MAP
# from transliteration.filter_language_characters import filter_language_characters
# from transliteration.transliteration import transliterate
from transliteration import (
    translate_parallel,
    LANGUAGE_CODE_MAP,
    TARGET_PATTERNS,
    filter_language_characters,
    transliterate, 
    add_furigana,
    transliterate_for_subtitles
)

# Function to read an SRT file
def read_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

# Function to write an SRT file
def write_srt(file_path, lines):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
def transliterate_srt(input_file: str, target_language: str) -> str:
    """
    Transliterates the text lines in an SRT file based on the target language.
    Skips SRT timestamps and line numbers.
    
    Args:
        input_file: Path to the input SRT file
        target_language: Language code for transliteration
    
    Returns:
        Path to the output transliterated SRT file
    """    
    # Read the SRT file
    lines = read_srt(input_file)
    
    # Prepare output lines
    output_lines = []
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        line = lines[i]
        
        # Handle SRT block structure
        if re.match(r'^\d+$', line.strip()):  # Line number
            output_lines.append(line)
            i += 1
            if i < total_lines and re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', lines[i].strip()):  # Timestamp
                output_lines.append(lines[i])
                i += 1
                # Process text lines in this block
                while i < total_lines and lines[i].strip():
                    original_line = lines[i].strip()
                    # Filter to get only target language characters
                    filtered_text = filter_language_characters(original_line, target_language=LANGUAGE_CODE_MAP[target_language])
                    
                    if filtered_text:  # Only process if target language text exists
                        output_lines.append(original_line + '\n')
                        print(f"Transliterating: {filtered_text}")  # Debug
                        transliterated_line = transliterate_for_subtitles(filtered_text, target_language)
                        # transliterated_line = add_furigana(filtered_text, transliterated_line, target_language)

                        if isinstance(transliterated_line, list):
                            # For Japanese: list of dictionaries
                            if target_language.lower() in ['ja', 'jp', 'japanese'] and transliterated_line and isinstance(transliterated_line[0], dict):
                                # Extract the 'hepburn' romanization
                                transliterated_line = ' '.join([item.get('hepburn', '') for item in transliterated_line])
                            else:
                                # For other cases where it might be a list of strings
                                transliterated_line = ' '.join(str(item) for item in transliterated_line)
                        elif not isinstance(transliterated_line, str):
                            # Convert other non-string types to string
                            transliterated_line = str(transliterated_line)
                        output_lines.append(transliterated_line + '\n')
                    else:
                        output_lines.append(original_line + '\n')
                    i += 1
                # Add empty line that ends the block
                if i < total_lines and not lines[i].strip():
                    output_lines.append(lines[i])
                    i += 1
            continue
        
        # For any other case (shouldn't happen in well-formed SRT)
        output_lines.append(line)
        i += 1
    
    # Write output file
    output_file = input_file.replace('.srt', f'_{target_language}_transliterated.srt')
    write_srt(output_file, output_lines)
    
    return output_file


def process_srt(input_file, target_language, enable_translation=True, enable_transliteration=False):
    start_time = time.time()

    # Read the SRT file
    lines = read_srt(input_file)

    # Translate lines if translation is enabled
    translated_lines = lines  # Default to original lines if not translating
    if enable_translation:
        translated_lines = translate_parallel(lines, target_language)

    transliterate_srt(input_file, target_language)
    
    # Prepare output lines
    # output_lines_v1 = []
    # output_lines_v2 = []
    # output_lines_v3 = []

    # for line, processed_line in zip(lines, translated_lines):
    #     # Skip SRT timestamps and line numbers
    #     if re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()):
    #         output_lines_v1.append(line)
    #         output_lines_v2.append(line)
    #         output_lines_v3.append(line)
    #         continue

    #     # Add original and translated lines to Version 1
    #     if enable_translation:
    #         output_lines_v1.append(line)
    #         output_lines_v1.append(processed_line + '\n')
    #     else:
    #         output_lines_v1.append(line)

    #     # Add original, translated, and transliterated lines to Version 2
    #     output_lines_v2.append(line)
    #     if enable_translation:
    #         output_lines_v2.append(processed_line + '\n')
    #     if enable_transliteration:
    #         line_to_transliterate = processed_line if enable_translation else line
    #         line_without_headers = re.sub(r'^#+\s*', '', line_to_transliterate)
    #         transliterated_line = transliterate(line_without_headers, target_language)
    #         output_lines_v2.append(transliterated_line + '\n')

    #     # Add only target language lines to Version 3
    #     pattern = TARGET_PATTERNS.get(target_language.lower())  # Handle case insensitivity
    #     if not pattern:  # Fallback: try to find by mapped code
    #         mapped_code = LANGUAGE_CODE_MAP.get(target_language.lower())
    #         pattern = TARGET_PATTERNS.get(mapped_code) if mapped_code else None
            
    #     if pattern and pattern.search(line):
    #         output_lines_v3.append(line)

    # # Write output files
    # base_name = input_file.replace('.srt', '')
    # if enable_translation:
    #     write_srt(f"{base_name}_{target_language}_v1.srt", output_lines_v1)
    # if enable_transliteration:
    #     write_srt(f"{base_name}_{target_language}_trans.srt", output_lines_v2)
    # # write_srt(f"{base_name}_{target_language}_no_latin.srt", output_lines_v3)

    # # Print processing time
    # end_time = time.time()
    # processing_time = end_time - start_time
    # print(f"Time to process {input_file}: {processing_time:.2f} seconds")

def process_zip(zip_file):
    # Determine processing mode based on zip filename
    if "translate.zip" in zip_file:
        enable_translation = True
        enable_transliteration = False
    elif "transliterate.zip" in zip_file:
        enable_translation = False
        enable_transliteration = True
    else:
        enable_translation = True
        enable_transliteration = False
    print(f"Mode: translation={enable_translation}, transliteration={enable_transliteration}")  # Debug

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('.srt'):
                # Extract target_language from filename pattern "target_language"-filename.srt
                print(f"Found file in zip: {file_info.filename}")  # Debug

                match = re.match(r'^([a-zA-Z-]+?)-.+\.srt$', file_info.filename)
                if match:
                    language_key = match.group(1).lower()  # Normalize to lowercase
                    target_language = LANGUAGE_CODE_MAP.get(language_key)
                    
                    if target_language:
                        print(f"Processing: {file_info.filename} (detected language: {target_language})")
                        zip_ref.extract(file_info)
                        process_srt(
                            file_info.orig_filename, 
                            target_language, 
                            enable_translation=enable_translation, 
                            enable_transliteration=enable_transliteration
                        )
                    else:
                        print(f"SKIPPED: Unsupported language '{language_key}' in filename '{file_info.filename}'")
                else:
                    print(f"SKIPPED: Filename '{file_info.filename}' doesn't match expected pattern.")
                    
# Function to process all SRT files listed in a CSV
def process_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            input_file, target_language, enable_translation, enable_transliteration = row
            process_srt(input_file, target_language, 
                       enable_translation, 
                       enable_transliteration)

# Main function
if __name__ == "__main__":
    """
        Let's change to process a list of languages, let's make it a multilingual srt creator
        Based on the list of target_languages, it should produce a combination of languages:
        Example:
        for     target_language = ["de", "ru", "zh-cn"]
        it should translate to all the target languages
        Produce single files for each target_language
        Produce combinations 2 by 2, 3 by 3, until a srt that contains all target_languages
        Total subtitles should be: Cn,1 + Cn,2 + ... + Cn,n
        All the subtitles should be zipped together into Input_filename.zip
    """
    zip_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles/transliterate.zip"
    process_zip(zip_file)
    # csv_file = "/home/zaya/Downloads/trans.csv"
    # process_csv(csv_file)
    # input_file = "/home/zaya/Downloads/Zayas/zayascinema/trans/Gosford-de-(ja).srt"
    # target_language = "japanese"
    # input_file = "/home/zaya/Downloads/Zayas/zayascinema/trans/Fargo-de-(ch).srt"
    # target_language = "chinese"
    # input_file = "/home/zaya/Downloads/Zayas/zayascinema/trans/Ghandi-ru-(ar).srt"
    # target_language = "arabic"
    # input_file = "/home/zaya/Downloads/Zayas/zayascinema/trans/Little-hi.srt"
    # target_language = "hindi"    

    # process_srt(input_file, target_language, enable_transliteration=True)
    # transliterate_srt(input_file, target_language)
    
    # 'de', 'it', 'fr', 'ru', 'zh-CN', 'ja', 'hi', 'ar', 'ko', 'en', 'es'
    # target_language = ["de", "ru", "zh-cn"]

   
