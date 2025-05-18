
from bs4 import BeautifulSoup, NavigableString  # For HTML parsing
import shutil
from transliteration.add_css import get_css_file, add_css_link  # Import from our new module
import os
from transliteration.transliteration import transliterate, add_furigana, is_latin

# def process_html_content(soup, language):
#     """Recursively process all text nodes in the HTML and add transliteration."""
#     for element in soup.descendants:
#         if isinstance(element, NavigableString) and element.strip():
#             # Skip text nodes that are inside script or style tags
#             if element.parent.name in ['script', 'style', 'ruby', 'rt']:
#                 continue
            
#             if(is_latin(element)):
#                 continue
            
#             # Transliterate the text content
#             transliterated_text = transliterate(element, language)
            
#             # Replace the text node with the transliterated text
#             element.replace_with(add_furigana(element, transliterated_text, language))


def process_html_content(soup, language, keep_translations=True):
    for element in soup.descendants:
        if not (isinstance(element, NavigableString) and element.strip()):
            continue
            
        parent = getattr(element, 'parent', None)
        if not parent or not hasattr(parent, 'name') or parent.name in ['script', 'style', 'ruby', 'rt']:
            continue
            
        # Get previous element sibling
        prev = getattr(parent, 'previous_sibling', None)
        while prev and not (hasattr(prev, 'name') and isinstance(prev.name, str)):
            prev = getattr(prev, 'previous_sibling', None)
        
        # Check conditions
        should_transliterate = False
        try:
            if keep_translations:
                if 'dir' in parent.attrs or (prev and prev.get('lang') != parent.get('lang')):
                    should_transliterate = True
            else:
                if prev and ('dir' in prev.attrs or prev.get('lang') != parent.get('lang')):
                    if getattr(prev, 'name', None) not in ['head', 'meta', 'title', 'link']:
                        should_transliterate = True
        except AttributeError:
            continue
            
        if not should_transliterate or is_latin(element):
            continue
            
        try:
            transliterated_text = transliterate(element, language)
            element.replace_with(add_furigana(element, transliterated_text, language))
        except Exception as e:
            print(f"Error processing element: {e}")
            continue
        
def process_file(input_file, language, enable_transliteration, epub_folder=None):
    """
    Processes an HTML or XHTML file for transliteration and CSS styling.

    Args:
        input_file (str): Path to the input HTML/XHTML file.
        language (str): Target language for transliteration.
        enable_transliteration (bool): Whether to enable transliteration.
        css_file (str, optional): Path to the CSS file to be added. Defaults to None.
    """
    print(f"Processing {input_file} for {language} with transliteration: {enable_transliteration}")

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse content
    # Parse content - use XML parser for XHTML and XML, HTML parser for others
    if input_file.endswith(('.xhtml', '.xml')):
        parser = 'lxml-xml'
    else:
        parser = 'html.parser'
    soup = BeautifulSoup(content, parser)

    # Apply transliteration if enabled
    if enable_transliteration:
        process_html_content(soup, language)

    # Add CSS if epub_folder is provided
    if epub_folder:
        css_rel_path = get_css_file(language, epub_folder)
        add_css_link(soup, css_rel_path)

    # Determine output filename (retain the original extension)
    base_name, ext = os.path.splitext(input_file)
    output_filename = f"{base_name}{ext}"

    # Save the modified content
    with open(output_filename, 'w', encoding='utf-8') as f:
        if input_file.endswith(('.xhtml', '.xml')):
            f.write(soup.prettify(formatter=None))  # Preserve XML formatting for XHTML
        else:
            f.write(soup.prettify(formatter=None))  # Standard HTML formatting
            
    print(f"Saved transliterated file: {output_filename}")
    
    
def process_folder(html_folder, target_language, enable_transliteration=True, epub_folder=None):
    """
    Processes all HTML files in the specified folder.
    """    

    for filename in os.listdir(html_folder):
        if filename.lower().endswith(('.html', '.htm', '.xhtml', '.xml')):
            input_filename = os.path.join(html_folder, filename)
            process_file(input_filename, target_language, enable_transliteration, epub_folder)
    
if __name__ == "__main__":
    # Define the folder containing HTML files
    html_folder = '/home/zaya/Downloads/Harry Potter シリーズ全7巻 (J.K. Rowling) (Z-Library)-trans/OEBPS/Text'  # Update this path to your folder containing HTML files
    target_language = 'japanese'  # Target language (e.g., 'chinese', 'japanese', etc.)
    process_folder(html_folder, target_language)

