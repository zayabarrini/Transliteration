import http.server
import socketserver
from http import HTTPStatus
from urllib.parse import parse_qs
import os
from googletrans import Translator
import time

# Map target languages to Google Translate language codes
LANGUAGE_CODE_MAP = {
    'german': 'de',
    'italian': 'it',
    'french': 'fr',
    'russian': 'ru',
    'chinese': 'zh-CN',
    'japanese': 'ja',
    'hindi': 'hi',
    'arabic': 'ar',
    'korean': 'ko',
    'english': 'en',
    'spanish': 'es'
}

TRANSLITERATION_LANGUAGES = ['chinese', 'japanese', 'hindi', 'arabic', 'korean', 'russian']

class TranslationHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open('output.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/translate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            input_text = params['text'][0]

            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            results_html = self.process_translation(input_text)
            with open('output.html', 'r', encoding='utf-8') as f:
                html = f.read()
                updated_html = html.replace('<div id="results"></div>', 
                                          f'<div id="results">{results_html}</div>')
                self.wfile.write(updated_html.encode('utf-8'))

    def process_translation(self, input_text):
        translator = Translator()
        results = []
        
        for lang_name, lang_code in LANGUAGE_CODE_MAP.items():
            try:
                translation = translator.translate(input_text, dest=lang_code).text
                
                if lang_name in TRANSLITERATION_LANGUAGES:
                    # This is a placeholder - replace with your actual transliteration
                    transliteration = f"TL-{translation[:5]}..."  
                    formatted_text = f'<ruby>{translation}<rt>{transliteration}</rt></ruby>'
                else:
                    formatted_text = translation
                
                results.append({
                    'language': lang_name,
                    'translation': translation,
                    'formatted_text': formatted_text,
                    'needs_transliteration': lang_name in TRANSLITERATION_LANGUAGES
                })
            except Exception as e:
                print(f"Error processing {lang_name}: {str(e)}")
                results.append({
                    'language': lang_name,
                    'error': str(e)
                })
        
        results_html = ""
        for result in results:
            if 'error' in result:
                results_html += f"""
                <div class="error">
                    <h2>{result['language'].capitalize()}</h2>
                    <p>Error: {result['error']}</p>
                </div>
                """
            else:
                results_html += f"""
                <div class="{result['language']}">
                    <h2>{result['language'].capitalize()}</h2>
                    <p><strong>Translation:</strong> {result['translation']}</p>
                    {f"<p><strong>Transliteration:</strong> {result['formatted_text']}</p>" 
                     if result['needs_transliteration'] else ""}
                </div>
                """
            results_html += "<hr>"
        
        return results_html

def start_server(port=8000):
    # Create default files if they don't exist
    if not os.path.exists('output.html'):
        with open('output.html', 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Translation App</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="content">
        <h1>Multilingual Translator</h1>
        <form method="post" action="/translate">
            <textarea name="text" rows="4" cols="50" placeholder="Enter text..." required></textarea><br>
            <input type="submit" value="Translate">
        </form>
        <div id="results"></div>
    </div>
</body>
</html>""")

    if not os.path.exists('styles.css'):
        with open('styles.css', 'w', encoding='utf-8') as f:
            f.write("""body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}
.content {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
textarea {
    width: 100%;
    padding: 8px;
    margin-bottom: 10px;
}
input[type="submit"] {
    padding: 8px 16px;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
#results {
    margin-top: 20px;
}
.error {
    color: #cc0000;
}
ruby {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
}
rt {
    font-size: 0.7em;
}""")

    print(f"Server starting at http://localhost:{port}")
    with socketserver.TCPServer(("", port), TranslationHandler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    start_server()