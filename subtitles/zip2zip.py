from pathlib import Path
import re
import csv
import os
import tempfile
import time
import traceback
import zipfile
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor
import sys
import chardet  # Add this import for encoding detection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from concurrent.futures import ThreadPoolExecutor
from transliteration.translationFunctions import translate_text, translate_parallel, transliterate, TARGET_PATTERNS, LANGUAGE_CODE_MAP, LANGUAGE_STYLES
from transliteration.filter_language_characters import filter_language_characters, filter_language_characters_preserve_spaces
from functools import lru_cache

# Import your translation functions (commented out as they're not provided)
# from translationFunctions import (
#     translate_text, 
#     transliterate, 
#     LANGUAGE_CODE_MAP,
#     LANGUAGE_STYLES
# )
# from filter_language_characters import filter_language_characters

# Function to read an SRT file with error handling
def read_srt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading SRT file {file_path}: {e}")
        return None

# Function to write an SRT file with error handling
def write_srt(file_path, lines):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error writing SRT file {file_path}: {e}")
        return False

def create_zip(input_file, output_files, output_dir=None):
    try:
        base_name = Path(input_file).stem
        zip_name = f"{base_name}.zip"
        if output_dir:
            zip_path = os.path.join(output_dir, zip_name)
        else:
            zip_path = zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in output_files:
                if os.path.exists(file):
                    arcname = os.path.basename(file)
                    zipf.write(file, arcname=arcname)
        return zip_path
    except Exception as e:
        print(f"Error creating zip file: {e}")
        return None

def apply_subtitle_style(text, language_code, enable_styling=True):
    """Applies language-specific styling to subtitles"""
    if not enable_styling:
        return text
    
    style = LANGUAGE_STYLES.get(language_code.lower(), {})
    if not style:
        return text
    
    color = style.get('color', '#FFFFFF')  # Default white if no color
    size = style.get('size', 16)          # Default 16px if no size
    
    return f'<font color="{color}" size="{size}">{text}</font>'

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
    output_file = input_file.replace('.srt', f'_{target_language}_trans.srt')
    write_srt(output_file, output_lines)
    
    return output_file

def translate_srt_block(block, target_languages):
    """Helper function to translate a single SRT block"""
    translated_blocks = {}
    
    # Extract the text lines from the block
    lines = block.split('\n')
    if len(lines) < 3:
        return translated_blocks
    
    # Get the original text (combining multiple text lines)
    original_text = '\n'.join(lines[2:-1])
    
    # Translate to each target language
    for lang in target_languages:
        translated_text = translate_text(original_text, lang)
        translated_blocks[lang] = {
            'original': original_text,
            'translated': translated_text
        }
    
    return translated_blocks

def generate_combination_srt(input_file, target_languages, combination, enable_transliteration=False, enable_styling=False):
    """Generate SRT file for a combination of languages with optional transliteration"""
    base_name = input_file.replace('.srt', '')
    combination_name = '_'.join(combination)
    output_file = f"{base_name}_{combination_name}.srt"
    
    # Read file with BOM handling
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
    
    # Extract all text content that needs translation
    text_lines = [line for line in lines if line.strip() and 
                 not re.match(r'^\d+$', line.strip()) and 
                 not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip())]
    
    # Create translation and transliteration maps for each language
    translation_maps = {}
    transliteration_maps = {}
    
    for lang in combination:
        # Translate texts
        translated_texts = [apply_subtitle_style(translate_text(line, lang), lang, enable_styling) for line in text_lines]
        translation_maps[lang] = dict(zip(text_lines, translated_texts))
        
        # Prepare transliterations if needed        
        if should_transliterate(lang, enable_transliteration):
            transliterated_texts = []
            for original_text, translated_text in zip(text_lines, translated_texts):
                filtered = filter_language_characters(translated_text, target_language=LANGUAGE_CODE_MAP[lang])
                transliterated = transliterate(filtered, lang) if filtered else ""
                transliterated_texts.append(transliterated)
            transliteration_maps[lang] = dict(zip(text_lines, transliterated_texts))
    
    # Process each block
    output_lines = []
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        line = lines[i]
        stripped = line.strip()
        
        # Start of a new subtitle block
        if stripped.isdigit():  # Line number
            block_lines = [f"{line}\n"]  # Store line number
            i += 1
            
            # Add timestamp if present
            if i < total_lines and re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', lines[i].strip()):
                block_lines.append(f"{lines[i]}\n")
                i += 1
                
                # Collect all text lines in this block
                text_block = []
                while i < total_lines and lines[i].strip():
                    original_line = lines[i]
                    block_lines.append(f"{original_line}\n")
                    text_block.append(original_line)
                    i += 1
                
                # Add translations and transliterations for each language in combination
                for lang in combination:
                    for original_line in text_block:
                        if original_line in translation_maps[lang]:
                            # Add translated line
                            translated_line = translation_maps[lang][original_line]
                            block_lines.append(f"{translated_line}\n")
                            
                            # Add transliteration if available
                            if lang in transliteration_maps and original_line in transliteration_maps[lang]:
                                transliterated_line = transliteration_maps[lang][original_line]
                                if transliterated_line.strip():  # Only add if not empty
                                    block_lines.append(f"{transliterated_line}\n")
                
                # Add empty line after block
                block_lines.append("\n")
                
                # Add complete block to output
                output_lines.extend(block_lines)
            continue
        
        # For any other lines
        output_lines.append(f"{line}\n")
        i += 1
    
    # Write output file
    write_srt(output_file, output_lines)
    return output_file

