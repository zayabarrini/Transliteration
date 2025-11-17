Build: Success, Handle Fail
Files: main-test.md, main-test.srt

Tests for:

1. EbookMenu:

- Split
- Remove Original
- Trasliterate Multilingual
- Merge
- MergeSimple

2. SubtitlesMenu:

- Movies
- Series
- Transliteration Multilingual

3. WebPagesVersion:

- ChineseTranslator
- color-coded-chinese
- color-coded-japanese-MeCab
- color-coded-japanese
- Hindi
- Japanese
- translator
- translator2language
- translator2transliteration

# For Epubs:

Directory: current Directory
run from terminal epubManager runs and present the EbookMenu
Select an option to do:

I usually do cd transliteration
pipenv shell
python3 -m transliteration.epubVersions or .epubSplitProcessor or .epubSplitProcessor or .epubMergeFolder or .epubMergeStack

What I want:
From working directory, just run: epubManager
Then select the option that I want

EbookMenu:

- Split
- Remove Original
- Trasliterate Multilingual
- Merge
- MergeSimple

from epubVersions.py:
process_folder_remove_original("/home/zaya/Downloads/Zayas/ZayasBooks/t")
process_folder_transliterate_epub(epub_path, language)

from epubSplitProcessor.py:
process_epub_folder(input_folder, output_folder)

default: file_patterns = ['*-db-*.epub']
from epubMergeFolder.py:
epub_paths, output_path, languages, merge_order = prep_epubs_by_pattern(
folder_path=folder_path,
file_patterns=file_patterns,
merge_order=['ch', 'de', 'ru'], # Use 'ch' here
output_suffix="ml"
)
merge_multiple_epubs(epub_paths, output_path, languages, merge_order)

from epubMergeStack.py:
prep_and_merge_simple(
folder_path=folder_path,
file_patterns=file_patterns,
merge_order=default_order,
output_suffix="ml-simple"
)

Let's build a default merge_order, take the epub_languages available (There can 2 or n languages involved) and based on the default merge_order builds a usable merge_order
I've being using the following order:
ru, de, en, ch, ar, hi, then we can have latin languages, asian languages, then the rest
Ebook languages that I've worked with:
['ar','ch','de','es','fr','el','he','hi','id','it','ja','ko','la','pl','pt','ru','sw','tr']

For Transliteration
SUPPORTED_LANGUAGES = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]
get_language_from_epub, detect_language_from_filename
