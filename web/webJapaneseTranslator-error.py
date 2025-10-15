from flask import Flask, render_template, request
import fugashi
import pykakasi
from deep_translator import GoogleTranslator
import time
import os

app = Flask(__name__)

# Initialize analyzers
kks = pykakasi.kakasi()

# Set MeCab environment variable if needed (fix for fugashi initialization)
os.environ["MECABRC"] = "/etc/mecabrc"  # or the correct path on your system


def get_translator():
    max_retries = 3
    for i in range(max_retries):
        try:
            translator = GoogleTranslator()
            translator.translate("test", src="en", dest="ja")
            return translator
        except:
            if i < max_retries - 1:
                time.sleep(1)
                continue
            raise Exception("Failed to initialize translator after multiple attempts")


def process_japanese(text):
    translator = get_translator()

    # Initialize fugashi with explicit dictionary path if needed
    try:
        tagger = fugashi.Tagger()
    except RuntimeError as e:
        # Try with system dictionary path
        tagger = fugashi.Tagger("-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd")

    words = [word.surface for word in tagger(text)]
    readings = []
    for word in words:
        try:
            conv = kks.convert(word)
            readings.append(conv[0]["hepburn"] if conv else word)
        except:
            readings.append(word)

    translations = []
    for word in words:
        try:
            time.sleep(0.5)
            translation = translator.translate(word, src="ja", dest="en")
            translations.append(translation)
        except Exception as e:
            print(f"Translation failed for '{word}': {str(e)}")
            translations.append(word)

    # Prepare ruby groups
    ruby_groups = []
    for word, reading, translation in zip(words, readings, translations):
        ruby_groups.append({"word": word, "reading": reading, "translation": translation})

    return ruby_groups


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form["text"]
        try:
            result = process_japanese(text)
            return render_template("Japanese.html", result=result, original_text=text)
        except Exception as e:
            return render_template("Japanese.html", error=f"An error occurred: {str(e)}")

    return render_template("Japanese.html")


if __name__ == "__main__":
    app.run(debug=True, port=5004)
