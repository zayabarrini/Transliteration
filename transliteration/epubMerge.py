import glob
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup


def merge_multiple_epubs(epub_paths: List[str], output_path: str, languages: List[str], merge_order: List[str] = None):
    """
    Merge multiple EPUB translations into a single multilingual EPUB.
    """
    
    if len(epub_paths) != len(languages):
        raise ValueError("Number of EPUB paths must match number of languages")
    
    if merge_order is None:
        merge_order = languages
    else:
        for lang in merge_order:
            if lang not in languages:
                raise ValueError(f"Language {lang} in merge_order not found in provided languages")
    
    print(f"Merging {len(epub_paths)} EPUBs in order: {merge_order}")
    
    # Create temporary directories for extraction
    temp_dirs = []
    try:
        # Extract all EPUBs
        epub_data = {}
        for i, (epub_path, lang) in enumerate(zip(epub_paths, languages)):
            temp_dir = tempfile.mkdtemp()
            temp_dirs.append(temp_dir)
            
            print(f"Extracting {lang} EPUB: {os.path.basename(epub_path)}")
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            epub_data[lang] = {
                'path': temp_dir,
                'order_index': merge_order.index(lang) if lang in merge_order else len(merge_order)
            }
        
        # Create merged directory using first EPUB as base
        merged_dir = tempfile.mkdtemp()
        temp_dirs.append(merged_dir)
        base_lang = languages[0]
        shutil.copytree(epub_data[base_lang]['path'], merged_dir, dirs_exist_ok=True)
        
        # Merge all HTML files
        merge_all_html_files(epub_data, merged_dir, merge_order)
        
        # Create final EPUB
        print("Creating merged multilingual EPUB...")
        create_epub_from_folder(merged_dir, output_path)
        print(f"Successfully created merged EPUB: {output_path}")
        
    finally:
        # Cleanup temporary directories
        for temp_dir in temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)

def merge_all_html_files(epub_data: Dict, merged_dir: str, merge_order: List[str]):
    """Merge HTML files from all EPUBs according to specified order."""
    
    # Get list of all HTML files from first EPUB
    base_lang = list(epub_data.keys())[0]
    html_files = []
    
    for root, dirs, files in os.walk(epub_data[base_lang]['path']):
        for file in files:
            if file.lower().endswith(('.html', '.htm', '.xhtml')):
                rel_path = os.path.relpath(os.path.join(root, file), epub_data[base_lang]['path'])
                html_files.append(rel_path)
    
    # Process each HTML file
    for html_file in html_files:
        print(f"Processing: {html_file}")
        
        # Collect all language versions of this file
        language_files = {}
        for lang, data in epub_data.items():
            file_path = os.path.join(data['path'], html_file)
            if os.path.exists(file_path):
                language_files[lang] = file_path
        
        if len(language_files) > 1:
            # Merge this file across all languages
            merged_file_path = os.path.join(merged_dir, html_file)
            merge_multilingual_html_robust(language_files, merged_file_path, merge_order)

def merge_multilingual_html_robust(language_files: Dict[str, str], output_path: str, merge_order: List[str]):
    """
    Merges by matching original texts and inserting all translations after each original.
    """
    
    # Load all language versions
    soups = {}
    for lang, file_path in language_files.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            soups[lang] = BeautifulSoup(f.read(), 'xml' if file_path.endswith('.xhtml') else 'html.parser')
    
    base_lang = list(language_files.keys())[0]
    base_soup = soups[base_lang]
    
    # Find all paragraphs in base language
    base_paragraphs = base_soup.find_all('p')
    
    # Process each paragraph in the base language
    for original_para in base_paragraphs:
        # Get the text content (this is the "original" text)
        original_text = original_para.get_text(strip=True)
        if not original_text:
            continue
            
        # Track if we found translations for this original
        found_translations = False
        
        # For each other language in order, find its translation
        for lang in merge_order:
            if lang == base_lang or lang not in soups:
                continue
                
            # Search for this original text in the target language file
            target_paragraphs = soups[lang].find_all('p')
            
            # Find where this original appears
            original_index = -1
            for i, target_p in enumerate(target_paragraphs):
                target_text = target_p.get_text(strip=True)
                if target_text == original_text:
                    original_index = i
                    break
            
            if original_index >= 0:
                # Look for the translation that follows this original
                # In the structure, translations follow the original immediately
                translation_found = False
                for j in range(original_index + 1, len(target_paragraphs)):
                    next_p = target_paragraphs[j]
                    # Check if this is a translation by looking for lang attribute or style
                    if (next_p.get('lang') or 
                        next_p.get('style') and 'color' in next_p.get('style', '')):
                        # Found a translation
                        new_translation = create_translation_copy(next_p, lang)
                        if new_translation:
                            # Insert before the original paragraph (so translations appear before the original)
                            original_para.insert_before(new_translation)
                            found_translations = True
                            translation_found = True
                            break
                    else:
                        # If we hit another original paragraph, stop looking
                        break
                
                # If we didn't find a translation immediately after, try searching more
                if not translation_found:
                    # Look for any paragraph with lang attribute within the next few paragraphs
                    for k in range(original_index + 1, min(original_index + 5, len(target_paragraphs))):
                        check_p = target_paragraphs[k]
                        if check_p.get('lang'):
                            new_translation = create_translation_copy(check_p, lang)
                            if new_translation:
                                original_para.insert_before(new_translation)
                                found_translations = True
                                break
    
    # Save merged HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        if output_path.endswith(('.xhtml', '.xml')):
            f.write(str(base_soup))
        else:
            f.write(base_soup.prettify())

def create_translation_copy(element, target_lang: str):
    """Create a copy of a translation element with the target language."""
    try:
        # Create a deep copy of the element
        element_copy = BeautifulSoup(str(element), 'html.parser').find()
        
        if element_copy:
            # Update language attributes
            element_copy['lang'] = target_lang
            element_copy['dir'] = 'auto'
            
            # Preserve style if it exists
            if element.get('style'):
                element_copy['style'] = element.get('style')
            
            # Preserve class
            if element.get('class'):
                element_copy['class'] = element['class']
        
        return element_copy
    except Exception as e:
        print(f"Error creating translation copy: {e}")
        return None

def create_epub_from_folder(folder_path: str, output_path: str):
    """Create EPUB file from folder contents."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

# Usage examples:
if __name__ == "__main__":
    epub_paths = [
        '/home/zaya/Downloads/Zayas/ZayasBooks/t/Quotes-Favorite-Movies-db-de.epub',
        '/home/zaya/Downloads/Zayas/ZayasBooks/t/Quotes-Favorite-Movies-db-ru.epub',
        '/home/zaya/Downloads/Zayas/ZayasBooks/t/Quotes-Favorite-Movies-db-fr.epub',
        '/home/zaya/Downloads/Zayas/ZayasBooks/t/Quotes-Favorite-Movies-db-it.epub',
        '/home/zaya/Downloads/Zayas/ZayasBooks/t/Quotes-Favorite-Movies-db-ch.epub'
    ]

    languages = ['de', 'ru', 'fr', 'it', 'zh']  
    merge_order = ['de', 'ru', 'fr', 'it', 'zh']  
    output_path = '/home/zaya/Downloads/Zayas/ZayasBooks/t/Quotes-Favorite-Movies-ml-de-ru-fr-it-ch.epub'
    
    merge_multiple_epubs(epub_paths, output_path, languages, merge_order)