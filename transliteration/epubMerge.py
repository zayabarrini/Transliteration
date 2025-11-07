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
            merge_multilingual_html_flexible(language_files, merged_file_path, merge_order)

def merge_multilingual_html_flexible(language_files: Dict[str, str], output_path: str, merge_order: List[str]):
    """
    Flexible merging that handles both calibre3 and calibre7 classes and various structures.
    """
    
    # Load all language versions
    soups = {}
    for lang, file_path in language_files.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            soups[lang] = BeautifulSoup(f.read(), 'xml' if file_path.endswith('.xhtml') else 'html.parser')
    
    # Use first language as base
    base_lang = list(language_files.keys())[0]
    base_soup = soups[base_lang]
    
    # Find all translation groups in all languages
    all_groups = {}
    for lang, soup in soups.items():
        all_groups[lang] = find_translation_groups_flexible(soup, lang)
    
    # Get the base language groups to use as reference
    base_groups = all_groups[base_lang]
    
    # For each translation group in base language, insert other language translations
    for group_key, (original_element, translation_element) in base_groups.items():
        # Insert other language translations before the original element
        for lang in merge_order:
            if lang == base_lang or lang not in all_groups:
                continue
                
            # Find the corresponding translation in the other language
            lang_groups = all_groups[lang]
            if group_key in lang_groups:
                other_original, other_translation = lang_groups[group_key]
                
                # Create a copy of the translation element with the correct language attributes
                if other_translation:
                    new_translation = create_translation_copy_flexible(other_translation, lang)
                    if new_translation:
                        # Insert before the original element
                        original_element.insert_before(new_translation)
    
    # Save merged HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        if output_path.endswith(('.xhtml', '.xml')):
            f.write(str(base_soup))
        else:
            f.write(base_soup.prettify())

def find_translation_groups_flexible(soup: BeautifulSoup, lang: str) -> Dict[str, Tuple]:
    """
    Find translation groups flexibly handling both calibre3 and calibre7 classes.
    Returns dict: {original_text: (original_element, translation_element)}
    """
    groups = {}
    
    # Find all paragraphs with calibre3 or calibre7 classes
    paragraphs = soup.find_all('p', class_=lambda x: x and ('calibre3' in x or 'calibre7' in x))
    
    i = 0
    while i < len(paragraphs):
        current_p = paragraphs[i]
        
        # Check if this is likely an original (no translation attributes)
        is_translation = is_translation_paragraph(current_p)
        is_original = not is_translation
        
        if is_original:
            original_text = current_p.get_text(strip=True)
            
            # Look ahead for translation paragraphs
            translation_elements = []
            j = i + 1
            while j < len(paragraphs):
                next_p = paragraphs[j]
                if is_translation_paragraph(next_p):
                    translation_elements.append(next_p)
                    j += 1
                else:
                    break
            
            if translation_elements:
                # Use the first translation as the main one (others might be alternative translations)
                groups[original_text] = (current_p, translation_elements[0])
                i = j  # Move to the next untranslated paragraph
            else:
                i += 1
        else:
            i += 1
    
    return groups

def is_translation_paragraph(paragraph) -> bool:
    """Check if a paragraph has translation attributes."""
    has_lang = paragraph.get('lang')
    has_dir = paragraph.get('dir') == 'auto'
    has_translation_style = paragraph.get('style') and 'color' in paragraph.get('style', '')
    
    return has_lang or has_dir or has_translation_style

def create_translation_copy_flexible(element, target_lang: str):
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

# Alternative robust approach that works with any structure
def merge_multilingual_html_robust(language_files: Dict[str, str], output_path: str, merge_order: List[str]):
    """
    Most robust merging approach - matches by original text content.
    """
    
    # Load all language versions
    soups = {}
    for lang, file_path in language_files.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            soups[lang] = BeautifulSoup(f.read(), 'xml' if file_path.endswith('.xhtml') else 'html.parser')
    
    base_lang = list(language_files.keys())[0]
    base_soup = soups[base_lang]
    
    # Find all original (non-translation) paragraphs in base language
    base_paragraphs = base_soup.find_all('p')
    base_originals = []
    
    for p in base_paragraphs:
        if not is_translation_paragraph(p):
            base_originals.append(p)
    
    # For each original paragraph, find and insert translations
    for original_para in base_originals:
        original_text = original_para.get_text(strip=True)
        if not original_text:
            continue
            
        # Insert translations for this original text
        for lang in merge_order:
            if lang == base_lang or lang not in soups:
                continue
                
            # Find matching original in target language and get its translation
            target_paragraphs = soups[lang].find_all('p')
            for i, target_p in enumerate(target_paragraphs):
                if not is_translation_paragraph(target_p):
                    target_text = target_p.get_text(strip=True)
                    if target_text == original_text:
                        # Found matching original, now find the translation that follows
                        translation_found = False
                        for j in range(i + 1, len(target_paragraphs)):
                            next_p = target_paragraphs[j]
                            if is_translation_paragraph(next_p):
                                # Create copy with target language
                                new_translation = create_translation_copy_flexible(next_p, lang)
                                if new_translation:
                                    original_para.insert_before(new_translation)
                                translation_found = True
                                break
                            elif not is_translation_paragraph(next_p):
                                # Reached another original, stop searching
                                break
                        
                        if translation_found:
                            break
    
    # Save merged HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        if output_path.endswith(('.xhtml', '.xml')):
            f.write(str(base_soup))
        else:
            f.write(base_soup.prettify())

# Update the main merging function to use the robust approach
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
            # Merge this file across all languages using robust approach
            merged_file_path = os.path.join(merged_dir, html_file)
            merge_multilingual_html_robust(language_files, merged_file_path, merge_order)

# Debug function
def debug_paragraph_structure(file_path: str, lang: str):
    """Debug function to see paragraph structure."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    print(f"\n=== Debug {lang} ===")
    paragraphs = soup.find_all('p')
    for i, p in enumerate(paragraphs):
        class_name = ' '.join(p.get('class', [])) if p.get('class') else 'no-class'
        lang_attr = p.get('lang', 'no-lang')
        dir_attr = p.get('dir', 'no-dir')
        style_attr = p.get('style', 'no-style')[:50] if p.get('style') else 'no-style'
        text_preview = p.get_text(strip=True)[:50] + "..." if len(p.get_text(strip=True)) > 50 else p.get_text(strip=True)
        
        print(f"Para {i}: class='{class_name}' lang='{lang_attr}' dir='{dir_attr}'")
        print(f"       style='{style_attr}'")
        print(f"       text='{text_preview}'")
        print()

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
    
    # Optional: Debug the structure first
    # for epub_path, lang in zip(epub_paths, languages):
    #     with tempfile.TemporaryDirectory() as temp_dir:
    #         with zipfile.ZipFile(epub_path, 'r') as zip_ref:
    #             zip_ref.extractall(temp_dir)
    #         # Find first HTML file to debug
    #         for root, dirs, files in os.walk(temp_dir):
    #             for file in files:
    #                 if file.lower().endswith(('.html', '.htm', '.xhtml')):
    #                     html_file = os.path.join(root, file)
    #                     debug_paragraph_structure(html_file, lang)
    #                     break
    #             break
    
    merge_multiple_epubs(epub_paths, output_path, languages, merge_order)