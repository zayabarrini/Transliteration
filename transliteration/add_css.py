import os
import shutil
from bs4 import BeautifulSoup


def ensure_styles_folder(epub_folder):
    """Ensure the Styles folder exists in the correct location (EPUB or OEBPS)"""
    # Try EPUB structure first
    styles_path = os.path.join(epub_folder, "EPUB", "Styles")
    if os.path.exists(os.path.join(epub_folder, "EPUB")):
        os.makedirs(styles_path, exist_ok=True)
        return styles_path, "EPUB"

    # Fall back to OEBPS structure
    styles_path = os.path.join(epub_folder, "OEBPS", "Styles")
    os.makedirs(styles_path, exist_ok=True)
    return styles_path, "OEBPS"


def get_css_file(language, epub_folder):
    """Returns the destination path for the CSS file after copying it to the EPUB folder"""
    css_mapping = {
        "japanese": "styles-jp.css",
        "chinese": "styles-ch.css",
        "arabic": "styles-ar.css",
        "hindi": "styles-hi.css",
        "default": "styles.css",
    }

    # Get the source CSS path
    css_filename = css_mapping.get(language, css_mapping["default"])
    source_path = f"/home/zaya/Downloads/Zayas/ZayasTransliteration/transliteration/{css_filename}"

    # Determine destination folder
    styles_path, structure = ensure_styles_folder(epub_folder)

    # Copy the CSS file
    dest_path = os.path.join(styles_path, css_filename)
    shutil.copy2(source_path, dest_path)

    # Return relative path from HTML files
    if structure == "EPUB":
        return os.path.join("..", "Styles", css_filename)
    else:  # OEBPS
        return os.path.join("..", "..", "OEBPS", "Styles", css_filename)


def add_css_link(soup, css_rel_path):
    """Add the CSS link to the HTML head"""
    # Ensure html element exists
    if not soup.html:
        soup.html = soup.new_tag("html")
        soup.append(soup.html)

    # Create or clean head section
    if not soup.head:
        head_tag = soup.new_tag("head")
        soup.html.insert(0, head_tag)

    # Remove existing style/link tags
    for tag in soup.head.find_all(["style", "link"]):
        tag.decompose()

    # Add new link tag
    link_tag = soup.new_tag("link", rel="stylesheet", type="text/css", href=css_rel_path)
    soup.head.append(link_tag)
