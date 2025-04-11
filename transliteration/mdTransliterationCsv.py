import re
import subprocess
import pypinyin  # For Chinese Pinyin
import os
from hangul_romanize import Transliter  # For Korean
from hangul_romanize.rule import academic
from indic_transliteration import sanscript  # For Hindi
from indic_transliteration.sanscript import transliterate as indic_transliterate
import pykakasi  # For Japanese Romaji
from pyarabic.trans import custom_utf82latin  # For Arabic transliteration
import jieba
import csv
import random

def format_transliteration(text):
    # Add spaces after commas and periods
    text = re.sub(r'([,.])', r'\1 ', text)
    
    # Add spaces around hyphens
    text = re.sub(r'([a-zA-Z])-([a-zA-Z])', r'\1 - \2', text)
    
    # Break long sentences into smaller chunks
    sentences = re.split(r'(?<=[。！？])', text)
    formatted_text = '\n'.join([s.strip() for s in sentences if s.strip()])
    
    return formatted_text

def is_latin(token):
    """Check if a token contains only Latin characters."""
    return bool(re.match(r'^[A-Za-z0-9\s\W_]+$', token))

# Function to tokenize text into words and symbols
def tokenize_text(text):
    # Tokenize the text into words and non-words (punctuation, spaces, etc.)
    tokens = re.findall(r'\w+|\W+', text)
    
    # Initialize a list to store the corrected tokens
    corrected_tokens = []
    
    for token in tokens:
        if re.match(r'\W+', token):  # Check if the token is punctuation
            if corrected_tokens:  # If there is a previous word, append punctuation to it
                corrected_tokens[-1] += token
            else:  # If no previous word exists, add the punctuation as a standalone token
                corrected_tokens.append(token)
        else:  # If the token is a word, add it to the list
            corrected_tokens.append(token)
    
    return corrected_tokens

def append_punctuation_to_previous_word(segmented_words):
    # List of punctuation marks to handle
    punctuation_marks = ['。', '，', '！', '？', '、', '「', '」', '『', '』', '（', '）', '《', '》', '.', ',', '!', '?']
    
    # Initialize a new list to store the corrected tokens
    corrected_words = []
    
    for word in segmented_words:
        if word in punctuation_marks:  # Check if the word is punctuation
            if corrected_words:  # If there is a previous word, append punctuation to it
                corrected_words[-1] += word
            else:  # If no previous word exists, add the punctuation as a standalone token
                corrected_words.append(word)
        else:  # If the word is not punctuation, add it to the list
            corrected_words.append(word)
    
    return corrected_words

# Function to add furigana to text
def add_furigana(text, transliteration, language):
    # tokens = text
    exclude_chars = [' ', '.', ',', '!', '?', '。', '，', '！', '？', '、', '「', '」', '『', '』', '（', '）', '《', '》']
    if language == "japanese":
        trans_words = [item['hepburn'] for item in transliteration]
    elif language == "korean":
        trans_words = transliteration  # Use the list of tuples directly
    else:
        trans_words = transliteration.split()
    
    furigana_text = []
    trans_index = 0
    
    if language == "japanese":
        segmented_chars = [item['orig'] for item in transliteration]
        # segmented_chars = list(token)
        for char in segmented_chars:
            if trans_index < len(trans_words):
                romaji = trans_words[trans_index]
                trans_index += 1
                if char in exclude_chars:
                    furigana_text.append(char)
                else:
                    furigana_text.append(f"<ruby>{char}<rt>{romaji}</rt></ruby>")
    elif language == "korean":
        # Process each character in the token
        for [char, trans] in trans_words:
            if char in exclude_chars:
                furigana_text.append(char)
            else:
                furigana_text.append(f"<ruby>{char}<rt>{trans}</rt></ruby>")
    elif language in ["hindi", "arabic", "russian"]:
        segmented_words = text.split()
        for word in segmented_words:
            if trans_index < len(trans_words):
                translit = trans_words[trans_index]
                trans_index += 1
                furigana_text.append(f"<ruby>{word}<rt>{translit}</rt></ruby>")
            else:
                furigana_text.append(f"<ruby>{word}</ruby>")
    # else:
    #     furigana_text.append(f"<ruby>{token}</ruby>")
    
    if language == "chinese":
        tokens = tokenize_text(text)
        for token in tokens:
            if is_latin(token):
                furigana_text.append(f"<ruby>{token}</ruby>")
            # elif re.match(r'\W+', token):
            #     Append punctuation to the previous word
            #     if furigana_text:
            #         furigana_text[-1] = furigana_text[-1] + token
            #     else:
            #         furigana_text.append(token)
            # print(token)
            else:
                # Handle Chinese text
                segmented_words = list(jieba.cut(token))
                print(segmented_words)
                # add punctuation to the previous word
                corrected_words = append_punctuation_to_previous_word(segmented_words)
 
                for word in corrected_words:
                    num_syllables = len(word)
                    pinyin = ' '.join(trans_words[trans_index:trans_index + num_syllables])
                    # remove punctuation from pin yin
                    pinyin = re.sub(r'[^\w\s]', '', pinyin)
                    trans_index += num_syllables
                    furigana_text.append(f"<ruby>{word}<rt>{pinyin}</rt></ruby>")
    return ''.join(furigana_text)

