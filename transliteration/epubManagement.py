import fnmatch
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
    
     # List of possible folder patterns to check
    possible_folders = [
        # Google Docs pattern
        ('GoogleDoc', []),
        # Your custom pattern
        ('*/EPUB/text', []),
        # Other common patterns
        ('EPUB/text', []),
        ('OEBPS/Text', []),
        ('text', []),
        ('Text', []),
        ('EPUB', []),
        ('', ['*.xhtml', '*.html'])  # Root directory with xhtml/html files
    ]
    
    # Check each possible pattern
    for folder_pattern, file_patterns in possible_folders:
        # Build full path pattern
        full_pattern = os.path.join(extract_to, folder_pattern)
        
        # Find matching directories
        for root, dirs, files in os.walk(extract_to):
            if fnmatch.fnmatch(root, full_pattern):
                # If specific file patterns are given, check for them
                if file_patterns:
                    for file in files:
                        if any(fnmatch.fnmatch(file, fp) for fp in file_patterns):
                            return root
                else:
                    # No specific file patterns - return first match
                    return root
    
    # Default fallback (create standard EPUB structure)
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