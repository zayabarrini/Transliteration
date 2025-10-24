# Remove original in EpubVersions

DEFAULT_CONFIG = {
"option": 1,
}

# Predefined configurations for common use cases

# Add to your CONFIG_PRESETS

CONFIG_PRESETS = {
"keep_russian_after_english": {"option": 3, "language_to_keep": "ru", "language_after": "en"},
"keep_english_after_chinese": {"option": 3, "language_to_keep": "en", "language_after": "zh"},
"remove_all_english": {"option": 2, "language_to_keep": "en"},
"remove_all_russian": {"option": 2, "language_to_keep": "ru"}, # NEW: Keep Russian paragraphs that come after paragraphs without lang attribute
"keep_russian_after_no_lang": {
"option": 4,
"language_to_keep": "ru",
"reference_has_no_lang": True,
},
"Remove_original_text_elements": {
"option": 1,
},
}
