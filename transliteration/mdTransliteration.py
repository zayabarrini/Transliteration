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

# def format_transliteration(text):
#     # Add spaces after commas and periods
#     text = re.sub(r'([,.])', r'\1 ', text)

#     # Add spaces around hyphens
#     text = re.sub(r'([a-zA-Z])-([a-zA-Z])', r'\1 - \2', text)

#     # Break long sentences into smaller chunks
#     sentences = re.split(r'(?<=[。！？])', text)
#     formatted_text = '\n'.join([s.strip() for s in sentences if s.strip()])

#     return formatted_text


def is_latin(token):
    """Check if a token contains only Latin characters."""
    return bool(re.match(r"^[A-Za-z0-9\s\W_]+$", token))


def tokenize_text(text):
    """Tokenize the text into words and symbols."""
    # Use a regex to split the text into words and symbols
    tokens = re.findall(r"\w+|\W+", text)
    return tokens


def add_furigana(text, transliteration, language):
    # Tokenize the text into words and symbols
    tokens = tokenize_text(text)

    # Split transliteration into individual syllables or words
    if language == "japanese":
        trans_words = transliteration  # transliteration is already a list of syllables
    else:
        trans_words = transliteration.split()

    # Align words with their transliterations
    furigana_text = []
    trans_index = 0

    for token in tokens:
        if is_latin(token):
            # If the token is Latin (e.g., code syntax, English), append it as-is
            furigana_text.append(token)
        elif re.match(r"\W+", token):
            # If the token is a symbol (e.g., punctuation, brackets), append it as-is
            furigana_text.append(token)
        else:
            # Token is a non-Latin word (e.g., Chinese, Japanese, etc.)
            if language == "chinese":
                # Use jieba to segment the Chinese text
                segmented_words = list(jieba.cut(token))
                # Each Chinese character corresponds to one pinyin syllable
                for word in segmented_words:
                    num_syllables = len(word)
                    # Get the corresponding pinyin syllables
                    pinyin = " ".join(trans_words[trans_index : trans_index + num_syllables])
                    trans_index += num_syllables
                    # Add <ruby> tags
                    furigana_text.append(f"<ruby>{word}<rt>{pinyin}</rt></ruby>")

            elif language == "japanese":
                segmented_chars = list(token)
                # Treat each character as a separate unit for furigana
                for char in segmented_chars:
                    # Get the corresponding Romaji syllable
                    if trans_index < len(trans_words):
                        romaji = trans_words[trans_index]
                        trans_index += 1
                        # Add <ruby> tags for each character
                        furigana_text.append(f"<ruby>{char}<rt>{romaji}</rt></ruby>")
                        print(f"char: {char}, romaji: {romaji}")
                    else:
                        # If not enough syllables, append the character without transliteration
                        furigana_text.append(char)

            elif language == "korean":
                # Treat each Hangul syllable block as a separate unit for furigana
                for char in token:
                    # Get the corresponding Romanization
                    romanization = trans_words[trans_index]
                    trans_index += 1
                    # Add <ruby> tags for each Hangul syllable block
                    furigana_text.append(f"<ruby>{char}<rt>{romanization}</rt></ruby>")
            elif language in ["hindi", "arabic", "russian"]:
                if trans_index < len(trans_words):
                    # Treat each word as a single unit for transliteration
                    translit = trans_words[trans_index]
                    trans_index += 1
                    # Add <ruby> tags for the entire word
                    furigana_text.append(f"<ruby>{token}<rt>{translit}</rt></ruby>")
                else:
                    # If not enough syllables, append the character without transliteration
                    furigana_text.append(token)
            else:
                # Default behavior for other languages
                furigana_text.append(token)

    return "".join(furigana_text)


# def add_furigana(text, transliteration, language):
#     # Tokenize the text into words and symbols
#     tokens = tokenize_text(text)

#     # Split transliteration into individual pinyin syllables
#     trans_words = transliteration.split()

#     # Align Chinese words with pinyin syllables
#     furigana_text = []
#     trans_index = 0

#     for token in tokens:
#         if is_latin(token):
#             # If the token is Latin (e.g., code syntax, English), append it as-is
#             furigana_text.append(token)
#         elif re.match(r'\W+', token):
#             # If the token is a symbol (e.g., punctuation, brackets), append it as-is
#             furigana_text.append(token)
#         else:
#             # Token is a non-Latin word (e.g., Chinese)
#             # Use jieba to segment the Chinese text
#             if language == "chinese":
#                 segmented_words = list(jieba.cut(token))
#             else:
#                 segmented_words = [token]  # Default to treating the token as a single word

#             # Process each segmented word
#             for word in segmented_words:
#                 # Count the number of pinyin syllables for the current word
#                 # Assumes each Chinese character corresponds to one pinyin syllable
#                 num_syllables = len(word)

#                 # Get the corresponding pinyin syllables
#                 pinyin = ' '.join(trans_words[trans_index:trans_index + num_syllables])
#                 trans_index += num_syllables

#                 # Add <ruby> tags
#                 furigana_text.append(f"<ruby>{word}<rt>{pinyin}</rt></ruby>")

#     return ''.join(furigana_text)

# Group 5 words into chunks
# def add_furigana(text, transliteration, language):
#     # Tokenize the Chinese text into words
#     if language == "chinese":
#         words = list(jieba.cut(text))  # Use jieba for Chinese word segmentation
#     else:
#         words = text.split()  # Default split for other languages

#     # Split transliteration into individual pinyin syllables
#     trans_words = transliteration.split()

#     # Group words and pinyin into chunks
#     furigana_text = []
#     trans_index = 0
#     chunk_size = 5  # Number of words per chunk

