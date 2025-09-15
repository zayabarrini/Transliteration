# Zaya Barrini Products

cards
zayasapp
zayascinema
zayasCRM
zayaslanguage
ZayasTransliteration
zayaweb

# Inspiration

Toward a Global Topological Psychology

https://zayabarrini.vercel.app/blog/posts/Psychoanalysis-Topology-NdP-Chinese

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

# Multilingual Products, Tools for Reading/Listening

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

E-book Split Sentences (Break paragraphs into sentences for easier reading of double language ebooks)
    ## Multi-file
    input_folder = '/home/zaya/Documents/Ebooks/Flow/Transliteration/Test'  # Update this path to your folder containing EPUB files
        output_folder = '/home/zaya/Documents/Ebooks/Flow/Transliteration/Test/Output'  # Update this path to your desired output folder
        process_epub_folder(input_folder, output_folder)
    
    ## Single file
    process_epub(str(epub_file), str(output_path))

E-Book Versions (db, no_original, trans)
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

Generate Word/Sentence Lists
Word/Translation/Transliteration
Sentence/Translation/Transliteration
Multilingual Ebook (sentence translation to n languages)

# Ebook Lists

## Themes 

Actresses
AllLanguages
Black Mirror
Characters
Cinema
Conversations
Curso
Diccionario De Topologia Lacaniana
Dictionary
Favorite
Fluxos
Freudiana
Grammar
Harry Potter
HP Cinema Screenplays
Lacan
LGBT
Literature
Mobius3
Mobius3Presentation
Music
Originals
Parts of Speech
Phonetics
Psicanálise
Psychoanalysis
Quotes
Revista
Sentences
Songs Lyrics
Studies
Topology
TransParenting
Vestibular
Vocabulaire
Word Frequency
WordList

## Languages

ar, ch, de, en, es, fr, gr, hb, hi, id, it, ja, jp, ko, la, ml, po, pt, ru, sw, tu

