def transliterate(input_text, language):
    if sys.getsizeof(input_text) > 1_000_000:  # 1MB
        return "Input too large"
    if not input_text:
        return ""
    if language == "chinese":
        # return ' '.join(pypinyin.lazy_pinyin(input_text, style=pypinyin.Style.NORMAL))
        return get_pinyin_annotations(input_text)
    elif language == "japanese":
        print("It's Japanese")
        # from modified.modified_kakasi import Kakasi as CustomKakasi

        # # kakasi = original_pykakasi.kakasi()  # Will use patched version
        # return CustomKakasi.kakasi().convert(input_text)
        kakasi = original_pykakasi.kakasi()
        return kakasi().convert(input_text)

        # kakasi.setMode("H", "a")  # Hiragana to Romaji
        # kakasi.setMode("K", "a")  # Katakana to Romaji
        # kakasi.setMode("J", "a")  # Kanji to Romaji
        # converter = kakasi.getConverter()
    elif language == "russian":
        import transliterate

        return transliterate.translit(input_text, "ru", reversed=True)
    elif language == "hindi":
        result = indic_transliterate(input_text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return result
    elif language == "arabic":
        # return original_pyarabic.custom_utf82latin(input_text)  # Will use patched version
        from modified.modified_pyarabic import custom_utf82latin as custom_arabic

        return custom_arabic(input_text)
    elif language == "korean":
        from modified.modified_hangul import Transliter as CustomTransliter

        transliter = CustomTransliter(rule=academic)  # Explicit rule
        # transliter = OriginalTransliter(rule=academic)  # Explicit rule
        result = transliter.translit(input_text)
        return result
    else:
        return input_text
