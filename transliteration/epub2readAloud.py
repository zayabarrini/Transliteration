#!/usr/bin/env python3
"""
epub2readAloud.py - Pre-process multilingual EPUB for @Voice with DEELX regex

This script adds hidden start and end markers for EVERY language detected,
so @Voice can detect them using pattern/replace regex.

Usage:
    python epub2readAloud.py input.epub
    python epub2readAloud.py input.epub --marker-start "##{LANG}_START##" --marker-end "##{LANG}_END##"
"""

import argparse
import os
import re
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from bs4 import BeautifulSoup

# Default configuration
DEFAULT_CONFIG = {
    'source_lang': 'en',                      # Default source language
    'marker_start': '[{LANG}]',               # Start marker pattern
    'marker_end': '[/{LANG}]',                # End marker pattern
    'verbose': False,
    'skip_nav_files': True,
    'output_suffix': '_readaloud',            # Suffix for output file
    'supported_languages': ['ar', 'bn', 'de', 'el', 'es', 'fr', 'he', 'hi', 'id', 
                           'it', 'ja', 'ko', 'la', 'mr', 'pa', 'pl', 'pt', 'ru', 
                           'sw', 'ta', 'te', 'th', 'tr', 'ur', 'vi', 'zh', 'en']
}

class EpubProcessor:
    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.source_lang = config.get('source_lang', DEFAULT_CONFIG['source_lang'])
        self.marker_start_pattern = config.get('marker_start', DEFAULT_CONFIG['marker_start'])
        self.marker_end_pattern = config.get('marker_end', DEFAULT_CONFIG['marker_end'])
        self.verbose = config.get('verbose', DEFAULT_CONFIG['verbose'])
        self.skip_nav_files = config.get('skip_nav_files', DEFAULT_CONFIG['skip_nav_files'])
        self.output_suffix = config.get('output_suffix', DEFAULT_CONFIG['output_suffix'])
        self.supported_languages = config.get('supported_languages', DEFAULT_CONFIG['supported_languages'])
        
        self.detected_languages = set()
        
    def log(self, message: str):
        """Print if verbose."""
        if self.verbose:
            print(f"[INFO] {message}", file=sys.stderr)
    
    def extract_epub(self, epub_path: str, extract_path: str) -> bool:
        """Extract EPUB to temp directory."""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            self.log(f"Extracted EPUB to {extract_path}")
            return True
        except Exception as e:
            print(f"Error extracting: {e}", file=sys.stderr)
            return False
    
    def create_epub(self, source_path: str, output_path: str) -> bool:
        """Create EPUB from extracted contents."""
        try:
            files = []
            for root, dirs, filenames in os.walk(source_path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, source_path)
                    files.append((filepath, rel_path))
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filepath, rel_path in files:
                    zipf.write(filepath, rel_path)
            
            self.log(f"Created EPUB: {output_path}")
            return True
        except Exception as e:
            print(f"Error creating EPUB: {e}", file=sys.stderr)
            return False
    
    def find_text_files(self, extract_path: str) -> List[Path]:
        """Find all HTML/XHTML files."""
        text_files = []
        search_paths = [
            os.path.join(extract_path, 'EPUB', 'text'),
            os.path.join(extract_path, 'EPUB'),
            os.path.join(extract_path, 'OEBPS', 'text'),
            os.path.join(extract_path, 'OEBPS', 'Text'),
            os.path.join(extract_path, 'OEBPS'),
            extract_path,
        ]
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                for ext in ['*.xhtml', '*.html', '*.htm', '*.xml']:
                    files = list(Path(search_path).glob(ext))
                    if files:
                        text_files.extend(sorted(files))
        
        self.log(f"Found {len(text_files)} text files")
        return text_files
    
    def get_paragraph_language(self, element, default_lang: str = None) -> str:
        """Determine language of a paragraph."""
        # Check element's lang attribute
        lang_attr = element.get('lang')
        if lang_attr:
            base_lang = lang_attr.split('-')[0].split('_')[0].lower()
            if base_lang in self.supported_languages:
                return base_lang
        
        # Check parent's lang attribute
        parent = element.parent
        while parent:
            parent_lang = parent.get('lang')
            if parent_lang:
                base_lang = parent_lang.split('-')[0].split('_')[0].lower()
                if base_lang in self.supported_languages:
                    return base_lang
            parent = parent.parent
        
        return default_lang or self.source_lang
    
    def detect_languages_in_file(self, file_path: Path) -> Set[str]:
        """Detect all languages in a file."""
        languages = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check elements with lang attribute
            for elem in soup.find_all(lang=True):
                lang = elem.get('lang', '').lower().strip()
                if lang:
                    base_lang = lang.split('-')[0].split('_')[0]
                    if len(base_lang) >= 2:
                        languages.add(base_lang)
            
            # Check paragraphs without lang (source language)
            has_content = False
            for p in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if not p.get('lang') and p.get_text().strip():
                    has_content = True
                    break
            
            if has_content:
                languages.add(self.source_lang)
                
        except Exception as e:
            self.log(f"Error detecting languages in {file_path}: {e}")
        
        return languages
    
    def detect_all_languages(self, text_files: List[Path]) -> Set[str]:
        """Detect all languages in EPUB."""
        all_languages = set()
        
        print("Detecting languages in EPUB...")
        for file_path in text_files:
            if self.skip_nav_files and any(skip in file_path.name.lower() 
                                          for skip in ['nav', 'cover', 'toc']):
                continue
            
            langs = self.detect_languages_in_file(file_path)
            all_languages.update(langs)
        
        if not all_languages:
            all_languages.add(self.source_lang)
        
        return all_languages
    
    def create_start_marker(self, lang: str) -> str:
        """Create start marker for a language."""
        return self.marker_start_pattern.replace('{LANG}', lang.upper())
    
    def create_end_marker(self, lang: str) -> str:
        """Create end marker for a language."""
        return self.marker_end_pattern.replace('{LANG}', lang.upper())
    
    def add_hidden_markers_to_paragraph(self, paragraph_text: str, language: str) -> str:
        """
        Add hidden start and end markers around paragraph text.
        """
        start_marker = self.create_start_marker(language)
        end_marker = self.create_end_marker(language)
        
        # Create hidden markers with multiple layers of hiding
        # display:none - hides from view
        # aria-hidden=true - hides from screen readers
        # class for identification
        hidden_start = f'<span style="display:none" aria-hidden="true" class="readaloud-marker-{language}" data-lang="{language}">{start_marker}</span>'
        hidden_end = f'<span style="display:none" aria-hidden="true" class="readaloud-marker-{language}" data-lang="{language}">{end_marker}</span>'
        
        # Wrap the entire paragraph content with markers
        modified_text = f'{hidden_start}{paragraph_text}{hidden_end}'
        
        return modified_text
    
    def process_html_file(self, file_path: Path, all_languages: Set[str]) -> Tuple[int, Dict[str, int]]:
        """Process HTML file and add markers."""
        marked_counts = defaultdict(int)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Process all text-containing elements
            elements = soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'li'])
            
            total_count = 0
            modified = False
            
            for elem in elements:
                # Get clean text (excluding any existing markers)
                original_text = elem.get_text()
                
                if not original_text.strip():
                    continue
                
                # Skip if text is too short (probably just punctuation)
                if len(original_text.strip()) < 2:
                    continue
                
                total_count += 1
                
                # Determine language
                lang = self.get_paragraph_language(elem, self.source_lang)
                
                if lang in all_languages:
                    marked_counts[lang] += 1
                    
                    # Clear and replace content
                    elem.clear()
                    
                    # Add markers around the text
                    modified_text = self.add_hidden_markers_to_paragraph(original_text, lang)
                    
                    # Parse and insert
                    try:
                        # Use div wrapper to maintain structure
                        wrapper = soup.new_tag('div', **{'class': f'readaloud-wrapper-{lang}'})
                        # Parse the modified text
                        parsed = BeautifulSoup(modified_text, 'html.parser')
                        wrapper.append(parsed)
                        elem.append(wrapper)
                        modified = True
                    except Exception as e:
                        self.log(f"Error processing element: {e}")
                        # Fallback: just keep original text
                        elem.string = original_text
            
            # Write back if modified
            if modified:
                # Clean up BeautifulSoup's formatting
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                self.log(f"  Modified {file_path.name}: {total_count} elements processed")
            
            return total_count, dict(marked_counts)
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            return 0, {}
    
    def generate_deelx_regex_config(self, all_languages: Set[str]) -> Dict[str, Dict[str, str]]:
        """
        Generate DEELX regex configuration for @Voice.
        
        @Voice uses DEELX regex engine with pattern/replace functionality.
        """
        config = {}
        
        for lang in sorted(all_languages):
            start_marker = self.create_start_marker(lang)
            end_marker = self.create_end_marker(lang)
            
            # Escape special regex characters
            start_escaped = re.escape(start_marker)
            end_escaped = re.escape(end_marker)
            
            # Pattern 1: Match content between start and end markers
            # This will capture the text to be read
            pattern1 = f'{start_escaped}(.*?){end_escaped}'
            replace1 = r'\1'  # Replace with captured content (remove markers)
            
            # Pattern 2: Match standalone markers (for safety)
            pattern2 = f'{start_escaped}|{end_escaped}'
            replace2 = ''  # Remove any leftover markers
            
            config[lang] = {
                'start_marker': start_marker,
                'end_marker': end_marker,
                'pattern_extract': pattern1,
                'replace_extract': replace1,
                'pattern_cleanup': pattern2,
                'replace_cleanup': replace2,
                'description': f'Read {lang.upper()} content'
            }
        
        return config
    
    def process_epub(self, epub_path: str) -> bool:
        """Process the entire EPUB."""
        epub_path_obj = Path(epub_path)
        if not epub_path_obj.exists():
            print(f"Error: EPUB not found: {epub_path}", file=sys.stderr)
            return False
        
        # Generate output path (same location as original)
        output_path = epub_path_obj.parent / f"{epub_path_obj.stem}{self.output_suffix}{epub_path_obj.suffix}"
        
        print(f"\n{'='*70}")
        print(f"Processing: {epub_path_obj.name}")
        print(f"{'='*70}")
        print(f"Source language: {self.source_lang}")
        print(f"Start marker pattern: {self.marker_start_pattern}")
        print(f"End marker pattern: {self.marker_end_pattern}")
        print(f"Output: {output_path.name}")
        print(f"{'='*70}\n")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract
            self.log("Extracting EPUB...")
            if not self.extract_epub(epub_path, temp_dir):
                return False
            
            # Find text files
            text_files = self.find_text_files(temp_dir)
            if not text_files:
                print("Error: No HTML files found", file=sys.stderr)
                return False
            
            print(f"Found {len(text_files)} content files")
            
            # Detect all languages
            all_languages = self.detect_all_languages(text_files)
            print(f"\nDetected languages: {', '.join(sorted(all_languages))}")
            
            if not all_languages:
                print("Warning: No languages detected!", file=sys.stderr)
                return False
            
            # Process files
            print(f"\nAdding hidden start/end markers...")
            print("-" * 70)
            
            total_elements = 0
            total_marked = defaultdict(int)
            
            for file_path in text_files:
                if self.skip_nav_files and any(skip in file_path.name.lower() 
                                              for skip in ['nav', 'cover', 'toc']):
                    self.log(f"Skipping: {file_path.name}")
                    continue
                
                elem_count, marked_counts = self.process_html_file(file_path, all_languages)
                total_elements += elem_count
                for lang, count in marked_counts.items():
                    total_marked[lang] += count
            
            print("-" * 70)
            print(f"\nProcessing complete:")
            print(f"  Total elements processed: {total_elements}")
            print(f"  Markers added by language:")
            for lang in sorted(total_marked.keys()):
                print(f"    {lang.upper()}: {total_marked[lang]} elements")
            
            # Generate @Voice DEELX configuration
            deelx_config = self.generate_deelx_regex_config(all_languages)
            
            print(f"\n{'='*70}")
            print("@VOICE DEELX REGEX CONFIGURATION")
            print(f"{'='*70}")
            print("\nAdd these patterns to @Voice (Pattern/Replace mode):\n")
            
            for lang, config in deelx_config.items():
                print(f"Language: {lang.upper()}")
                print(f"  Start marker: {config['start_marker']}")
                print(f"  End marker: {config['end_marker']}")
                print(f"  Pattern: {config['pattern_extract']}")
                print(f"  Replace: {config['replace_extract']}")
                print(f"  Cleanup Pattern: {config['pattern_cleanup']}")
                print(f"  Cleanup Replace: {config['replace_cleanup']}")
                print()
            
            # Save configuration
            config_output = output_path.parent / f"{output_path.stem}_@voice_config.txt"
            with open(config_output, 'w', encoding='utf-8') as f:
                f.write("@Voice DEELX Regex Configuration\n")
                f.write("="*70 + "\n\n")
                f.write("Add these patterns to @Voice:\n")
                f.write("1. Go to Settings → Text-to-Speech → Pattern/Replace\n")
                f.write("2. Add the following patterns:\n\n")
                
                for lang, config in deelx_config.items():
                    f.write(f"[{lang.upper()}]\n")
                    f.write(f"  Pattern: {config['pattern_extract']}\n")
                    f.write(f"  Replace: {config['replace_extract']}\n")
                    f.write(f"  Cleanup Pattern: {config['pattern_cleanup']}\n")
                    f.write(f"  Cleanup Replace: {config['replace_cleanup']}\n")
                    f.write(f"  Note: Reads text between {config['start_marker']} and {config['end_marker']}\n\n")
                
                f.write("\nUSAGE TIPS:\n")
                f.write("1. Enable 'Pattern/Replace' mode in @Voice\n")
                f.write("2. Enable only the language patterns you want to read\n")
                f.write("3. Disable patterns for languages you don't want to hear\n")
                f.write("4. The markers are hidden (display:none) so you won't see them\n")
            
            print(f"Configuration saved to: {config_output}")
            
            # Create new EPUB
            print(f"\nCreating output EPUB...")
            if not self.create_epub(temp_dir, output_path):
                return False
            
            return True

