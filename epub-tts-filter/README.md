# Filter Chinese/Russian text from EPUB

pipenv run python epub_tts_filter.py /home/zaya/Downloads/Zayas/ZayasTransliteration/epub-tts-filter/Trans-Psychosis-db-ru.epub

# Read filtered content aloud

pipenv run python epub_tts_reader.py /home/zaya/Downloads/Zayas/ZayasTransliteration/epub-tts-filter/Trans-Psychosis-db-ru.epub

# Use specific TTS engine

pipenv run python epub_tts_reader.py /home/zaya/Downloads/Zayas/ZayasTransliteration/epub-tts-filter/Trans-Psychosis-db-ru.epub espeak
