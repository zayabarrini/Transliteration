import os
import shutil

import webbrowser
import http.server
import socketserver
import threading


from bs4 import BeautifulSoup, NavigableString  # For HTML parsing

from transliteration.add_css import (  # Import from our new module
    add_css_link,
    get_css_file,
)
from transliteration.transliteration import (
    add_furigana,
    get_pinyin_annotations,
    is_latin,
    transliterate,
)


def contains_chinese(text):
    """Check if text contains Chinese characters"""
    import re

    chinese_pattern = re.compile(r"[\u4e00-\u9fff]")
    return bool(chinese_pattern.search(text))


def process_html_content(soup, language):
    """Recursively process all text nodes in the HTML and add transliteration."""
    from bs4 import BeautifulSoup, NavigableString

    for element in soup.find_all(string=True):
        if element.parent and element.parent.name in ["script", "style", "ruby", "rt"]:
            continue

        text = element.strip()
        if not text:
            continue

        # For Chinese language processing, only apply dual display to text with Chinese characters
        if language.lower() == "chinese":
            if contains_chinese(text):
                # This is Chinese text - apply dual display
                dual_display = get_pinyin_annotations(text, color_coded=True)
                element.replace_with(dual_display)
            else:
                # This is non-Chinese text - leave it as is or apply simple processing
                # You can choose to leave it untouched or add minimal processing
                continue  # Skip processing for non-Chinese text
        else:
            # Handle other languages
            transliterated_text = transliterate(text, language)
            furigana_content = add_furigana(text, transliterated_text, language)
            if furigana_content != text:
                element.replace_with(furigana_content)

import re
from collections import Counter

LANGUAGE_CHAR_RANGES = {
    "korean": [(0xAC00, 0xD7AF)],  # Hangul syllables
    "arabic": [(0x0600, 0x06FF)],   # Basic Arabic
    "russian": [(0x0400, 0x04FF)],  # Cyrillic
    "hindi": [(0x0900, 0x097F)],    # Devanagari (Hindi)
    "japanese": [
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana  
        (0x4E00, 0x9FFF),  # Kanji/Chinese characters
    ],
    "chinese": [(0x4E00, 0x9FFF)],  # Chinese characters
    "latin": [(0x0041, 0x007A), (0x00C0, 0x02AF)],  # Basic Latin + extended
}

# Language priority for ambiguous characters (Chinese/Japanese share Kanji)
LANGUAGE_PRIORITY = ["chinese", "japanese", "korean", "hindi", "arabic", "russian", "latin"]

def detect_language_char(char):
    """Detect which language a character belongs to"""
    char_code = ord(char)
    
    # Skip common punctuation and whitespace
    if char in ' .,!?。，！？、」「『』（）《》-—–…':
        return "punctuation"
    
    for lang, ranges in LANGUAGE_CHAR_RANGES.items():
        for start, end in ranges:
            if start <= char_code <= end:
                return lang
    
    return "unknown"

def detect_language_text(text):
    """Detect the primary language of a text block"""
    if not text.strip():
        return "unknown"
    
    char_languages = []
    for char in text:
        lang = detect_language_char(char)
        if lang not in ["punctuation", "unknown"]:
            char_languages.append(lang)
    
    if not char_languages:
        return "unknown"
    
    # Count language occurrences
    lang_counts = Counter(char_languages)
    
    # Handle Chinese/Japanese ambiguity with better heuristics
    if "japanese" in lang_counts and "chinese" in lang_counts:
        # If there are Japanese-specific characters, prioritize Japanese
        if contains_japanese_specific_chars(text):
            return "japanese"
        # If there are Chinese-specific patterns, prioritize Chinese
        elif contains_chinese_specific_patterns(text):
            return "chinese"
        # Default to the majority
        elif lang_counts["japanese"] > lang_counts["chinese"]:
            return "japanese"
        else:
            return "chinese"
    
    # For single language or clear majority
    primary_lang = lang_counts.most_common(1)[0][0]
    
    # Double-check Chinese/Japanese if detected
    if primary_lang == "japanese" and not contains_japanese_specific_chars(text) and contains_chinese_specific_patterns(text):
        return "chinese"
    elif primary_lang == "chinese" and contains_japanese_specific_chars(text):
        return "japanese"
    
    return primary_lang

def contains_japanese_specific_chars(text):
    """Check for Japanese-specific characters"""
    # Hiragana and Katakana are uniquely Japanese
    hiragana_range = (0x3040, 0x309F)
    katakana_range = (0x30A0, 0x30FF)
    # Japanese punctuation and symbols
    japanese_punct = "・「」『』〜"
    
    for char in text:
        code = ord(char)
        if (hiragana_range[0] <= code <= hiragana_range[1] or 
            katakana_range[0] <= code <= katakana_range[1] or
            char in japanese_punct):
            return True
    return False

