import os
import zipfile
from lxml import etree

def extract_epub(epub_path: str, extract_to: str) -> None:
    """Extracts EPUB contents to a directory."""
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def create_epub(folder_path: str, epub_path: str) -> None:
    """Creates an EPUB from a directory with proper EPUB structure."""
    # EPUB requires mimetype to be first and uncompressed
    with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add mimetype first and uncompressed
        mimetype_path = os.path.join(folder_path, 'mimetype')
        if os.path.exists(mimetype_path):
            zipf.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
        
        # Add remaining files
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file == 'mimetype':
                    continue  # Already added
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def find_text_folder(extract_to: str) -> str:
    """Locates the folder containing HTML/XML content files."""
    # Check common EPUB3 structure first
    common_paths = [
        os.path.join(extract_to, 'EPUB', 'text'),  # Most common in EPUB3
        os.path.join(extract_to, 'OEBPS', 'Text'),  # Some older EPUBs
        os.path.join(extract_to, 'text'),           # Some simple EPUBs
        os.path.join(extract_to, 'Text'),          # Alternate capitalization
        os.path.join(extract_to, 'EPUB'),          # Sometimes files are directly in EPUB
        extract_to                                 # Sometimes files are in root
    ]
    
    # Check each possible path
    for path in common_paths:
        if os.path.exists(path):
            # Verify it contains XHTML/HTML files
            if any(f.lower().endswith(('.xhtml', '.html')) for f in os.listdir(path)):
                return path
            # If no files found but directory exists, check subdirectories
            for root, _, files in os.walk(path):
                if any(f.lower().endswith(('.xhtml', '.html')) for f in files):
                    return root
    
    # If nothing found, try to find any XHTML/HTML files in the extraction directory
    for root, _, files in os.walk(extract_to):
        for file in files:
            if file.lower().endswith(('.xhtml', '.html')):
                return root
    
    # Default fallback (create directory if needed)
    default_path = os.path.join(extract_to, 'EPUB', 'text')
    os.makedirs(default_path, exist_ok=True)
    return default_path

def get_xhtml_files(text_folder: str) -> list:
    """Returns paths to all XHTML/HTML files in the text folder."""
    if not os.path.exists(text_folder):
        return []
    
    return [
        os.path.join(text_folder, f) 
        for f in os.listdir(text_folder) 
        if f.lower().endswith(('.xhtml', '.html'))
    ]