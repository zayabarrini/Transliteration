import os
import shutil
import sys
from transliteration.epubManagement import (
    extract_epub,
    create_epub,
    find_text_folder,
    get_xhtml_files)

# SUPPORTED_LANGUAGES = ["japanese", "korean", "chinese", "hindi", "arabic"]
SUPPORTED_LANGUAGES = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]

from transliteration.html2transliteration import process_folder
from transliteration.add_metadata_and_cover import add_metadata_and_cover

def get_language_from_filename(filename: str) -> str:
    """Extracts language from filename (e.g., 'hindi-book.epub' -> 'hindi')."""
    return filename.split('-')[0].lower()

def verify_language(language: str) -> None:
    """Validates if the language is supported."""
    if language not in SUPPORTED_LANGUAGES:
        print(f"Error: Unsupported language '{language}'. Skipping file.")
        print(f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}")
        sys.exit(1)

def process_epub(epub_path: str) -> str:
    """
    Processes an EPUB for transliteration:
    1. Extracts EPUB
    2. Transliterates text in HTML files
    3. Adds metadata/cover
    4. Repackages into new EPUB
    Returns path to the generated EPUB.
    """
    base_name = os.path.basename(epub_path).replace('.epub', '')
    language = get_language_from_filename(base_name)
    verify_language(language)

    extract_to = epub_path.replace('.epub', '_temp')
    output_path = epub_path.replace('.epub', '_transliterated.epub')

    try:
        # Extract EPUB
        extract_epub(epub_path, extract_to)

        # Process HTML files (transliteration)
        text_folder = find_text_folder(extract_to)
        process_folder(
            text_folder, 
            language, 
            enable_transliteration=True, 
            epub_folder=extract_to
        )

        # Add metadata and cover
        add_metadata_and_cover(extract_to, base_name + '_transliterated', language)

        # Repackage
        create_epub(extract_to, output_path)
        return output_path

    finally:
        # Cleanup
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)

if __name__ == "__main__":
    # Example CLI usage
    if len(sys.argv) == 2:
        input_epub = sys.argv[1]
        output_epub = process_epub(input_epub)
        print(f"Generated transliterated EPUB: {output_epub}")
    else:
        # Batch processing (optional)
        folder_path = '/home/zaya/Documents/Ebooks/trans'
        for filename in os.listdir(folder_path):
            if filename.endswith('.epub'):
                epub_path = os.path.join(folder_path, filename)
                process_epub(epub_path)