def contains_chinese_specific_patterns(text):
    """Check for Chinese-specific patterns"""
    # Chinese punctuation
    chinese_punct = "。，！？《》【】"
    # Common Chinese characters not typically used in Japanese
    chinese_specific_chars = "这那为个说国们着么"
    
    if any(punct in text for punct in chinese_punct):
        return True
    
    if any(char in text for char in chinese_specific_chars):
        return True
    
    return False

def segment_text_by_language(text):
    """Segment text into language-specific blocks"""
    if not text.strip():
        return []
    
    # First, detect the primary language of the entire text block
    primary_lang = detect_language_text(text)
    
    # If it's clearly one language, treat it as a single segment
    if primary_lang not in ["unknown", "punctuation"]:
        return [(text, primary_lang)]
    
    # Fallback: character-level segmentation for truly mixed content
    segments = []
    current_segment = ""
    current_lang = None
    
    for char in text:
        char_lang = detect_language_char(char)
        
        # Treat punctuation as continuing the current segment
        if char_lang == "punctuation":
            current_segment += char
            continue
        
        if current_lang is None:
            current_lang = char_lang
            current_segment = char
        elif current_lang == char_lang:
            current_segment += char
        else:
            # Language changed, save current segment
            if current_segment.strip():
                segments.append((current_segment, current_lang))
            current_segment = char
            current_lang = char_lang
    
    # Add the final segment
    if current_segment.strip():
        segments.append((current_segment, current_lang))
    
    return segments

def process_html_content_multilingual(soup, default_language=None):
    """Process HTML content with automatic language detection and transliteration"""
    from bs4 import BeautifulSoup, NavigableString, Tag
    
    for element in soup.find_all(string=True):
        if element.parent and element.parent.name in ["script", "style", "ruby", "rt"]:
            continue
        
        text = element.strip()
        if not text:
            continue
        
        # Skip if text is too short or doesn't need processing
        if len(text) < 2 or text.isascii():
            continue
        
        # Segment text by language
        segments = segment_text_by_language(text)
        
        if len(segments) == 1:
            # Single language text
            segment_text, detected_lang = segments[0]
            if detected_lang not in ["unknown", "punctuation", "latin"]:
                processed_content = process_segment(segment_text, detected_lang)
                if processed_content != segment_text:
                    # Ensure we're replacing with proper HTML
                    if isinstance(processed_content, str):
                        # Parse the HTML string and replace
                        try:
                            processed_soup = BeautifulSoup(processed_content, 'html.parser')
                            if processed_soup.find():
                                # If it contains HTML tags, replace with the parsed content
                                element.replace_with(processed_soup)
                            else:
                                # Plain text replacement
                                element.replace_with(processed_content)
                        except:
                            # Fallback: plain text replacement
                            element.replace_with(processed_content)
                    else:
                        # Already a BeautifulSoup object
                        element.replace_with(processed_content)
        
        elif len(segments) > 1:
            # Mixed language text - process each segment
            processed_segments = []
            for segment_text, detected_lang in segments:
                if detected_lang in ["unknown", "punctuation"]:
                    processed_segments.append(segment_text)
                elif detected_lang == "latin":
                    # Keep Latin text as-is
                    processed_segments.append(segment_text)
                else:
                    processed_segment = process_segment(segment_text, detected_lang)
                    processed_segments.append(processed_segment)
            
            # Combine processed segments - handle both strings and BeautifulSoup objects
            combined_content = soup.new_tag("span")
            for segment in processed_segments:
                if isinstance(segment, (Tag, NavigableString)):
                    # Already a BeautifulSoup object
                    combined_content.append(segment)
                elif isinstance(segment, str):
                    # Plain text or HTML string
                    try:
                        # Try to parse as HTML
                        segment_soup = BeautifulSoup(segment, 'html.parser')
                        if segment_soup.find():
                            # Contains HTML tags, append all children
                            for child in segment_soup.contents:
                                combined_content.append(child)
                        else:
                            # Plain text
                            combined_content.append(segment)
                    except:
                        # Fallback: append as plain text
                        combined_content.append(segment)
                else:
                    # Unknown type, convert to string
                    combined_content.append(str(segment))
            
            # Replace the original element with our combined content
            element.replace_with(combined_content)