def process_single_language(input_file, target_language, output_file, enable_transliteration=False, enable_styling=False):
    """Process SRT file for a single target language with optional transliteration"""
    # Read file and decode any BOM
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
    
    # Translate all text content (excluding timestamps and numbers)
    text_lines = [line for line in lines if line.strip() and 
                 not re.match(r'^\d+$', line.strip()) and 
                 not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip())]
    
    # Translate all text lines at once
    translated_texts = [apply_subtitle_style(translate_text(line, target_language), target_language, enable_styling) for line in text_lines]
    
    # Create translation mapping
    translation_map = dict(zip(text_lines, translated_texts))
    
    output_lines = []
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        line = lines[i]
        stripped = line.strip()
        
        # Handle SRT block structure
        if stripped.isdigit():  # Line number
            output_lines.append(f"{line}\n")
            i += 1
            
            # Process timestamp if present
            if i < total_lines and re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', lines[i].strip()):
                output_lines.append(f"{lines[i]}\n")
                i += 1
                
                # Process text lines in this block
                while i < total_lines and lines[i].strip():
                    original_line = lines[i]
                    output_lines.append(f"{original_line}\n")
                    
                    # Get translation from our map
                    if original_line in translation_map:
                        translated_line = translation_map[original_line]
                        output_lines.append(f"{translated_line}\n")
                        
                        # Add transliteration if enabled and supported
                        if should_transliterate(target_language, enable_transliteration):
                            filtered_text = filter_language_characters(
                                translated_line, 
                                target_language=LANGUAGE_CODE_MAP[target_language]
                            )
                            if filtered_text:
                                transliterated_line = transliterate(filtered_text, target_language)
                                output_lines.append(f"{transliterated_line}\n")
                    i += 1
                
                # Add empty line after block
                if i < total_lines and not lines[i].strip():
                    output_lines.append("\n")
                    i += 1
            continue
        
        # For any other lines
        output_lines.append(f"{line}\n")
        i += 1
    
    write_srt(output_file, output_lines)
    return output_file

def should_transliterate(lang, enable_transliteration):
    # Languages that can be transliterated (those not in this list use Latin script)
    transliteratable_languages = ['zh-ch', 'zh-CN', 'hi', 'ar', 'ja', 'ko']
    
    return enable_transliteration and lang in transliteratable_languages

def process_multilingual_srt(input_file, target_languages, enable_transliteration=False, enable_styling=False):
    start_time = time.time()
    output_files = []
    base_name = input_file.replace('.srt', '')
    
    # 1. Generate single language files
    for lang in target_languages:
        # Generate standard translation
        output_file = f"{base_name}_{lang}.srt"
        process_single_language(input_file, lang, output_file, enable_transliteration, enable_styling)
        output_files.append(output_file)
        
        # Generate transliterated version if enabled
        # if should_transliterate(lang, enable_transliteration):
        #     print(f"Transliterating {lang}...")
        #     transliterated_file = transliterate_srt(input_file, lang)
        #     output_files.append(transliterated_file)
    
    # 2. Generate all combinations (2 by 2, 3 by 3, etc.)
    for r in range(2, len(target_languages)+1):
        for combo in combinations(target_languages, r):
            combo_file = generate_combination_srt(input_file, target_languages, combo, enable_transliteration, enable_styling)
            output_files.append(combo_file)
    
    # 3. Create a zip file with all outputs
    zip_file = create_zip(input_file, output_files)
    
    # 4. Clean up individual SRT files
    # for srt_file in output_files:
    #     try:
    #         os.remove(srt_file)
    #         print(f"Removed temporary file: {srt_file}")
    #     except OSError as e:
    #         print(f"Error removing {srt_file}: {e}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    print(f"Time to process {input_file}: {processing_time:.2f} seconds")
    print(f"Created zip file: {zip_file}")
    
    return zip_file