Ch
Black_Mirror-db-ch.epub
Black_Mirror-db-ch_transliterated.epub
Characters-Frequency-ch-db-trans.epub
Characters-Strokes-ch-db-trans.epub
Cinema-ch-Favorite-Movies-3.0-ch-ch-trans.epub
Cinema-ch-Favorite-Movies-3.0-ch-db_transliterated.epub
Cinema-ch-Favorite-Movies-3.0-ch-trans--Zaya.epub
Cinema-ch-Favorite-Movies-3.0-ch-trans.epub
Cinema-ch-Favorite-Movies-3.0-ch.epub
Cinema-ch-Favorite-Movies-3.0-ch_no_original_transliterated.epub
Cinema-ch-Favorite-Movies-3.0-transliterated-ch.epub
Cinema-Directors-ch-db-trans.epub
Cinema-Directors-ch-db.epub
Cinema-Directors-ch-trans.epub
Cinema-Directors-ch.epub
Conversations-Chinese-ch.epub
Conversations-Chinese-db-ch.epub
Conversations-Chinese-db-ch_transliterated.epub
Diccionario_De_Topologia_Lacaniana-db-ch-s.epub
Diccionario_De_Topologia_Lacaniana-db-ch_transliterated-s.epub
Dictionary-ch-db-trans.epub
Dictionary-ch-db.epub
Dictionary-ch-trans.epub
Dictionary-ch.epub
Favorite-Movies--ch_trans.epub
Favorite-Movies--db-ch.epub
Favorite-Movies--db-ch_no_original.epub
Favorite-Movies--no-ch.epub
Favorite-Movies-3.0-ch-db.epub
Favorite-Movies-3.0-ch-db_transliterated.epub
Favorite-Movies-3.0-ch.epub
Favorite-Movies-3.0-ch_no_original.epub
Favorite-Movies-3.0-ch_no_original_transliterated.epub
Favorite-Movies-4-ch-db.epub
Favorite-Movies-4-ch-db_no_original.epub
Favorite-Movies-4-ch-db_no_original_no_original.epub
Favorite-Movies-4-ch-db_transliterated.epub
Favorite-Movies_-The-Hours--db-ch.epub
Favorite-Movies_-The-Hours--no-ch.epub
Favorite-Movies_-The-Hours-db-ch.epub
Favorite-Movies_-The-Hours-db-ch_transliterated.epub
Favorite-Movies_-TheHours--db-ch_transliterated.epub
Fluxos---Melancholic-Machines--ch---巴里尼尺寸.epub
Fluxos---Melancholic-Machines-ch-nl---Zaya-Barrini.epub
Fluxos-Melancholic-Machines--ch.epub
Freudiana-chinese-E-PATER-db-ch---Freudiana---CdC-ELP_no_original.epub
Freudiana-chinese-Malestares-Contemporáneos-db-ch---Freudiana---CdC-ELP_no_original.epub
Freudiana-E-PATER-db-ch---Freudiana---CdC-ELP.epub
Freudiana-E-PATER-db-ch---Freudiana---CdC-ELP_transliterated.epub
Freudiana-E-PATER-Freudiana97-CdC-ELP-ch.epub
Freudiana-Malestares-Contemporáneos-db-ch---Freudiana---CdC-ELP.epub
Freudiana-Malestares-Contemporáneos-db-ch---Freudiana---CdC-ELP_transliterated.epub
Freudiana-Testo-yonqui-(Paul-B.-Preciado)-ch.epub
Freudiana-Testo-yonqui-(Spanish-Edition)---Paul-B.-Preciado-db-ch.epub
Freudiana-潮騒---三島由紀夫-db-ch.epub
Freudiana-精神分析殺人事件-(角川文庫)---森村-誠一-db-ch.epub
HP_Cinema_Screenplays-db-ch.epub
HP_Cinema_Screenplays-db-ch_transliterated.epub
Lacan-S4-LA-RELATION-db-ch.epub
Lacan-S4-LA-RELATION-db-ch_no.epub
Lacan-S4-LA-RELATION-db-ch_transliterated.epub
"Lacan-S10-L'ANGOISSE-db-ch.epub"
"Lacan-S10-L'ANGOISSE-db-ch_no.epub"
"Lacan-S10-L'ANGOISSE-db-ch_transliterated.epub"
Lacan-S14-LOGIQUE-db-ch.epub
Lacan-S14-LOGIQUE-db-ch_no.epub
Lacan-S14-LOGIQUE-db-ch_transliterated.epub
Lacan-S20-ENCORE-db-ch.epub
Lacan-S20-ENCORE-db-ch_no.epub
Lacan-S20-ENCORE-db-ch_transliterated.epub
Lacan-S25-db-ch.epub
Lacan-S25-db-ch_no.epub
Lacan-seminaires-db-ch.epub
Lacan-seminaires-db-ch_no.epub
Lacan-seminaires-db-ch_transliterated.epub
"Lacan-Seminaires-S18-D'UN-DISCOURS..-ch.epub"
"Lacan-Seminaires-S18-D'UN-DISCOURS..-ch.pdf"
LGBT-Dictionary-ch-db-trans.epub
LGBT-Dictionary-ch-db.epub
LGBT-Dictionary-ch-trans.epub
LGBT-Dictionary-ch.epub
Mobius3-ch-trans.epub
Mobius3Presentation-ch-db.epub
Mobius3Presentation-ch-db_transliterated.epub
Music-2025-1D-BS-db-ch.epub
Music-2025-1D-BS-db-ch_transliterated.epub
Music-Practice-Chinese-Songs-db-ch_transliterated.epub
Music-Practice-Languages-Music-db-ch_transliterated.epub
Parts_of_Speech-ch-db-trans.epub
Parts_of_Speech-ch-db.epub
Parts_of_Speech-ch-trans.epub
Parts_of_Speech-ch.epub
Phonetics-ch.epub
Psychoanalysis-Murder-Case-(Kadokawa-Library)-(Mori-mura-Seiichi)-ch.epub
Psychoanalysis-中国经典名著：续子不语（简体版）（Chinese-Classics-Continued-confucius-said-nothing-—-Simplified-Chinese-Edition）-(Yuan-Mei)-(Z-Library)-ch.epub
Psychoanalysis-你当像鸟飞往你的山-(塔拉·韦斯特弗（Tara-Westover）)-(Z-Library)-ch.epub
Psychoanalysis-哈利波特完整系列-(Harry_Potter-the-Complete-Collection)-(Rowling-J.K.,-马爱农,-马爱新,-苏农)-ch.epub
Psychoanalysis-在熟悉的家中向世界道别-(上野千鹤子)-(Z-Library)-ch.epub
Psychoanalysis-日本語を書く作法・読む作法-(角川文庫)-(阿刀田-高)-(Z-Library)-ch.epub
Psychoanalysis-潮騒---三島由紀夫-db-ch.epub
Psychoanalysis-精神分析殺人事件-(角川文庫)-(森村-誠一)-(Z-Library)-ch.epub
Psychoanalysis-韓国語能力試験初級（1級・2級）対策単語・文法-(韓国語教材)-(韓国語学習会)-(Z-Library)-ch.epub
Quotes-Favorite-Movies-db-ch.epub
Quotes-Favorite-Movies-db-ch_transliterated.epub
Sentences-ch-db.epub
Sentences-ch-db_transliterated.epub
Sentences-ch.epub
Songs_Lyrics-db-ch.epub
Songs_Lyrics-db-ch_transliterated.epub
Studies-Chinese-ch.epub
Studies-Chinese-Studies-db_no_original-ch.epub
Studies-db-ch.epub
Studies-db_transliterated-ch.epub
Topology-Nom-du-Père-db-ch.epub
Topology-Nom-du-Père-db-ch_transliterated.epub
Topology-Nom-du-Père-no-ch_no.epub
Vocabulaire-psychanalyse--Chinese-ch.epub
Vocabulaire-psychanalyse--Jean-Laplanche-&-Jean-Bertrand-Pontalis-ch.epub
Vocabulaire-psychanalyse-ch.epub
Vocabulaire-psychanalyse-Chinese-English-ch.epub
Word_Frequency-ch-db-trans.epub
WordList-ch-no.epub
WordList-Pinyin,-WordList-Chinese-db-ch.epub
WordList-Pinyin,-WordList-Chinese_-words-db---Zaya-Barrini-ch.epub