# Function to transliterate text
def transliterate(input_text, language):
    if language == "chinese":
        return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.TONE3))
    elif language == "japanese":
        kakasi = pykakasi.kakasi()
        # kakasi.setMode("H", "a")
        # kakasi.setMode("K", "a")
        # kakasi.setMode("J", "a")
        # converter = kakasi.getConverter()
        # result = converter.do(input_text)
        result = kakasi.convert(input_text)
        return result
    elif language == "russian":
        import transliterate
        return transliterate.translit(input_text, 'ru', reversed=True)
    elif language == "hindi":
        result = indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return result
    elif language == "arabic":
        return custom_utf82latin(input_text)
    elif language == "korean":
        transliter = Transliter(rule=academic)
        result = transliter.translit(input_text)
        return result
    else:
        return input_text
    
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
        if target_language_pattern.search(line)  # Keep only lines with the target language script
    ]  
    return '\n'.join(filtered_lines)

# Save content as Markdown
def save_markdown(content, output_file):
    print(f"Saving Markdown file: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

def is_header(line):
    """Check if the line is a Markdown header."""
    return re.match(r'^#+\s*', line) is not None

def generate_epub(content, output_file, css_file=None, metadata=None, cover_image=None):
    # Using Pandoc to generate EPUB
    temp_file = "temp.md"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Build Pandoc command
    pandoc_args = ["pandoc", "-o", output_file, "-t", "epub", temp_file]
    
    # Add CSS file if provided
    if css_file:
        pandoc_args.extend(["--css", css_file])
    
    # Add metadata if provided
    if metadata:
        for key, value in metadata.items():
            pandoc_args.extend(["--metadata", f"{key}={value}"])
    
    # Add cover image if provided
    if cover_image:
        pandoc_args.extend(["--epub-cover-image", cover_image])
    
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
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
def process_file(input_filename):
    with open(input_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            input_md_file = row['input']  # Path to the input Markdown file
            language = row['target_language']  # Target language
            enable_transliteration = True  # Enable transliteration by default

            if enable_transliteration:
                # Read the content of the input Markdown file
                with open(input_md_file, mode='r', encoding='utf-8') as md_file:
                    input_text = md_file.read()

                # Extract base_name from the input Markdown file path
                base_name = os.path.splitext(os.path.basename(input_md_file))[0]
                print(f"Processing {input_md_file} for {language}")

                # Generate output Markdown file name
                output_filename_version2 = f"{base_name}-{language}-trans.md"
                print(f"Saving {output_filename_version2} with transliteration")

                # Process each line of the input text
                content_with_transliteration = ""
                for line in input_text.splitlines():  # Process each line
                    if re.search(r'[\u4e00-\u9fff\u0400-\u04FF\u0900-\u097F\u3040-\u30FF\uAC00-\uD7AF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', line):
                        # If the line contains target language script, add transliteration
                        if is_header(line):
                            # If it's a header, return the line as-is
                            content_with_transliteration += f"{line}\n\n"
                        else:
                            # If it's not a header, transliterate and format the line
                            transliteration_line = transliterate(line, language)
                            formatted_line = add_furigana(line, transliteration_line, language)
                            content_with_transliteration += f"{formatted_line}\n\n"
                    else:
                        # If the line is Latin (e.g., English), keep it as is
                        content_with_transliteration += f"{line}\n\n"

                # Save the processed Markdown content
                save_markdown(content_with_transliteration, output_filename_version2)

                # Generate EPUB file name
                output_epub_file = f"{base_name}-{language}-trans.epub"

                # Set CSS file based on language
                if language == "japanese" or language == "chinese":
                    css_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/styles-ch-jp.css"
                elif language == "arabic":
                    css_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/styles-ar.css"
                else:
                    css_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/styles.css"

                # Generate random cover image path
                random_number = random.randint(1, 211)
                cover_image = f"/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_number}.png"

                # Generate EPUB with metadata and cover image
                generate_epub(
                    content_with_transliteration,
                    output_epub_file,
                    css_file=css_file,
                    metadata={
                        "title": base_name,
                        "author": "Zaya Barrini",
                        "website": "https://zayabarrini.vercel.app/",
                    },
                    cover_image=cover_image
                )

# Example Usage
# input_filename = '/home/zaya/Documents/Ebooks/Russian-Favorite-Movies-3.0.md'
# # input_filename = '/home/zaya/Documents/Ebooks/Chinese-Favorite-Movies-3.0-chinese.md'
# # input_filename = '/home/zaya/Documents/Ebooks/test.md'
# target_language = 'russian'  # Target language (e.g., 'chinese', 'japanese', etc.)

# process_file(input_filename, target_language, enable_transliteration=True)

input_folder = '/home/zaya/Downloads/transliteration_files.csv'
process_file(input_folder)