def main():
    # Configuration dictionary
    config = DEFAULT_CONFIG.copy()
    
    parser = argparse.ArgumentParser(
        description='Pre-process EPUB for @Voice with DEELX regex (start/end markers)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process with default settings (output: book_readaloud.epub)
  python epub2readaloud.py book.epub
  
  # Custom markers
  python epub2readaloud.py book.epub --marker-start "##{LANG}_START##" --marker-end "##{LANG}_END##"
  
  # Different source language
  python epub2readaloud.py book.epub --source-lang fr
  
  # Verbose mode
  python epub2readaloud.py book.epub --verbose

The script will:
  1. Detect all languages in your EPUB
  2. Add hidden start/end markers for each language
  3. Generate @Voice DEELX regex configuration
  4. Create a new EPUB in the same location with '_readaloud' suffix
        """
    )
    
    parser.add_argument('epub_file', help='Path to the input EPUB file')
    parser.add_argument('--source-lang', '-s', default=config['source_lang'],
                       help=f'Default source language (default: {config["source_lang"]})')
    parser.add_argument('--marker-start', default=config['marker_start'],
                       help=f'Start marker pattern with {{LANG}} (default: "{config["marker_start"]}")')
    parser.add_argument('--marker-end', default=config['marker_end'],
                       help=f'End marker pattern with {{LANG}} (default: "{config["marker_end"]}")')
    parser.add_argument('--output-suffix', default=config['output_suffix'],
                       help=f'Output file suffix (default: "{config["output_suffix"]}")')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print verbose output')
    parser.add_argument('--no-skip-nav', action='store_true',
                       help='Process navigation files as well')
    
    args = parser.parse_args()
    
    # Update configuration
    config['source_lang'] = args.source_lang
    config['marker_start'] = args.marker_start
    config['marker_end'] = args.marker_end
    config['output_suffix'] = args.output_suffix
    config['verbose'] = args.verbose
    config['skip_nav_files'] = not args.no_skip_nav
    
    # Process
    processor = EpubProcessor(config)
    success = processor.process_epub(args.epub_file)
    
    if success:
        epub_path = Path(args.epub_file)
        output_path = epub_path.parent / f"{epub_path.stem}{config['output_suffix']}{epub_path.suffix}"
        print(f"\n✅ Success! Processed EPUB saved to: {output_path}")
        print("\n📱 @Voice Setup:")
        print("  1. Open @Voice Aloud Reader")
        print("  2. Settings → Text-to-Speech → Pattern/Replace")
        print("  3. Enable 'Pattern/Replace mode'")
        print("  4. Add the patterns from the generated config file")
        print("  5. Enable only the language you want to read")
        print("\n💡 Tip: Keep patterns for other languages disabled until you need them")
    else:
        print("\n❌ Failed to process EPUB", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()