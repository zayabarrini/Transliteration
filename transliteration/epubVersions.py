from transliteration.epubTransliteration import SUPPORTED_LANGUAGES
from transliteration.epub_no_original import process_epub as remove_original
from transliteration.epubTransliteration import process_epub as transliterate_epub
import os

def process_folder(folder_path: str):
    for filename in os.listdir(folder_path):
        if filename.endswith('.epub'):
            epub_path = os.path.join(folder_path, filename)
            language = filename.split('-')[0].lower()
            
            # Option 1: Remove original text
            epub_path_no_original = remove_original(epub_path)

            # if language in SUPPORTED_LANGUAGES:
            #     # Option 2: Transliterate
            #     transliterate_epub(epub_path)
                # Option : Transliterate no_original
                # transliterate_epub(epub_path_no_original)


if __name__ == "__main__":
    process_folder("/home/zaya/Documents/Ebooks/Revistas/Freudiana/db/du")
    # process_folder("/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks")
