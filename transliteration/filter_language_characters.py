import re

def filter_language_characters(text: str, target_language: str) -> str:
    """
    Filters text to keep only characters from the target language's script.
    Returns empty string if no characters from the target language are found.
    
    Args:
        text: Input text to filter
        target_language: Language code (e.g., 'zh', 'hi', 'ar', 'ja', 'ko', 'ru')
    
    Returns:
        Text containing only characters from the target language's script
    """
    # Define Unicode ranges for different language scripts
    script_ranges = {
        'zh-CN': (  # Chinese (Han characters)
            r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]',
            "CJK Unified Ideographs"
        ),
        'zh-ch': (  # Chinese (Han characters)
            r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]',
            "CJK Unified Ideographs"
        ),
        'hi': (  # Hindi (Devanagari)
            r'[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF]',
            "Devanagari"
        ),
        'ar': (  # Arabic
            r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
            "Arabic"
        ),
        'ja': (  # Japanese (Hiragana, Katakana, Kanji)
            r'[\u3040-\u309F\u30A0-\u30FF\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]',
            "Japanese"
        ),
        'ko': (  # Korean (Hangul)
            r'[\u1100-\u11FF\u3130-\u318F\uA960-\uA97F\uAC00-\uD7AF\uD7B0-\uD7FF]',
            "Hangul"
        ),
        'ru': (  # Russian (Cyrillic)
            r'[\u0400-\u04FF\u0500-\u052F]',
            "Cyrillic"
        )
    }
    
                # r'[\u0400-\u04FF\u0500-\u052F]',

    
    if target_language not in script_ranges:
        raise ValueError(f"Unsupported target language: {target_language}")
    
    pattern, _ = script_ranges[target_language]
    # Find all characters from the target script
    matched_chars = re.findall(pattern, text)
    if(target_language == 'zh-CN' or target_language == 'ja' or target_language == 'zh-ch' or target_language == 'ko'):
            filtered_text = ''.join(matched_chars)
    else:
        filtered_text = ' '.join(matched_chars)
    
    return filtered_text.strip()

def filter_language_characters_preserve_spaces(text: str, target_language: str) -> str:
    """
    Filters text to keep only characters from the target language's script while
    preserving spaces between words.
    
    Args:
        text: Input text to filter
        target_language: Language code (e.g., 'ru' for Russian)
    
    Returns:
        Text containing only characters from the target language's script with preserved spaces
    """
    script_ranges = {
        'ru': (r'[\u0400-\u04FF\u0500-\u052F]', "Cyrillic"),  # Russian Cyrillic
        'hi': (  # Hindi (Devanagari)
            r'[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF]',
            "Devanagari"
        ),
        'ar': (  # Arabic
            r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
            "Arabic"
        ),    
    }
    
    if target_language not in script_ranges:
        raise ValueError(f"Unsupported target language: {target_language}")
    
    pattern, _ = script_ranges[target_language]
    
    # Split the text into words while preserving spaces
    words = text.split()
    filtered_words = []
    
    for word in words:
        # Find all characters from the target script in this word
        matched_chars = re.findall(pattern, word)
        filtered_word = ''.join(matched_chars)
        
        # Only keep the word if it contains target language characters
        if filtered_word:
            filtered_words.append(filtered_word)
    
    # Rejoin words with spaces
    return ' '.join(filtered_words)

def get_language_script_name(target_language: str) -> str:
    """
    Returns the name of the script for a given language code.
    """
    script_ranges = {
        'zh-CN': "Chinese (Han)",   
        'zh-ch': "Chinese (Han)",
        'hi': "Devanagari",
        'ar': "Arabic",
        'ja': "Japanese",
        'ko': "Hangul",
        'ru': "Cyrillic"
    }
    return script_ranges.get(target_language, "Unknown script")

# Example usage:
if __name__ == "__main__":
    test_text = "我儿子的中国文学成绩一直很好。1959 年夏 SUMMER 1959"
    print(filter_language_characters(test_text, 'zh'))  # Returns only Chinese characters
    print(filter_language_characters(test_text, 'en'))  # Raises ValueError