def join_lines_if_starts_with_letter(lines):
    """Apply regex to join lines if next line starts with a letter"""
    joined_lines = []
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        current_line = lines[i]
        
        # Check if we should look ahead
        if i + 1 < total_lines and lines[i+1].strip():
            next_line = lines[i+1]
            # Check if next line starts with a letter (lowercase or uppercase)
            if re.match(r'^[a-zA-Z]', next_line.lstrip()):
                # Join current line with next line (remove newline from current)
                joined_line = current_line.rstrip('\n') + ' ' + next_line.lstrip()
                joined_lines.append(joined_line + '\n')
                i += 2  # Skip the next line since we've joined it
                continue
        
        # If no join, just add the current line
        joined_lines.append(current_line)
        i += 1
    
    return joined_lines

def process_single_srt_file(srt_path, target_languages, enable_transliteration, enable_styling):
    """Process a single SRT file with the given parameters"""
    # Read the SRT file
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Apply the line joining transformation
    transformed_lines = join_lines_if_starts_with_letter(lines)
    
    # Write the transformed file to a temporary location
    temp_dir = tempfile.mkdtemp()
    base_name = os.path.basename(srt_path)
    temp_srt_path = os.path.join(temp_dir, base_name)
    with open(temp_srt_path, 'w', encoding='utf-8') as f:
        f.writelines(transformed_lines)
    
    # Process the transformed file
    zip_path = process_multilingual_srt(
        temp_srt_path, 
        target_languages, 
        enable_transliteration=enable_transliteration, 
        enable_styling=enable_styling
    )
    
    # Clean up temporary files
    try:
        os.remove(temp_srt_path)
        os.rmdir(temp_dir)
    except OSError:
        pass
    
    return zip_path
# Cache translations to avoid repeating the same work
@lru_cache(maxsize=1000)
def cached_translate_text(text, lang):
    return translate_text(text, lang)

@lru_cache(maxsize=1000)
def cached_transliterate(text, lang):
    filtered = filter_language_characters(text, target_language=LANGUAGE_CODE_MAP[lang])
    return transliterate(filtered, lang) if filtered else ""

def generate_combination_output(lines, translation_maps, transliteration_maps, output_file):
    """Generate output for a combination of languages"""
    with open(output_file, 'w', encoding='utf-8') as f:
        i = 0
        total_lines = len(lines)
        while i < total_lines:
            line = lines[i]
            stripped = line.strip()
            
            if stripped.isdigit():  # Line number
                f.write(line)
                i += 1
                if i < total_lines and re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', lines[i].strip()):
                    f.write(lines[i])
                    i += 1
                    while i < total_lines and lines[i].strip():
                        original = lines[i].strip()
                        f.write(lines[i])
                        
                        # Add translations and transliterations for each language in the combination
                        for lang in translation_maps:
                            if original in translation_maps[lang]:
                                f.write(translation_maps[lang][original] + '\n')
                                if lang in transliteration_maps and original in transliteration_maps[lang] and transliteration_maps[lang][original]:
                                    f.write(transliteration_maps[lang][original] + '\n')
                        i += 1
                    
                    if i < total_lines and not lines[i].strip():
                        f.write('\n')
                        i += 1
                continue
            
            f.write(line)
            i += 1

