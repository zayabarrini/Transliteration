# Test everything
# --------------------- Subtitles

## Only Transliteration
input_dir = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles"
target_languages = ["de", "zh-ch"]  

# input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Gosford-de-(ja).srt"
# target_language = "japanese"
# input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Fargo-de-(ch).srt"
# target_language = "chinese"
# input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Ghandi-ru-(ar).srt"
# target_language = "arabic"
# input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Little-hi.srt"
# target_language = "hindi"   

# I'm testing transliteration here for japanese, chinese, arabic, hindi, korean, russian
from transliteration.sub2translate_literate import process_csv, process_zip
csv_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles/trans.csv"
process_csv(csv_file)

input_zip_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles/transliteration.zip"
process_zip(input_zip_path)
# expect = correct transliteration for each language, correct formating

# from subMultilingualVersions import process_multilingual_srt
# for filename in os.listdir(input_dir):
#     if filename.lower().endswith('.srt'):
#         filepath = os.path.join(input_dir, filename)
#         process_multilingual_srt(filepath, target_languages, True)

# I'm testing transliteration here for japanese, chinese, arabic, hindi
## Zip File
input_zip_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles/subtitles.zip"
target_languages = ["de", "zh-ch"]  # Your target languages
from subtitles.zip2zip import process_zip_of_srts
process_zip_of_srts(input_zip_path, target_languages)

# expect = unzip, unzip, correct translation + transliteration for each language and combination, correct formating 

# --------------------- Ebook: Transliteration
input_folder_ebooks = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks"
from transliteration.epubVersions import process_folder
process_folder(input_folder_ebooks)

# expect = ebook correct transliteration for each language, files: orig, db, no, trans + correct formating 

# --------------------- Ebook: Split Sentences
input_folder = '/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks/ebook.epub'  # Update this path to your folder containing EPUB files
output_folder = '/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks/Output' 

from transliteration.epubSplitProcessor import process_epub_folder
process_epub_folder(input_folder, output_folder)

# expect = longer sentences split into smaller ones, correct formating

# --------------------- Webpage: Transliteration
from web.webflask import _main_
# run main.py, which is a Flask app
# pass some initial string = "I'm just testing"
_main_()

# expect = run correctly + correct transliteration for each language, correct formating
