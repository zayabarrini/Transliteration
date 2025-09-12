# Ebook composition of word lists

ar, ch, hi, ru, ja, ko, it
Lista original: várias línguas, en, de, ru
en-de
en-ru

# Compor ruby tags
lista en, lista target_language => Ruby tags

# Adicionar ruby tags no md => convert to ebook + pass styles
com en, sem en



## Usage

1. Prepare your English and German word lists in `test-en.md` and `test-de.md`
2. Ensure the files have the same number of lines and comma-separated words match positionally
3. Run `WordListRubyTranslation.py`
4. The results will be saved in `RubyTranslation.md`



# Ruby Translation Documentation

This document explains the ruby translation process that pairs English words with their German translations in a furigana-style format.

## How It Works

1. The script reads two markdown files:
   - `test-en.md` (English words)
   - `test-de.md` (German translations)

2. For each line in the files:
   - Header lines (starting with #) are skipped
   - Other lines are split by commas
   - Each word pair is combined into a ruby annotation format:
     ```html
     <ruby>German<rt>English</rt></ruby>
     ```

3. The results are saved to `RubyTranslation.md`

## Example Input

`test-en.md`: