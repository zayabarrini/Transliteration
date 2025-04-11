import os
import zipfile
import shutil
import sys
from lxml import etree

def extract_epub(epub_path: str, extract_to: str) -> None:
    """Extracts EPUB contents to a directory."""
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def create_epub(folder_path: str, epub_path: str) -> None:
    """Creates an EPUB from a directory."""
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def find_text_folder(extract_to: str) -> str:
    """Locates the folder containing HTML/XML content files."""
    for path in [
        os.path.join(extract_to, 'OEBPS', 'Text'),
        os.path.join(extract_to, 'EPUB', 'text'),
        os.path.join(extract_to, 'text')
    ]:
        if os.path.exists(path):
            return path
    default_path = os.path.join(extract_to, 'OEBPS', 'Text')
    os.makedirs(default_path, exist_ok=True)
    return default_path

def get_xhtml_files(text_folder: str) -> list:
    """Returns paths to all XHTML/HTML files in the text folder."""
    return [
        os.path.join(text_folder, f) 
        for f in os.listdir(text_folder) 
        if f.endswith(('.xhtml', '.html'))
    ]