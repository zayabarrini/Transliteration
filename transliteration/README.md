Todo:

Remove_original/transliteration as a command

```sh
python3 -m transliteration.epubVersions -rm "option 3" -trans "zh"
```

# Remove original in EpubVersions

Predefined configurations for common use cases

```python
DEFAULT_CONFIG = {
"option": 1,
}
```

```python
CONFIG_PRESETS = {
    "keep_russian_after_english": {"option": 3, "language_to_keep": "ru", "language_after": "en"},
    "keep_chinese_after_russian": {"option": 3, "language_to_keep": "zh", "language_after": "ru"},
    "keep_english_after_chinese": {"option": 3, "language_to_keep": "en", "language_after": "zh"},
    "remove_all_english": {"option": 2, "language_to_keep": "en"},
    "remove_all_russian": {"option": 2, "language_to_keep": "ru"},
    # NEW: Keep Russian paragraphs that come after paragraphs without lang attribute
    "keep_russian_after_no_lang": {
        "option": 4,
        "language_to_keep": "ru",
        "reference_has_no_lang": True,
    },
    "Remove_original_text_elements": {
        "option": 1,
    },
}
```

# Merge 3 specific EPUBs in custom order

```python
merge_multiple_epubs(
    epub_paths=['file-de.epub', 'file-ru.epub', 'file-zh.epub'],
    output_path='merged.epub',
    languages=['de', 'ru', 'zh'],
    merge_order=['de', 'ru', 'zh']  # Or ['ru', 'de', 'zh'] etc.
)
```

# Use glob pattern to automatically find and merge

```python
merge_multiple_epubs_simple(
    file_patterns=['/path/to/books/*-db-*.epub'],
    output_path='merged.epub',
    merge_order=['de', 'ru', 'zh']
)
```

```python
epub_paths = [
    '/home/zaya/Downloads/Zayas/ZayasBooks/Language/t/Quotes-Favorite-Movies-db-de.epub',
    '/home/zaya/Downloads/Zayas/ZayasBooks/Language/t/Quotes-Favorite-Movies-db-ru.epub',
    '/home/zaya/Downloads/Zayas/ZayasBooks/Language/t/Quotes-Favorite-Movies-db-ch.epub'
]

languages = ['de', 'ru', 'zh']
merge_order = ['de', 'ru', 'zh']
output_path = '/home/zaya/Downloads/Zayas/ZayasBooks/Language/t/Quotes-Favorite-Movies-ml-de-ru-ch.epub'
```
