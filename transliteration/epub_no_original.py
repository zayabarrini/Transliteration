import os
import shutil
from lxml import etree
from transliteration.epubManagement import extract_epub, create_epub, find_text_folder, get_xhtml_files
# from transliteration.epubManagementNew import extract_epub, create_epub, find_text_folder, get_xhtml_files

from transliteration.epubTransliteration import get_language_from_filename
from transliteration.add_metadata_and_cover import add_metadata_and_cover

def remove_original_text(file_path: str) -> None:
    """
    Removes only the original text elements (immediately before dir="auto" elements)
    while preserving all other structure.
    """
    parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
    tree = etree.parse(file_path, parser)
    root = tree.getroot()
    
    keep_translations = True   # Set to False to keep originals instead

    # Find all translated elements
    # translations = root.xpath('//*[@dir="auto" or (@lang and not(@lang="en"))]')
    translations = root.xpath('//*[@dir="auto" or (@lang)]')
    
    # For each translation, remove its immediate previous sibling if it exists
    # and doesn't have dir="auto"
    for elem in translations:
        prev = elem.getprevious()
        if keep_translations:
            # When keeping translations, remove originals
            if 'dir' in elem.attrib or (prev is not None and prev.get('lang') != elem.get('lang')):
                # This is likely a translation (has dir attribute or different lang from previous)
                if (prev is not None and 
                    prev.tag not in ['head', 'meta', 'title', 'link']):
                    parent = prev.getparent()
                    if parent is not None:
                        parent.remove(prev)
        else:
            # When keeping originals, remove translations
            if 'dir' in elem.attrib or (prev is not None and prev.get('lang') != elem.get('lang')):
                # This is likely a translation - remove it
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
        print(f"Text folder found: {text_folder}")
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