def process_segment(text, language):
    """Process a text segment with the specified language"""
    try:
        if language == "chinese":
            chinese_result = get_pinyin_annotations(text, color_coded=True)
            from bs4 import BeautifulSoup
            return BeautifulSoup(chinese_result, 'html.parser')       
        else:
            # For all other languages, use add_furigana which now includes language classes
            transliterated = transliterate(text, language)
            furigana_content = add_furigana(text, transliterated, language)
            return furigana_content
    
    except Exception as e:
        print(f"Error processing {language} text '{text}': {e}")
        return text  # Fallback to original text
        
# def process_html_content(soup, language, keep_translations=True):
#     for element in soup.descendants:
#         if not (isinstance(element, NavigableString) and element.strip()):
#             continue

#         parent = getattr(element, 'parent', None)
#         if not parent or not hasattr(parent, 'name') or parent.name in ['script', 'style', 'ruby', 'rt']:
#             continue

#         # Get previous element sibling
#         prev = getattr(parent, 'previous_sibling', None)
#         while prev and not (hasattr(prev, 'name') and isinstance(prev.name, str)):
#             prev = getattr(prev, 'previous_sibling', None)

#         # Check conditions
#         should_transliterate = False
#         try:
#             if keep_translations:
#                 if 'dir' in parent.attrs or (prev and prev.get('lang') != parent.get('lang')):
#                     should_transliterate = True
#             else:
#                 if prev and ('dir' in prev.attrs or prev.get('lang') != parent.get('lang')):
#                     if getattr(prev, 'name', None) not in ['head', 'meta', 'title', 'link']:
#                         should_transliterate = True
#         except AttributeError:
#             continue

#         if not should_transliterate or is_latin(element):
#             continue

#         try:
#             transliterated_text = transliterate(element, language)
#             element.replace_with(add_furigana(element, transliterated_text, language))
#         except Exception as e:
#             print(f"Error processing element: {e}")
#             continue

def serve_html_folder(folder_path, port=8000, auto_open=True):
    """
    Start an HTTP server to serve HTML files from the specified folder.
    
    Args:
        folder_path (str): Path to the folder containing HTML files
        port (int): Port number for the server (default: 8000)
        auto_open (bool): Whether to automatically open the browser (default: True)
    
    Returns:
        str: URL of the server
    """
    # Convert to absolute path
    folder_path = os.path.abspath(folder_path)
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return None
    
    # Create a simple index page for easy navigation
    index_path = os.path.join(folder_path, "index.html")
    if not os.path.exists(index_path):
        create_navigation_index(folder_path)
    
    # Change to the folder
    original_dir = os.getcwd()
    os.chdir(folder_path)
    
    # Create handler with custom logging
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # Suppress default logging for cleaner output
            if not format.startswith("GET /"):
                print(f"  → {args[0] if args else format}")
    
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    server_url = f"http://localhost:{port}/"
    
    print(f"\n{'='*60}")
    print(f"🌐 HTTP Server Started")
    print(f"📁 Serving folder: {folder_path}")
    print(f"🔗 URL: {server_url}")
    print(f"⚙️  Port: {port}")
    print(f"💡 Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")
    
    if auto_open:
        webbrowser.open(server_url)
        print(f"✅ Browser opened automatically\n")
    
    try:
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{'='*60}")
        print(f"🛑 Server stopped")
        print(f"{'='*60}\n")
    finally:
        os.chdir(original_dir)


