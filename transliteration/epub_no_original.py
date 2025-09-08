import os
import shutil
from lxml import etree
from transliteration.epubManagement import extract_epub, create_epub, find_text_folder, get_xhtml_files
# from transliteration.epubManagementNew import extract_epub, create_epub, find_text_folder, get_xhtml_files

from transliteration.epubTransliteration import get_language_from_filename
from transliteration.add_metadata_and_cover import add_metadata_and_cover

def remove_original_text(file_path: str, keep_translations: bool = True) -> None:
    """
    Removes either original text or translated text based on keep_translations flag.
    Assumes pattern: <p lang="en">English</p><p lang="de" dir="auto">German</p>
    """
    parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
    tree = etree.parse(file_path, parser)
    root = tree.getroot()
    
    # Find all paragraph elements with lang attribute
    paragraphs = root.xpath('//p[@lang]')
    
    elements_to_remove = []
    
    for i, elem in enumerate(paragraphs):
        lang = elem.get('lang', '')
        
        if keep_translations:
            # We want to keep translations, so remove English originals
            if lang == 'en':
                # Check if this English paragraph is followed by a translation
                next_elem = elem.getnext()
                if (next_elem is not None and 
                    next_elem.tag == 'p' and 
                    next_elem.get('lang') != 'en'):
                    elements_to_remove.append(elem)
        else:
            # We want to keep originals, so remove translations
            if lang != 'en':
                # Check if this translation is preceded by an English original
                prev_elem = elem.getprevious()
                if (prev_elem is not None and 
                    prev_elem.tag == 'p' and 
                    prev_elem.get('lang') == 'en'):
                    elements_to_remove.append(elem)
    
    # Remove the identified elements
    for elem in elements_to_remove:
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)

    # Save the modified file
    tree.write(file_path, encoding='utf-8', pretty_print=True, xml_declaration=True)

def process_epub(epub_path: str) -> str:
    """Processes an EPUB to remove original text while preserving structure."""
    base_name = os.path.basename(epub_path).replace('.epub', '')
    language = get_language_from_filename(base_name)
    extract_to = epub_path.replace('.epub', '_temp')
    output_path = epub_path.replace('.epub', '_no.epub')

    try:
        extract_epub(epub_path, extract_to)
        text_folder = find_text_folder(extract_to)
        for file_path in get_xhtml_files(text_folder):
            remove_original_text(file_path)
            
        add_metadata_and_cover(extract_to, base_name + '_no', language)

        create_epub(extract_to, output_path)
        return output_path

    finally:
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python epub_no_original.py <input.epub>")
        sys.exit(1)

    input_epub = sys.argv[1]
    output_epub = process_epub(input_epub)
    print(f"Generated EPUB with original text removed: {output_epub}")