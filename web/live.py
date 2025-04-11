import re
import os
import pypinyin
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as indic_transliterate
import pykakasi
from pyarabic.trans import custom_utf82latin
import jieba
import http.server
import socketserver
import json
from livereload import Server
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Function to check if a token contains only Latin characters
def is_latin(token):
    return bool(re.match(r'^[A-Za-z0-9\s\W_]+$', token))

# Function to tokenize text into words and symbols
def tokenize_text(text):
    tokens = re.findall(r'\w+|\W+', text)
    return tokens

# Function to add furigana to text
def add_furigana(text, transliteration, language):
    tokens = tokenize_text(text)
    # tokens = text
    if language == "japanese":
        trans_words = transliteration
    elif language == "korean":
        trans_words = transliteration
    else:
        trans_words = transliteration.split()
    
    furigana_text = []
    trans_index = 0
    
    for token in tokens:
        if is_latin(token):
            furigana_text.append(token)
        elif re.match(r'\W+', token):
            furigana_text.append(token)
        else:
            if language == "chinese":
                segmented_words = list(jieba.cut(token))
                for word in segmented_words:
                    num_syllables = len(word)
                    pinyin = ' '.join(trans_words[trans_index:trans_index + num_syllables])
                    trans_index += num_syllables
                    furigana_text.append(f"<ruby>{word}<rt>{pinyin}</rt></ruby>")
            elif language == "japanese":
                segmented_chars = list(token)
                for char in segmented_chars:
                    if trans_index < len(trans_words):
                        romaji = trans_words[trans_index]
                        trans_index += 1
                        furigana_text.append(f"<ruby>{char}<rt>{romaji}</rt></ruby>")
                    else:
                        furigana_text.append(char)
            elif language == "korean":
                for char in token:
                    if trans_index < len(trans_words):
                        romanization = trans_words[trans_index]
                        trans_index += 1
                        furigana_text.append(f"<ruby>{char}<rt>{romanization}</rt></ruby>")
                    else:
                        furigana_text.append(char)
            elif language in ["hindi", "arabic", "russian"]:
                if trans_index < len(trans_words):
                    translit = trans_words[trans_index]
                    trans_index += 1
                    furigana_text.append(f"<ruby>{token}<rt>{translit}</rt></ruby>")
                else:
                    furigana_text.append(token)
            else:
                furigana_text.append(token)
    
    return ''.join(furigana_text)

# Function to transliterate text
def transliterate(input_text, language):
    if language == "chinese":
        return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.TONE3))
    elif language == "japanese":
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")
        kakasi.setMode("K", "a")
        kakasi.setMode("J", "a")
        converter = kakasi.getConverter()
        result = converter.do(input_text)
        return result.split()
    elif language == "russian":
        import transliterate
        return transliterate.translit(input_text, 'ru', reversed=True)
    elif language == "hindi":
        result = indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return result
    elif language == "arabic":
        return custom_utf82latin(input_text)
    elif language == "korean":
        transliter = Transliter(rule=academic)
        result = transliter.translit(input_text)
        return result.split() 
    else:
        return input_text

# Function to write the HTML file
def write_html_file(content, output_file):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Multilingual Transliteration</title>
        <link rel="stylesheet" href="styles.css">
        <!-- Add LiveReload script -->
        <script>
            document.write('<script src="http://' + (location.host || 'localhost').split(':')[0] +
            ':35729/livereload.js?snipver=1"></' + 'script>');
        </script>
    </head>
    <body>
        <div class="content">
            {content}
        </div>
    </body>
    </html>
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

# Function to write the CSS file
def write_css_file(css_file):
    css_content = """
    ruby {
        display: inline-flex;
        flex-direction: column-reverse;
        align-items: center;
        white-space: nowrap;
        margin-right: 0.5em;
    }

    rt {
        font-size: 0.75em;
        line-height: 1.2;
        text-align: center;
    }

    .content {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        font-family: Arial, sans-serif;
    }

    h1 {
        font-size: 1.5em;
        margin-bottom: 10px;
    }

    p {
        font-size: 1.2em;
        line-height: 1.6;
    }
    """
    with open(css_file, "w", encoding="utf-8") as f:
        f.write(css_content)

# Function to start a live server
def start_live_server(port=8000):
    server = Server()
    server.watch("output.html")  # Watch the HTML file for changes
    server.watch("styles.css")   # Watch the CSS file for changes
    server.watch("test.json")    # Watch the JSON file for changes
    server.watch("webTransliteration.py")  # Watch the Python script for changes
    server.serve(root=".", port=port, open_url_delay=1)  # Serve the current directory
    
# Function to read and parse the JSON file
def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# Watch for changes to JSON or Python files
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if event.src_path.endswith((".json", ".py")):
            print(f"Detected changes in {event.src_path}. Regenerating files...")
            self.callback()

def watch_files(callback):
    event_handler = FileChangeHandler(callback)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Main function to process the input file
def process_file(input_file):
    def generate_files():
        # Read the JSON file
        input_file_data = read_json_file(input_file)
        
        # Generate HTML content
        html_content = ""
        for entry in input_file_data:
            language = entry["language"]
            text = entry["text"]
            transliteration_line = transliterate(text, language)
            formatted_line = add_furigana(text, transliteration_line, language)
            
            html_content += f"""
            <h1>{language.capitalize()}</h1>
            <p>{formatted_line}</p>
            """

        # Write the HTML file
        write_html_file(html_content, "output.html")

        # Write the CSS file
        write_css_file("styles.css")

    # Generate files initially
    generate_files()

    # Watch for changes and regenerate files
    watch_files(generate_files)

    # Start the live server
    start_live_server()

# Example usage
input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/test.json"  # Replace with your input file
process_file(input_file)