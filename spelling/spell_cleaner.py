import re
import spacy
from spellchecker import SpellChecker
import argparse
from pathlib import Path

class MDSpellCleaner:
    def __init__(self):
        # Character mapping for encoding fixes
        self.char_mapping = {
            'a´': 'á', 'e´': 'é', 'ı´': 'í', 'o´': 'ó', 'u´': 'ú',
            'A´': 'Á', 'E´': 'É', 'I´': 'Í', 'O´': 'Ó', 'U´': 'Ú',
            'aˆ': 'â', 'eˆ': 'ê', 'iˆ': 'î', 'oˆ': 'ô', 'uˆ': 'û',
            'Aˆ': 'Â', 'Eˆ': 'Ê', 'Iˆ': 'Î', 'Oˆ': 'Ô', 'Uˆ': 'Û',
            'a˜': 'ã', 'e˜': 'ẽ', 'i˜': 'ĩ', 'o˜': 'õ', 'u˜': 'ũ',
            'A˜': 'Ã', 'E˜': 'Ẽ', 'I˜': 'Ĩ', 'O˜': 'Õ', 'U˜': 'Ũ',
            'n˜': 'ñ', 'N˜': 'Ñ', 'c¸': 'ç', 'C¸': 'Ç',
            'a`': 'à', 'e`': 'è', 'ı`': 'ì', 'o`': 'ò', 'u`': 'ù',
            'A`': 'À', 'E`': 'È', 'I`': 'Ì', 'O`': 'Ò', 'U`': 'Ù',
            '´ı': 'í', '´I': 'Í'  # Fix for standalone acute accent + i
        }
        
        # Additional pattern fixes - using raw strings
        self.pattern_fixes = {
            r'\[\.\.\.\]': '...',    # [...] to ...
            r'\\\)': ')',            # \) to )
            r'\\\(': '(',            # \( to (
            r'\\\-': '-',            # \- to -
            r'\\\]': ']',            # \] to ]
            r'\\\[': '[',            # \[ to [
        }
        
        # Portuguese spell checker
        self.spell = SpellChecker(language='pt')
        
        # Common proper nouns and technical terms to ignore
        self.ignore_words = {
            'ita', 'brasil', 'eua', 'amazon', 'santos', 'dumont', 'embraer',
            'neil', 'tyson', 'alberto', 'ipanema', 'andres', 'cordilheira',
            'amazonas', 'atlântico', 'cruzeiro', 'sul', 'norte', 'steam', 'stem',
            'g20', 'onu', 'ods', 'labcts', 'cnii', 'marcelo', 'gleiser',
            'graciliano', 'ramos', 'vieira', 'camões', 'castro', 'alves',
            'gilberto', 'gil', 'chico', 'ferreira', 'bento', 'fabiano',
            'vitória', 'tomás', 'siracusa', 'arquimedes', 'oppenheimer',
            'hiroshima', 'nagasaki', 'alexandres', 'teixeira', 'poveda',
            'losekann', 'sergio', 'hocevar', 'blanchet', 'atahualpa',
            'ineía', 'turchetti', 'dullius', 'ellensohn', 'cruz', 'rufino',
            'alvear', 'oliveira', 'gabriela'
        }
        
        # Compile regex patterns for efficiency
        self.patterns = {re.escape(k): v for k, v in self.char_mapping.items()}
        self.regex_patterns = re.compile("|".join(self.patterns.keys()))
        
        # Compile pattern fixes - using raw strings properly
        pattern_keys = [re.escape(key) for key in self.pattern_fixes.keys()]
        self.pattern_fixes_regex = re.compile("|".join(pattern_keys))
        
        # Punctuation that should have space after (when missing)
        self.punctuation_needs_space = {'.', ',', ';', ':', '!', '?', '...'}
        
    def fix_encoding_issues(self, text):
        """Fix character encoding problems in the text"""
        def replace_match(match):
            return self.patterns[re.escape(match.group(0))]
        
        text = self.regex_patterns.sub(replace_match, text)
        return text
    
    def fix_patterns(self, text):
        """Fix specific patterns like [...], \\), etc."""
        def replace_pattern_match(match):
            matched_text = match.group(0)
            return self.pattern_fixes[matched_text]
        
        text = self.pattern_fixes_regex.sub(replace_pattern_match, text)
        return text
    
    def add_spaces_after_punctuation(self, text):
        """Add spaces after punctuation when there's none and remove spaces before punctuation"""
        
        # First, remove spaces BEFORE punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Then add spaces AFTER punctuation when missing
        def add_space_after_punctuation(match):
            punctuation = match.group(1)
            next_char = match.group(2)
            
            # Don't add space if it's part of a number (like 1.5)
            if punctuation == '.' and next_char.isdigit():
                return match.group(0)  # Leave 1.5 as is
            
            # Don't add space if it's part of a URL or file path
            if any(indicator in match.string for indicator in ['http://', 'https://', 'www.', '.com', '.org', '.net']):
                return match.group(0)
            
            # Don't add space if it's markdown syntax
            line_start = match.string[:match.start()].split('\n')[-1].strip()
            if any(line_start.startswith(char) for char in ['#', '-', '*', '>']) or line_start.replace('.', '').isdigit():
                return match.group(0)
            
            return f'{punctuation} {next_char}'
        
        # Patterns for adding spaces after punctuation
        patterns = [
            # Basic punctuation followed by letter
            (r'([.,;:!?])([a-zA-Zà-úÀ-Ú])', add_space_after_punctuation),
            # Ellipsis followed by letter
            (r'(\.\.\.)([a-zA-Zà-úÀ-Ú])', add_space_after_punctuation),
            # Punctuation before opening parenthesis
            (r'([.,;:!?])(\()', add_space_after_punctuation),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def spell_check_text(self, text):
        """Apply spell checking to the text"""
        lines = text.split('\n')
        corrected_lines = []
        
        for line in lines:
            # Skip lines that are likely code, URLs, or special formatting
            if any(indicator in line for indicator in ['http', 'www.', '.com', '.br', '**', '#', '```', '<!--']):
                corrected_lines.append(line)
                continue
            
            # Split into words while preserving punctuation and numbers
            words = re.findall(r'\b\w+\b|[^\w\s]', line)
            corrected_words = []
            
            for word in words:
                if not word.isalpha() or len(word) <= 1:
                    corrected_words.append(word)
                    continue
                
                # Check if word should be ignored (proper nouns, technical terms)
                if word.lower() in self.ignore_words or word.istitle() or word.isupper():
                    corrected_words.append(word)
                    continue
                
                # Check spelling
                if self.spell.unknown([word.lower()]):
                    correction = self.spell.correction(word.lower())
                    if correction and correction != word.lower():
                        # Preserve original capitalization
                        if word.istitle():
                            correction = correction.title()
                        elif word.isupper():
                            correction = correction.upper()
                        corrected_words.append(correction)
                    else:
                        corrected_words.append(word)
                else:
                    corrected_words.append(word)
            
            # Reconstruct the line
            corrected_line = ''
            for i, word in enumerate(corrected_words):
                if i > 0 and word.isalnum() and corrected_words[i-1].isalnum():
                    corrected_line += ' ' + word
                else:
                    corrected_line += word
            
            corrected_lines.append(corrected_line)
        
        return '\n'.join(corrected_lines)
    
    def clean_text(self, text):
        """Clean text by fixing encoding, patterns, punctuation spacing, and spell checking"""
        print("Fixing encoding issues...")
        text = self.fix_encoding_issues(text)
        
        print("Fixing patterns...")
        text = self.fix_patterns(text)
        
        print("Adding spaces after punctuation...")
        text = self.add_spaces_after_punctuation(text)
        
        print("Applying spell check...")
        text = self.spell_check_text(text)
        
        return text
    
    def clean_markdown_file(self, input_file, output_file=None):
        """Clean a markdown file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'iso-8859-1', 'windows-1252']:
                try:
                    with open(input_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode the file with any common encoding")
        
        content = self.clean_text(content)
        
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Cleaned file saved as: {output_file}")
        return output_file


def clean_markdown_file(input_file, output_file=None):
    """Convenience function to clean a markdown file"""
    cleaner = MDSpellCleaner()
    return cleaner.clean_markdown_file(input_file, output_file)


def clean_text(text):
    """Convenience function to clean text"""
    cleaner = MDSpellCleaner()
    return cleaner.clean_text(text)


# Test function to demonstrate the fixes
def test_fixes():
    """Test the specific fixes requested"""
    test_cases = [
        # Original -> Expected
        ("a`", "à"),
        ("´ı", "í"),
        ("[...]", "..."),
        ("\\)", ")"),
        ("\\-", "-"),
        ("\\]", "]"),
        ("\\[", "["),
        ("Olá.Mundo", "Olá. Mundo"),
        ("Teste,isso", "Teste, isso"),
        ("Final!Vamos", "Final! Vamos"),
    ]
    
    cleaner = MDSpellCleaner()
    
    print("Testing fixes:")
    for original, expected in test_cases:
        result = cleaner.clean_text(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{original}' -> '{result}' (expected: '{expected}')")


if __name__ == "__main__":
    # Run tests
    test_fixes()
    
    # Example usage
    sample_text = """
    Testando os fixes: a` palavra,´ıso, texto[...] e final\\).
    Também teste-palavra\\-outra e array\\[index\\].
    Sem espaço depois de pontuação.Isso deve ser corrigido.
    """
    
    print("\nSample text before:")
    print(sample_text)
    
    cleaner = MDSpellCleaner()
    cleaned = cleaner.clean_text(sample_text)
    
    print("Sample text after:")
    print(cleaned)