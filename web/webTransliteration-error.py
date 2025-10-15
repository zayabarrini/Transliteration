import re
import os
import http.server
import socketserver
import json
from transliteration.transliteration import add_furigana, transliterate


# Function to start a live server
def start_live_server(port=8000):
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving at http://localhost:{port}")
        httpd.serve_forever()


# Function to read and parse the JSON file
def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# Function to generate HTML content from JSON data
def generate_html_content(input_data):
    html_content = ""
    for entry in input_data:
        language = entry["language"]
        text = entry["text"]
        transliteration_line = transliterate(text, language)
        if transliteration_line is None:
            print(f"Warning: Failed to transliterate line: {text}")
            transliteration_line = text  # Fallback
        formatted_line = add_furigana(text, transliteration_line, language)

        html_content += f"""
        <div class={language}>
            <h1>{language.capitalize()}</h1>
            <p>{formatted_line}</p>
        </div>
        """
    return html_content


# Main function to process the input file
def process_file(input_file):
    # Read the input file
    input_file_data = read_json_file(input_file)

    # Generate HTML content
    html_content = generate_html_content(input_file_data)

    # Read the existing HTML template
    with open("output.html", "r", encoding="utf-8") as f:
        html_template = f.read()

    # Insert the generated content into the template
    updated_html = html_template.replace(
        '<div class="content"></div>', f'<div class="content">{html_content}</div>'
    )

    # Write the updated HTML back to the file
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(updated_html)

    # Start the live server
    start_live_server()


# Example usage
input_file = (
    "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/test.json"  # Replace with your input file
)
process_file(input_file)

# kakasi = pykakasi.kakasi()
# input_text = "漢字かなカナ"
# # result = kakasi.convert(input_text)
# # for entry in result:
# #     print(entry)
# result = kakasi.convert(input_text)
# furigana_text = add_furigana(input_text, result, "japanese")
# print(furigana_text)

# input_text_korean = "한글 그것은 쉽게 악몽으로"
# transliter = Transliter(rule=academic)
# result = transliter.translit(input_text_korean)
# furigana_text = add_furigana(input_text_korean, result, "korean")
# print(furigana_text)
# print(result)


# input_text_hindi = "आसानी से एक दुःस्वप्न में"
# result = indic_transliterate(input_text_hindi, sanscript.DEVANAGARI, sanscript.ITRANS)
# furigana_text = add_furigana(input_text_hindi, result, "hindi")
# print(furigana_text)
# print(result)

# input_text_chinese = "这很容易变成一场噩梦，但麦克尔斯菲尔德的加里和切里让它成功了。取得了巨大的成功。"
# result = ' '.join(pypinyin.lazy_pinyin(input_text_chinese, style=pypinyin.Style.TONE3))
# furigana_text = add_furigana(input_text_chinese, result, "chinese")
# print(furigana_text)
# # print(result)
