import os
import zipfile
import random
import shutil
from html2transliteration import process_folder
from add_metadata_and_cover import add_metadata_and_cover
import sys  # For exiting the script

# List of supported languages
SUPPORTED_LANGUAGES = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]

def extract_epub(epub_path, extract_to):
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def create_epub(folder_path, epub_path):
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def get_language_from_filename(filename):
    return filename.split('-')[0].lower()

def verify_language(language):
    """
    Verifies if the language is supported.
    If not, prints a warning and exits the script.
    """
    if language not in SUPPORTED_LANGUAGES:
        print(f"Warning: Unsupported language '{language}'. File will be skipped.")
        print(f"Supported languages are: {', '.join(SUPPORTED_LANGUAGES)}")
        sys.exit(1)

def find_text_folder(extract_to):
    """Locate the folder containing HTML content files"""
    # Check common EPUB structures
    for path in [
        os.path.join(extract_to, 'OEBPS', 'Text'),
        os.path.join(extract_to, 'EPUB', 'text'),
        os.path.join(extract_to, 'OEBPS', 'text'),
        os.path.join(extract_to, 'EPUB', 'Text')
    ]:
        if os.path.exists(path):
            print(f"Found HTML files in: {path}")
            return path
    
    # Create default folder if none found
    default_path = os.path.join(extract_to, 'OEBPS', 'Text')
    os.makedirs(default_path, exist_ok=True)
    print(f"Created default folder: {default_path}")
    return default_path


def process_epub(epub_path):
    base_name = os.path.basename(epub_path).replace('.epub', '')
    language = get_language_from_filename(base_name)
    verify_language(language)

    # css_file = get_css_file(language)

    # Rename epub to zip and extract
    zip_path = epub_path.replace('.epub', '.zip')
    os.rename(epub_path, zip_path)
    extract_to = zip_path.replace('.zip', '')
    epub_folder = extract_to
    extract_epub(zip_path, extract_to)
    
    
    try:
        # Process HTML files
        text_folder = find_text_folder(extract_to)
        process_folder(text_folder, language, enable_transliteration=True, epub_folder=epub_folder)

        # Add metadata and cover image
        add_metadata_and_cover(extract_to, base_name, language)

        # Repackage into EPUB
        new_epub_path = epub_path.replace('.epub', '_transliterated.epub')
        create_epub(extract_to, new_epub_path)
        
    finally:
        # Clean up
        os.rename(zip_path, epub_path)
        shutil.rmtree(extract_to)

if __name__ == "__main__":
    folder_path = '/home/zaya/Documents/Ebooks/trans'  # Update this path to your folder containing EPUB files
    for filename in os.listdir(folder_path):
        if filename.endswith('.epub'):
            epub_path = os.path.join(folder_path, filename)
            process_epub(epub_path)