# For What

- Multilingual Products, Tools for Reading/Listening: [de, it, fr, ru, zh-ch, jp, hi, ar, ko, en, es ]
- Transliteration: SUPPORTED_LANGUAGES = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]
- Consistent with patterns from Calibre Translation Plugin

# How to Use, Download and Install

Menu.md

## Requeriments

python_version = "3.12"

[Grammar Rules](https://github.com/zayabarrini/zayas-grammar-db)

# Main usage

## Epub Versions

### Transliteration: transliterate_epub(epub_path, language)

### merge_multiple_epubs(epub_paths, output_path, languages, merge_order)

Merge different dual translations of the same Epub into one

```python
epub_paths = [
        '/folder/filename-db-de.epub',
        '/folder/filename-db-ru.epub',
        '/folder/filename-db-fr.epub',
        '/folder/filename-db-it.epub',
        '/folder/filename-db-ch.epub'
    ]

    languages = ['de', 'ru', 'fr', 'it', 'zh']
    merge_order = ['de', 'ru', 'fr', 'it', 'zh']
    output_path = '/folder/filename-ml-de-ru-fr-it-ch.epub'
```

#### epubMergeFolder.py process a folder

### remove_original(epub_path)

Remove different combinations of languages

### WordList process .csv files

## start-chinese-session.sh

Starts webChineseColor-coded.py and grammar-db (Contains language grammar rules)

## subtitles2epub.sh

Takes a list of .txt, .md, .srt files and compile into EPUB

### subtitles/zip2zipMultilingual.py

Compose multiple language subtitles with transliteration
