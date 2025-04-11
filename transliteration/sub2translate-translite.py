import re
import csv
import time
from concurrent.futures import ThreadPoolExecutor
from translationFunctions import (
    translate_text, 
    translate_parallel, 
    transliterate, 
    TARGET_PATTERNS, 
    LANGUAGE_CODE_MAP
)

from filter_language_characters import filter_language_characters

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
                        transliterated_line = transliterate(filtered_text, target_language)
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


# Function to process an SRT file
def process_srt(input_file, target_language, enable_transliteration=False):
    start_time = time.time()

    # Read the SRT file
    lines = read_srt(input_file)

    # Translate lines in parallel
    translated_lines = translate_parallel(lines, target_language)

    # Prepare output lines
    output_lines_v1 = []
    output_lines_v2 = []
    output_lines_v3 = []

    for line, translated_line in zip(lines, translated_lines):
        # Skip SRT timestamps and line numbers
        if re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()):
            output_lines_v1.append(line)
            output_lines_v2.append(line)
            output_lines_v3.append(line)
            continue

        # Add original and translated lines to Version 1
        output_lines_v1.append(line)
        output_lines_v1.append(translated_line + '\n')

        # Add original, translated, and transliterated lines to Version 2
        output_lines_v2.append(line)
        output_lines_v2.append(translated_line + '\n')
        if enable_transliteration:
            line_without_headers = re.sub(r'^#+\s*', '', translated_line)
            transliterated_line = transliterate(line_without_headers, target_language)
            # transliterated_line = transliterate(translated_line, target_language)
            output_lines_v2.append(transliterated_line + '\n')

        # Add only target language lines to Version 3
        if TARGET_PATTERNS.get(target_language).search(line):
            output_lines_v3.append(line)

    # Write output files
    base_name = input_file.replace('.srt', '')
    write_srt(f"{base_name}_{target_language}_v1.md", output_lines_v1)
    if enable_transliteration:
        write_srt(f"{base_name}_{target_language}_transliterated.md", output_lines_v2)
    write_srt(f"{base_name}_{target_language}_no_latin.md", output_lines_v3)

    # Print processing time
    end_time = time.time()
    processing_time = end_time - start_time
    print(f"Time to process {input_file}: {processing_time:.2f} seconds")

# Function to process all SRT files listed in a CSV
def process_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            input_file, target_language = row
            process_srt(input_file, target_language, enable_transliteration=True)

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
    # csv_file = "/home/zaya/Downloads/transliteration_files.csv"
    # process_csv(csv_file)
    input_file = "/home/zaya/Documents/Gitrepos/cinema/Subtitles/Chinese-A-brighter-summer-day.srt"
    target_language = "chinese"
    
    # process_srt(input_file, target_language, enable_transliteration=True)
    transliterate_srt(input_file, target_language)
    
    # 'de', 'it', 'fr', 'ru', 'zh-CN', 'ja', 'hi', 'ar', 'ko', 'en', 'es'
    # target_language = ["de", "ru", "zh-cn"]

   