#     for i in range(0, len(words), chunk_size):
#         chunk_words = words[i:i + chunk_size]
#         chunk_pinyin = trans_words[trans_index:trans_index + len(chunk_words)]
#         trans_index += len(chunk_words)

#         # Combine chunk into <ruby> tags
#         furigana_text.append(f"<ruby>{''.join(chunk_words)}<rt>&#8203;{' '.join(chunk_pinyin)}&#8203;</rt></ruby>")

#     return ' '.join(furigana_text)


# Define a transliteration function for each language
def transliterate(input_text, language):
    if language == "chinese":
        return " ".join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.TONE3))
    elif language == "japanese":
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")  # Hiragana to Romaji
        kakasi.setMode("K", "a")  # Katakana to Romaji
        kakasi.setMode("J", "a")  # Kanji to Romaji
        converter = kakasi.getConverter()
        result = converter.do(input_text)
        print(result.split())
        return result.split()
        # return format_transliteration(converter.do(input_text))

    elif language == "russian":
        # Use a library like transliterate for Cyrillic to Latin
        import transliterate

        return transliterate.translit(input_text, "ru", reversed=True)
    elif language == "hindi":
        # Use a library like indic-transliteration for Hindi to Latin
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        result = transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
        print(result)
        return result
    elif language == "arabic":
        return custom_utf82latin(input_text)
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
        "chinese": r"[\u4e00-\u9fff]",
        "russian": r"[\u0400-\u04FF]",
        "hindi": r"[\u0900-\u097F]",
        "japanese": r"[\u3040-\u30FF\u4E00-\u9FFF]",
        "korean": r"[\uAC00-\uD7AF]",
        "arabic": r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]",  # Added Arabic
    }

    target_pattern = language_ranges.get(language, r"[\u4e00-\u9fff]")  # Default to Chinese
    english_pattern = re.compile(r"^[A-Za-z0-9\s,.!?;:()\'\"-]+$", re.MULTILINE)
    target_language_pattern = re.compile(target_pattern)

    lines = content.splitlines()
    filtered_lines = [
        line
        for line in lines
        if target_language_pattern.search(line)  # Keep only lines with the target language script
    ]
    return "\n".join(filtered_lines)


# Save content as Markdown
def save_markdown(content, output_file):
    print(f"Saving Markdown file: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def is_header(line):
    """Check if the line is a Markdown header."""
    return re.match(r"^#+\s*", line) is not None


# Pipeline for processing the file and generating two versions
def process_file(input_file, language, enable_transliteration):
    print(f"Processing {input_file} for {language} with transliteration: {enable_transliteration}")
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Remove English lines (keeping only the target language translation)
    # content_no_english = remove_latin(content, language)

    # Determine output filenames
    base_name = os.path.splitext(input_filename)[0]
    # output_filename_version1 = f"{base_name}-{language}.md"

    # Step 4: Save Version 1 (only Input Language characters)
    # print(f"Saving {output_filename_version1}")
    # save_markdown(content_no_english, output_filename_version1)

    # Want transliteration for the target language?
    if enable_transliteration:
        output_filename_version2 = f"{base_name}-{language}-trans.md"

        # Step 2: Add Transliteration (Pinyin, Romaji, etc.)
        print(f"Saving {output_filename_version2} with transliteration")
        content_with_transliteration = ""
        for line in content.splitlines():  # Use the original content (including Latin lines)
            if re.search(
                r"[\u4e00-\u9fff\u0400-\u04FF\u0900-\u097F\u3040-\u30FF\uAC00-\uD7AF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]",
                line,
            ):
                # If the line contains target language script, add transliteration
                if is_header(line):
                    # If it's a header, return the line as-is
                    content_with_transliteration += f"{line}\n\n"
                else:
                    # If it's not a header, transliterate and format the line
                    transliteration_line = transliterate(line, language)
                    formatted_line = add_furigana(line, transliteration_line, language)
                    content_with_transliteration += f"{formatted_line}\n\n"
                # print(transliteration_line)
                # content_with_transliteration += f"{formatted_line}\n\n{line}\n\n"
            else:
                # If the line is Latin (e.g., English), keep it as is
                content_with_transliteration += f"{line}\n\n"

        # Step 3: Save Version 2 (Original + Transliteration + Latin lines)
        save_markdown(content_with_transliteration, output_filename_version2)


# Example Usage
# input_filename = '/home/zaya/Documents/Ebooks/Japanese-Favorite-Movies-3.0.md'
# input_filename = '/home/zaya/Documents/Ebooks/test-japanese.md'
# input_filename = '/home/zaya/Documents/Ebooks/Favorite-movies-3-hi-hindi.md'
# # input_filename = '/home/zaya/Documents/Ebooks/test.md'
# target_language = 'hindi'  # Target language (e.g., 'chinese', 'japanese', etc.)

# process_file(input_filename, target_language, enable_transliteration=True)

input_filename = "/home/zaya/Documents/Gitrepos/cinema/Subtitles/Chinese-A-brighter-summer-day.srt"
target_language = "chinese"
process_file(input_filename, target_language, enable_transliteration=True)

# input_folder = '/home/zaya/Documents/Ebooks'  # Update this path to your folder containing HTML files
# target_language = 'japanese'  # Target language (e.g., 'chinese', 'japanese', etc.)

# # Iterate over all HTML files in the folder
# for filename in os.listdir(input_folder):
#     if filename.endswith('.html'):
#         input_filename = os.path.join(input_folder, filename)
#         print(f"Processing file: {input_filename}")
#         process_file(input_filename, target_language, enable_transliteration=True)
