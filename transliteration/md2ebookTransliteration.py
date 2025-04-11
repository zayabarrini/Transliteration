import re
import subprocess
import pypinyin  # For Chinese Pinyin
# import markdown
# import pandoc
import os
# import transliterate
# import arabic_reshaper
# import hangul_romanize
from indic_transliteration import sanscript  # For Hindi
from indic_transliteration.sanscript import transliterate as indic_transliterate
from hangul_romanize import Transliter  # For Korean
from hangul_romanize.rule import academic
import pykakasi  # For Japanese Romaji


# Define a transliteration function for each language
def transliterate(input_text, language):
    if language == "chinese":
        return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.TONE3))
    elif language == "japanese":
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")  # Hiragana to Romaji
        kakasi.setMode("K", "a")  # Katakana to Romaji
        kakasi.setMode("J", "a")  # Kanji to Romaji
        converter = kakasi.getConverter()
        return converter.do(input_text)
    elif language == "russian":
        # Use a library like transliterate for Cyrillic to Latin
        import transliterate
        return transliterate.translit(input_text, 'ru', reversed=True)
    elif language == "hindi":
        # Use a library like indic-transliteration for Hindi to Latin
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        return transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
    # elif language == "arabic":
    #     # Use the transliterate library for Arabic
    #     ar2bw = CharMapper.builtin_mapper('ar2bw')
    #     sent_bw = ar2bw(input_text)
        
    #     # Define a custom mapping from Buckwalter to Phonetic
    #     bw2phonetic = {
    #         '*': 'dh', 'h': 'h', 'b': 'b', 't': 't',
    #         '<': 'ʿ', 'l': 'l', 'Y': 'á', 'A': 'a',
    #         'm': 'm', 'k': 'k', 'p': 'p', '.': '.'
    #     }
        
    #     # Convert Buckwalter to Phonetic
    #     return ''.join([bw2phonetic.get(char, char) for char in sent_bw])    
    elif language == "korean":
        # Use a library like hangul-romanize for Korean to Latin
        transliter = Transliter(rule=academic)  # Use the Transliter class
        return transliter.translit(input_text)  # Correct method for transliteration
    else:
        return input_text  # For languages without a need for transliteration

# Remove English lines from content
def remove_latin(content, language):
    print(f"Removing English lines from {language} content")
    language_ranges = {
        'chinese': r'[\u4e00-\u9fff]',
        'russian': r'[\u0400-\u04FF]',
        'hindi': r'[\u0900-\u097F]',
        'japanese': r'[\u3040-\u30FF\u4E00-\u9FFF]',
        'korean': r'[\uAC00-\uD7AF]',
        'arabic': r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]',  # Added Arabic
    }
    
    target_pattern = language_ranges.get(language, r'[\u4e00-\u9fff]')  # Default to Chinese
    english_pattern = re.compile(r'^[A-Za-z0-9\s,.!?;:()\'\"-]+$', re.MULTILINE)
    target_language_pattern = re.compile(target_pattern)
    
    lines = content.splitlines()
    filtered_lines = [
        line for line in lines
        # if not english_pattern.match(line) or target_language_pattern.search(line)
        if target_language_pattern.search(line)  # Keep only lines with the target language script
    ]
    
    return '\n'.join(filtered_lines)

# Create EPUB files with Markdown content
def generate_epub(content, output_file):
    # Using Pandoc or Calibre to generate EPUB
    temp_file = "temp.md"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
    pandoc_args = ["pandoc", "-o", output_file, "-t", "epub"]
    print(f"Running Pandoc command: {' '.join(pandoc_args)}")
    try:
        # Run the pandoc command
        result = subprocess.run(pandoc_args, capture_output=True, text=True)
        
        # Print the output and errors (if any)
        if result.stdout:
            print("Pandoc Output:", result.stdout)
        if result.stderr:
            print("Pandoc Error:", result.stderr)
        
        # Check if the command was successful
        if result.returncode == 0:
            print(f"EPUB successfully generated: {output_file}")
        else:
            print(f"Failed to generate EPUB. Return code: {result.returncode}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the temporary file
        import os
        if os.path.exists(temp_file):
            os.remove(temp_file)

# Pipeline for processing the file and generating two versions
def process_file(input_file, language, enable_transliteration):
    print(f"Processing {input_file} for {language} with transliteration: {enable_transliteration}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Remove English lines (keeping only the target language translation)
    content_no_english = remove_latin(content, language)
    
     # Determine output filenames
    base_name = os.path.splitext(input_filename)[0]
    output_filename_version1 = f"{base_name}-{language}.epub"
    
    # Step 4: Generate Version 2 (only Input Language characters for Pleco/Voice Reader)
    print(f"Generating {output_filename_version1}")
    generate_epub(content_no_english, output_filename_version1)
    
    # Want transliteration for the target language?
    if(enable_transliteration):   
        output_filename_version2 = f"{base_name}-{language}-trans.epub"

        # Step 2: Add Transliteration (Pinyin, Romaji, etc.)
        print(f"Generating {output_filename_version2} with transliteration")    
        content_with_transliteration = ""
        for line in content_no_english.splitlines():
            if re.search(r'[\u4e00-\u9fff\u0400-\u04FF\u0900-\u097F\u3040-\u30FF\uAC00-\uD7AF]', line):
                transliteration_line = transliterate(line, language)
                print(transliteration_line)
                content_with_transliteration += f"{transliteration_line}\n{line}\n"
            else:
                content_with_transliteration += f"{line}\n"
        
        # Step 3: Generate Version 1 (English + Transliteration + Input Language)
        generate_epub(content_with_transliteration, output_filename_version2)
    

# Pipeline for processing the file and generating two versions
# Step 1: Write the Markdown File (input.md)
# Step 2: Convert to EPUB with Calibre (English + Target_Language)
# Step 3: Convert EPUB back to Markdown with Pandoc
    # pandoc -f epub -t markdown -o output.md input.epub
# Step 4: Run the Python script to generate two versions of the EPUB
    # python md2ebookTransliteration.py

# Example Usage
# process_file('/home/zaya/Downloads/input.md', 'chinese')  # Pass the language as 'chinese', 'japanese', etc.

input_filename = '/home/zaya/Documents/Ebooks/Transliteration/test.md'
target_language = 'chinese'  # Russian target language (can be dynamically set)

process_file(input_filename, target_language, enable_transliteration=True)
