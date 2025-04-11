# Files
Subtitles
md
epub
web
html

# Ebooks
## Easy
Grammar
Conversing
Language Conversation Made Natural Engaging Dialogues

## Flow
Favorite-movies-3.md
Favorite-movies-2.md
Favorite-movies.md
Fluxos - Melancholic Machines

## Basic
150-Lacanian-Sentences
Vocabulaire de la psychanalyse
Harry Potter

## Interesting
Psychoanalytical Magazines
Literature
Philosophy

# Language map
originals - (fr, en, es, pt, de, ru, it, ko, ch, ja, hi, ar)
all-en
original-(fr, en, es, pt, de?)

## 02/04/25
original-trans: fr-de, en-ch, es-ru, pt-ar, de-en
ch/ko/ja/hi/ar/ru-en
ch/ko/ja/hi/ar - transliteration Included

# To do 

Break Original Ebooks into phrases so Transliteration/Translation is easier to FlowRead
Remove original or translation
Mind Ebook size - it already takes some 20 to translate these smaller ebooks - Number of paragraphs
Language pairs:

# Process

- Process Ebook for Translation
- Ebook Translation ~30min
- Rename
- EbookVersions.py

# Multilingual Products

Multi-file Processing, single file processing
E-book Split Sentences
E-Book Versions
Subtitle Versions
Webpage Version

Let's build a menu for the products:
Multi-file Processing, single file processing for each:
E-book Split Sentences: epubSplitProcessor.py
E-Book Versions: epubVersions.py
Subtitle Versions: subMultilingualVersions.py
Webpage Version: html2transliteration.py

E-book Split Sentences
    ## Multi-file
    input_folder = '/home/zaya/Documents/Ebooks/Flow/Transliteration/Test'  # Update this path to your folder containing EPUB files
        output_folder = '/home/zaya/Documents/Ebooks/Flow/Transliteration/Test/Output'  # Update this path to your desired output folder
        process_epub_folder(input_folder, output_folder)
    
    ## Single file
    process_epub(str(epub_file), str(output_path))

E-Book Versions
    ## Multi-file
        process_folder("/home/zaya/Documents/Ebooks")
    ## Single file
        # Option 1: Remove original text
                epub_path_no_original = remove_original(epub_path)
        if language in SUPPORTED_LANGUAGES:
            # Option 2: Transliterate
            transliterate_epub(epub_path)
            # Option : Transliterate no_original
            transliterate_epub(epub_path_no_original)

Subtitle Versions
    ## Multi-file
        # input_dir = "/home/zaya/Documents/Gitrepos/cinema/Subtitles/"
    ## Single file
        ### Only Transliteration
            transliterate_srt(input_file, target_language)
        ### Multilingual zip generation
            input_file = "/home/zaya/Documents/Gitrepos/cinema/Subtitles/test.srt"
            target_languages = ["de", "zh-ch"]        
            process_multilingual_srt(input_file, target_languages, enable_transliteration=True)

Webpage Version
    ## Multi-file
        html_folder = '/home/zaya/Downloads/Harry Potter シリーズ全7巻 (J.K. Rowling) (Z-Library)-trans/OEBPS/Text'  # Update this path to your folder containing HTML files
        target_language = 'japanese'  # Target language (e.g., 'chinese', 'japanese', etc.)
        process_folder(html_folder, target_language)
    ## Single file
        process_file(input_filename, target_language, enable_transliteration, epub_folder)