def optimized_process_single_srt_file(srt_path, target_languages, enable_transliteration, enable_styling):
    """Optimized version that caches translations and transliterations"""
    # Read and transform the SRT file
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Create translation and transliteration mappings
    translation_maps = {lang: {} for lang in target_languages}
    transliteration_maps = {lang: {} for lang in target_languages}
    
    # First pass: identify all unique text segments that need translation
    text_segments = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not re.match(r'^\d+$', stripped) and \
           not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', stripped):
            text_segments.add(stripped)
    
    # Pre-translate all unique segments for each language
    for lang in target_languages:
        for segment in text_segments:
            translated = apply_subtitle_style(
                cached_translate_text(segment, lang), 
                lang, 
                enable_styling
            )
            translation_maps[lang][segment] = translated
            
            if should_transliterate(lang, enable_transliteration):
                transliteration_maps[lang][segment] = cached_transliterate(translated, lang)
    
    # Process all output files in one pass
    base_name = os.path.splitext(os.path.basename(srt_path))[0]
    temp_dir = tempfile.mkdtemp()
    output_files = []
    
    # 1. Generate single language files
    for lang in target_languages:
        output_file = os.path.join(temp_dir, f"{base_name}_{lang}.srt")
        generate_single_language_output(
            lines, 
            translation_maps[lang], 
            transliteration_maps[lang] if should_transliterate(lang, enable_transliteration) else None,
            output_file
        )
        output_files.append(output_file)
    
    # 2. Generate combinations (limit to practical combinations)
    practical_combinations = []
    if len(target_languages) > 1:
        # Only generate 2-language combinations if we have many languages
        practical_combinations = list(combinations(target_languages, 2))
        if len(target_languages) <= 3:  # For 3 languages, also include the 3-way combination
            practical_combinations.append(tuple(target_languages))
    
    for combo in practical_combinations:
        combo_name = '_'.join(combo)
        output_file = os.path.join(temp_dir, f"{base_name}_{combo_name}.srt")
        generate_combination_output(
            lines,
            {lang: translation_maps[lang] for lang in combo},
            {lang: transliteration_maps[lang] for lang in combo if should_transliterate(lang, enable_transliteration)},
            output_file
        )
        output_files.append(output_file)
    
    # Create zip file
    zip_path = os.path.join(temp_dir, f"{base_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in output_files:
            zipf.write(file, arcname=os.path.basename(file))
    
    # Clean up
    for file in output_files:
        try:
            os.remove(file)
        except OSError:
            pass
    
    return zip_path

def generate_single_language_output(lines, translation_map, transliteration_map, output_file):
    """Generate output for a single language"""
    with open(output_file, 'w', encoding='utf-8') as f:
        i = 0
        total_lines = len(lines)
        while i < total_lines:
            line = lines[i]
            stripped = line.strip()
            
            if stripped.isdigit():  # Line number
                f.write(line)
                i += 1
                if i < total_lines and re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', lines[i].strip()):
                    f.write(lines[i])
                    i += 1
                    while i < total_lines and lines[i].strip():
                        original = lines[i].strip()
                        f.write(lines[i])
                        if original in translation_map:
                            f.write(translation_map[original] + '\n')
                            if transliteration_map and original in transliteration_map and transliteration_map[original]:
                                f.write(transliteration_map[original] + '\n')
                        i += 1
                    if i < total_lines and not lines[i].strip():
                        f.write('\n')
                        i += 1
                continue
            
            f.write(line)
            i += 1

def process_single_srt(input_srt, target_languages, enable_transliteration=False, enable_styling=False):
    """Process a single SRT file and return the paths of generated files with error handling"""
    output_files = []
    base_name = Path(input_srt).stem
    
    try:
        # 1. Generate single language files
        for lang in target_languages:
            try:
                # Generate standard translation
                output_file = f"{base_name}_{lang}.srt"
                if process_single_language(input_srt, lang, output_file, enable_transliteration, enable_styling):
                    output_files.append(output_file)
                
                # Generate transliterated version if enabled
                if should_transliterate(lang, enable_transliteration):
                    try:
                        transliterated_file = transliterate_srt(input_srt, lang)
                        output_files.append(transliterated_file)
                    except Exception as e:
                        print(f"Error transliterating {input_srt} for {lang}: {e}")
                        continue
            except Exception as e:
                print(f"Error processing {input_srt} for language {lang}: {e}")
                continue
        
        # 2. Generate all combinations (2 by 2, 3 by 3, etc.)
        for r in range(2, len(target_languages)+1):
            for combo in combinations(target_languages, r):
                try:
                    combo_file = generate_combination_srt(input_srt, target_languages, combo, enable_transliteration, enable_styling)
                    output_files.append(combo_file)
                except Exception as e:
                    print(f"Error generating combination {combo} for {input_srt}: {e}")
                    continue
        
        # 3. Create a zip file with all outputs
        temp_dir = tempfile.mkdtemp()
        zip_file = create_zip(input_srt, output_files, temp_dir)
        
        # 4. Clean up individual SRT files
        for srt_file in output_files:
            try:
                if os.path.exists(srt_file):
                    os.remove(srt_file)
            except OSError as e:
                print(f"Error removing temporary file {srt_file}: {e}")
        
        return zip_file if zip_file else None
        
    except Exception as e:
        print(f"Error processing SRT file {input_srt}: {e}")
        traceback.print_exc()
        return None

def merge_subtitle_lines(input_file, output_file=None):
    """Merge subtitle lines and save the modified content with error handling."""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        content = None
        
        for encoding in encodings:
            try:
                with open(input_file, 'r', encoding=encoding) as f:
                    content = f.read()
                # If we get here, the encoding worked
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # If none of the encodings worked, fall back to binary with error handling
            with open(input_file, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
        
        # Split into individual subtitle blocks
        blocks = re.split(r'\n\n+', content.strip())
        processed_blocks = []
        
        for block in blocks:
            try:
                lines = block.split('\n')
                if len(lines) < 3:
                    processed_blocks.append(block)
                    continue
                
                # Keep the number and timestamp lines as-is
                number_line = lines[0]
                time_line = lines[1]
                
                # Merge all text lines into one, replacing newlines with spaces
                text_lines = [line.strip() for line in lines[2:] if line.strip()]
                merged_text = ' '.join(text_lines)
                
                # Rebuild the block
                processed_block = f"{number_line}\n{time_line}\n{merged_text}"
                processed_blocks.append(processed_block)
            except Exception as e:
                print(f"Error processing block in {input_file}: {e}")
                processed_blocks.append(block)  # Keep the original block if there's an error
                continue
        
        # Join all blocks with double newlines
        merged_content = '\n\n'.join(processed_blocks)

        # Write to output file or overwrite input file
        if output_file is None:
            output_file = input_file
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(merged_content)
            
        return True
    except Exception as e:
        print(f"Error merging subtitle lines in {input_file}: {e}")
        return False


def process_zip_of_srts(input_zip_path, target_languages, enable_transliteration=False, enable_styling=False):
    """Process a zip file containing multiple SRT files with error handling"""
    temp_dir = tempfile.mkdtemp()
    output_zips = []
    
    try:
        # Extract all SRT files from the input zip
        with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Process each SRT file
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith('.srt'):
                    srt_path = os.path.join(root, file)
                    try:
                        # Pre-process: merge lines
                        if not merge_subtitle_lines(srt_path):
                            print(f"Skipping {srt_path} due to merge error")
                            continue
                        
                        # Process the SRT
                        output_zip = process_single_srt(
                            srt_path, 
                            target_languages, 
                            enable_transliteration, 
                            enable_styling
                        )
                        
                        if output_zip:
                            output_zips.append(output_zip)
                    except Exception as e:
                        print(f"Error processing SRT file {srt_path}: {e}")
                        traceback.print_exc()
                        continue
        
        # Create final zip containing all individual zips
        if output_zips:
            final_zip_path = os.path.join(os.path.dirname(input_zip_path), "all_translations.zip")
            with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as final_zip:
                for zip_file in output_zips:
                    if zip_file and os.path.exists(zip_file):
                        final_zip.write(zip_file, arcname=os.path.basename(zip_file))
            
            # Clean up temporary files
            for zip_file in output_zips:
                try:
                    if os.path.exists(zip_file):
                        os.remove(zip_file)
                except OSError as e:
                    print(f"Error removing temporary zip file {zip_file}: {e}")
            
            return final_zip_path
        else:
            print("No SRT files were successfully processed")
            return None
            
    except Exception as e:
        print(f"Error processing zip file {input_zip_path}: {e}")
        traceback.print_exc()
        return None
    finally:
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except OSError as e:
            print(f"Error removing temporary directory {temp_dir}: {e}")

# Main function
if __name__ == "__main__":
    # Example usage:
    input_zip_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/all_subtitles/6.zip"
    target_languages = ["zh-ch"]  # Your target languages
    
    final_zip = process_zip_of_srts(
        input_zip_path,
        target_languages,
        enable_transliteration=True,
        enable_styling=False
    )
    
    if final_zip:
        print(f"Successfully created final zip: {final_zip}")
    else:
        print("Failed to create final zip file")