def create_navigation_index(folder_path):
    """
    Create an index.html file for easy navigation through HTML files.
    
    Args:
        folder_path (str): Path to the folder
    """
    # Get all HTML/XHTML files
    html_files = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".html", ".htm", ".xhtml", ".xml")):
            html_files.append(filename)
    
    if not html_files:
        return
    
    # Sort files
    html_files.sort()
    
    # Create the index HTML
    index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EPUB Viewer - Navigate Pages</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .file-list {{
            padding: 30px;
        }}
        
        .file-item {{
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }}
        
        .file-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .file-link {{
            display: flex;
            align-items: center;
            padding: 15px 20px;
            text-decoration: none;
            color: #333;
            font-size: 1.1em;
        }}
        
        .file-link:hover {{
            color: #667eea;
        }}
        
        .file-icon {{
            font-size: 1.5em;
            margin-right: 15px;
        }}
        
        .file-name {{
            flex: 1;
            font-family: monospace;
        }}
        
        .file-size {{
            color: #666;
            font-size: 0.9em;
            margin-left: 15px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .file-link {{
                flex-wrap: wrap;
            }}
            
            .file-size {{
                margin-left: 35px;
                margin-top: 5px;
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 EPUB Viewer</h1>
            <p>Select a page to start reading</p>
        </div>
        
        <div class="file-list">
            <h2 style="margin-bottom: 20px; color: #333;">📖 Available Pages</h2>
"""
    
    # Add each HTML file as a link
    for filename in html_files:
        # Get file size
        file_path = os.path.join(folder_path, filename)
        file_size = os.path.getsize(file_path)
        
        # Format size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # Choose icon based on file type
        icon = "📄" if filename.endswith(".html") else "📝"
        
        index_content += f"""
            <div class="file-item">
                <a href="{filename}" class="file-link">
                    <span class="file-icon">{icon}</span>
                    <span class="file-name">{filename}</span>
                    <span class="file-size">{size_str}</span>
                </a>
            </div>
"""
    
    index_content += f"""
        </div>
        
        <div class="footer">
            <p>✨ Total {len(html_files)} pages • Server running locally</p>
            <p style="margin-top: 5px; font-size: 0.8em;">💡 Tip: You can also navigate to specific files directly</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write the index file
    with open(os.path.join(folder_path, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"📝 Created navigation index with {len(html_files)} files")


def view_processed_html(html_file_path, port=8000):
    """
    View a specific HTML file by starting a server and opening it.
    
    Args:
        html_file_path (str): Path to the HTML file
        port (int): Port for the server
    """
    if not os.path.exists(html_file_path):
        print(f"❌ File not found: {html_file_path}")
        return
    
    folder = os.path.dirname(html_file_path)
    filename = os.path.basename(html_file_path)
    
    # Start server in a separate thread
    original_dir = os.getcwd()
    os.chdir(folder)
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress logging
    
    socketserver.TCPServer.allow_reuse_address = True
    
    server_url = f"http://localhost:{port}/{filename}"
    
    print(f"\n{'='*60}")
    print(f"🌐 Opening HTML file: {filename}")
    print(f"🔗 URL: {server_url}")
    print(f"💡 Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")
    
    webbrowser.open(server_url)
    
    try:
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped\n")
    finally:
        os.chdir(original_dir)


def process_file(input_file, language, enable_multilingual_transliteration, epub_folder=None):
    """
    Processes an HTML or XHTML file for transliteration and CSS styling.

    Args:
        input_file (str): Path to the input HTML/XHTML file.
        language (str): Target language for transliteration.
        enable_multilingual_transliteration (bool): Whether to enable transliteration.
        css_file (str, optional): Path to the CSS file to be added. Defaults to None.
    """
    print(f"Processing {input_file} for {language} with transliteration: {enable_multilingual_transliteration}")

    # Read the input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse content
    # Parse content - use XML parser for XHTML and XML, HTML parser for others
    if input_file.endswith((".xhtml", ".xml")):
        parser = "lxml-xml"
    else:
        parser = "html.parser"
    soup = BeautifulSoup(content, parser)

    # Apply transliteration if enabled
    if enable_multilingual_transliteration:
        process_html_content_multilingual(soup, language)
    else:
        process_html_content(soup, language)

    # Add CSS if epub_folder is provided
    if epub_folder:
        css_rel_path = get_css_file(language, epub_folder)
        add_css_link(soup, css_rel_path)

    # Determine output filename (retain the original extension)
    base_name, ext = os.path.splitext(input_file)
    output_filename = f"{base_name}{ext}"

    # Save the modified content
    with open(output_filename, "w", encoding="utf-8") as f:
        if input_file.endswith((".xhtml", ".xml")):
            f.write(soup.prettify(formatter=None))  # Preserve XML formatting for XHTML
        else:
            f.write(soup.prettify(formatter=None))  # Standard HTML formatting

    print(f"Saved transliterated file: {output_filename}")


def process_folder(html_folder, target_language, enable_multilingual_transliteration=False, epub_folder=None):
    """
    Processes all HTML files in the specified folder.
    """

    for filename in os.listdir(html_folder):
        if filename.lower().endswith((".html", ".htm", ".xhtml", ".xml")):
            input_filename = os.path.join(html_folder, filename)
            process_file(input_filename, target_language, enable_multilingual_transliteration, epub_folder)


if __name__ == "__main__":
    # Define the folder containing HTML files
    html_folder = "/home/zaya/Downloads/Zayas/ZayasBooks/t/Heated-Rivalry-db-zh_transliterated_ccs/"
    # target_language = "japanese"  # Target language (e.g., 'chinese', 'japanese', etc.)
    # process_folder(html_folder, target_language)
    
    # Then serve them for viewing
    serve_html_folder(html_folder, port=8000)
    
    # Or view a specific file
    # specific_file = os.path.join(html_folder, "chapter1.xhtml")
    # view_processed_html(specific_file)