#!/usr/bin/env python3
"""
EPUB Manager - Simple version with defaults
Provides quick menu-driven access to EPUB operations with sensible defaults
"""

import glob
import os
import subprocess
import sys
from pathlib import Path

from transliteration.epub2post import EpubToPostConverter

# Now import the modules (we're in pipenv)
try:
    from transliteration.epubMergeFolder import (
        merge_multiple_epubs,
        prep_epubs_by_pattern,
    )
    from transliteration.epubMergeStack import prep_and_merge_simple
    from transliteration.epubSplitProcessor import process_epub_folder
    from transliteration.epubVersions import (
        get_language_from_epub,
        process_folder_remove_original,
        process_folder_transliterate_epub,
        process_folder_transliterate_epub_multilingual,
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the correct directory with transliteration package")
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path)
    sys.exit(1)


class SimpleEbookManager:
    def __init__(self, target_directory=None):
        self.default_merge_order = ['ru', 'de', 'en', 'ch', 'ar', 'hi', 'es', 'fr', 'el', 'he', 'id', 'it', 'ja', 'ko', 'la', 'pl', 'pt', 'sw', 'tr']
        self.supported_languages = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]
        
        # Language name to code mapping
        self.language_map = {
            "chinese": "ch",
            "russian": "ru", 
            "german": "de",
            "english": "en",
            "arabic": "ar",
            "hindi": "hi",
            "spanish": "es",
            "french": "fr",
            "greek": "el",
            "hebrew": "he",
            "indonesian": "id",
            "italian": "it",
            "japanese": "ja",
            "korean": "ko",
            "latin": "la",
            "polish": "pl",
            "portuguese": "pt",
            "swahili": "sw",
            "turkish": "tr"
        }
        
        # Use target_directory if provided, otherwise use current directory
        if target_directory and os.path.exists(target_directory):
            self.current_directory = target_directory
            print(f"Using target directory: {target_directory}")
        else:
            self.current_directory = os.getcwd()
            print(f"Using current directory: {self.current_directory}")
        
        # Use target_directory if provided, otherwise use current directory
        if target_directory and os.path.exists(target_directory):
            self.current_directory = target_directory
            print(f"Using target directory: {target_directory}")
        else:
            self.current_directory = os.getcwd()
            print(f"Using current directory: {self.current_directory}")
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_menu(self):
        """Display the main menu"""
        self.clear_screen()
        print("=" * 50)
        print("          EPUB MANAGER - SIMPLE")
        print("=" * 50)
        print(f"Current directory: {self.current_directory}")
        print(f"Pipenv active: {'Yes' if os.environ.get('PIPENV_ACTIVE') else 'No'}")
        print()
        print("1. Split EPUB files")
        print("2. Remove original text") 
        print("3. Transliterate EPUBs (Default - Main Language Detection)")
        print("4. Merge-compose EPUBs by Languages/Line by Line")
        print("5. Simple Merge/Epub Stacking")
        print("6. Convert EPUBs to Blog Posts")
        print("7. Advanced Options")
        print("0. Exit")
        print()
    
    def get_user_choice(self):
        """Get user menu choice"""
        try:
            choice = input("Select an option: ").strip()
            return choice
        except KeyboardInterrupt:
            return '0'

    def detect_available_languages(self, folder_path):
        """Detect available languages from EPUB files in folder"""
        epub_files = glob.glob(os.path.join(folder_path, "*.epub"))
        available_languages = set()
        
        for epub_file in epub_files:
            try:
                language = get_language_from_epub(epub_file)
                if language:
                    available_languages.add(language)
            except Exception as e:
                print(f"Warning: Could not detect language for {epub_file}: {e}")
        
        return sorted(available_languages)

    def get_smart_merge_order(self, folder_path):
        """Create merge order based on available languages and preferred order"""
        available_langs = self.detect_available_languages(folder_path)
        if not available_langs:
            return self.default_merge_order
        
        print(f"Available languages detected: {available_langs}")
        
        # Convert language names to codes
        available_codes = set()
        for lang_name in available_langs:
            code = self.language_map.get(lang_name.lower())
            if code:
                available_codes.add(code)
            else:
                # If no mapping found, try to use first 2 letters as fallback
                code = lang_name[:2].lower()
                available_codes.add(code)
                print(f"Warning: No mapping for '{lang_name}', using '{code}' as code")
        
        print(f"Available language codes: {sorted(available_codes)}")
        
        # Filter default merge order to only include available language codes
        smart_order = [lang for lang in self.default_merge_order if lang in available_codes]
        
        # Add any remaining available languages that aren't in default order
        for lang in available_codes:
            if lang not in smart_order:
                smart_order.append(lang)
        
        return smart_order

    def split_epubs(self):
        """Split EPUB files with defaults"""
        print("\n=== Split EPUB Files ===")
        print("Using current directory as both input and output")
        print("File pattern: *-db-*.epub")
        
        input_folder = self.current_directory
        output_folder = self.current_directory
        
        try:
            print(f"Processing EPUBs from {input_folder}...")
            process_epub_folder(input_folder, output_folder)
            print("Split operation completed successfully!")
        except Exception as e:
            print(f"Error during split operation: {e}")
        
        input("Press Enter to continue...")
    
    def remove_original(self):
        """Remove original text from EPUBs with defaults"""
        print("\n=== Remove Original Text ===")
        print("Using current directory")
        
        folder_path = self.current_directory
        
        try:
            print(f"Removing original text from EPUBs in {folder_path}...")
            process_folder_remove_original(folder_path)
            print("Remove original operation completed successfully!")
        except Exception as e:
            print(f"Error during remove original operation: {e}")
        
        input("Press Enter to continue...")
    
    def transliterate_epubs(self):
        """Transliterate EPUBs with defaults (Main Language Detection)"""
        print("\n=== Transliterate EPUBs ===")
        print("Mode: Main Language Detection (Default)")
        print("Detects the primary language of each EPUB and transliterates it")
        print("Using current directory")
        
        folder_path = self.current_directory
        
        try:
            print(f"Transliterating EPUBs in {folder_path} using main language detection...")
            process_folder_transliterate_epub(folder_path)
            print("Transliteration completed successfully!")
        except Exception as e:
            print(f"Error during transliteration: {e}")
        
        input("Press Enter to continue...")
    
    def merge_epubs(self):
        """Merge EPUBs by pattern with defaults"""
        print("\n=== Merge EPUBs by Pattern ===")
        print("Using current directory")
        print("File pattern: *-db-*.epub")
        
        folder_path = self.current_directory
        file_patterns = ['*-db-*.epub']
        
        # Use smart merge order based on available languages
        merge_order = self.get_smart_merge_order(folder_path)
        print(f"Smart merge order: {merge_order}")
        
        output_suffix = "ml"
        
        try:
            print(f"Merging EPUBs in {folder_path}...")
            epub_paths, output_path, languages, final_merge_order = prep_epubs_by_pattern(
                folder_path=folder_path,
                file_patterns=file_patterns,
                merge_order=merge_order,
                output_suffix=output_suffix
            )
            
            if epub_paths:
                print(f"Found {len(epub_paths)} files to merge")
                print(f"Languages: {languages}")
                print(f"Final merge order: {final_merge_order}")
                
                merge_multiple_epubs(epub_paths, output_path, languages, final_merge_order)
                print("Merge operation completed successfully!")
            else:
                print("No files found matching the pattern '*-db-*.epub'!")
        
        except Exception as e:
            print(f"Error during merge operation: {e}")
        
        input("Press Enter to continue...")
    
    def simple_merge(self):
        """Simple merge operation with defaults"""
        print("\n=== Simple Merge ===")
        print("Using current directory")
        print("File pattern: *-db-*.epub")
        
        folder_path = self.current_directory
        file_patterns = ['*-db-*.epub']
        
        # Use smart merge order based on available languages
        merge_order = self.get_smart_merge_order(folder_path)
        print(f"Smart merge order: {merge_order}")
        
        output_suffix = "ml-simple"
        
        try:
            print(f"Simple merge of EPUBs in {folder_path}...")
            prep_and_merge_simple(
                folder_path=folder_path,
                file_patterns=file_patterns,
                merge_order=merge_order,
                output_suffix=output_suffix
            )
            print("Simple merge completed successfully!")
        except Exception as e:
            print(f"Error during simple merge: {e}")
        
        input("Press Enter to continue...")
        
    def convert_epubs_to_posts(self):
        """Convert EPUB files to markdown posts"""
        print("\n=== Convert EPUBs to Posts ===")
        print("Using current directory as source")
        
        folder_path = self.current_directory
        
        print("\nSelect destination for posts:")
        print("1. /home/zaya/Downloads/Zayas/zayaslanguage/src/posts")
        print("2. /home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts")
        print("3. Custom path")
        
        dest_choice = input("Select destination (1-3, Enter for default 2): ").strip()
        
        if dest_choice == "1":
            posts_dir = "/home/zaya/Downloads/Zayas/zayaslanguage/src/posts"
        elif dest_choice == "3":
            posts_dir = input("Enter custom posts directory path: ").strip()
            if not posts_dir:
                print("No path provided, using default")
                posts_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts"
        else:  # Default to option 2
            posts_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts"
        
        print(f"\nPosts will be saved to: {posts_dir}")
        
        # Image directory is fixed based on zayaweb structure
        images_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/static/css/img"
        
        try:
            converter = EpubToPostConverter(
                posts_dir=posts_dir,
                images_base_dir=images_dir,
                scripts_dir="/home/zaya/Downloads/Zayas/zayaweb/apps/web/scripts"
            )
            
            # Ask for pattern
            pattern = input("\nEnter file pattern (Enter for '*.epub'): ").strip() or "*.epub"
            
            # Ask if they want to review each file
            review_each = input("Review each file before conversion? (y/N): ").strip().lower() == 'y'
            
            if review_each:
                import glob
                epub_files = sorted(glob.glob(os.path.join(folder_path, pattern)))
                
                if not epub_files:
                    print(f"No EPUB files found matching '{pattern}'")
                else:
                    print(f"\nFound {len(epub_files)} EPUB files:")
                    for i, epub_file in enumerate(epub_files, 1):
                        print(f"{i}. {os.path.basename(epub_file)}")
                    
                    for epub_file in epub_files:
                        print(f"\n{'-'*50}")
                        print(f"Processing: {os.path.basename(epub_file)}")
                        proceed = input("Convert this file? (y/N): ").strip().lower()
                        
                        if proceed == 'y':
                            # Ask for custom title/slug
                            use_custom = input("Use custom title/slug? (y/N): ").strip().lower()
                            custom_title = None
                            custom_slug = None
                            
                            if use_custom == 'y':
                                custom_title = input("Enter title (Enter to auto-detect): ").strip() or None
                                custom_slug = input("Enter slug (Enter to generate): ").strip() or None
                            
                            converter.convert_epub_to_post(
                                epub_file,
                                custom_title=custom_title,
                                custom_slug=custom_slug
                            )
                        else:
                            print("Skipping...")
            else:
                # Bulk convert all
                results = converter.convert_folder(folder_path, pattern)
                
                # Show summary
                successful = [r for r in results if r['success']]
                if successful:
                    print(f"\n✅ Successfully converted {len(successful)} EPUBs to posts")
            
            print("\nConversion process completed!")
            
        except Exception as e:
            print(f"Error during conversion: {e}")
        
        input("Press Enter to continue...")
    
    def run(self):
        """Main program loop"""
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                self.split_epubs()
            elif choice == '2':
                self.remove_original()
            elif choice == '3':
                self.transliterate_epubs()
            elif choice == '4':
                self.merge_epubs()
            elif choice == '5':
                self.simple_merge()
            elif choice == '6':
                self.convert_epubs_to_posts()
            elif choice == '7':
                # Launch advanced version
                advanced_manager = EpubManagerWithOptions(self.current_directory)
                advanced_manager.run()
            else:
                print("Invalid choice! Please try again.")
                input("Press Enter to continue...")


class EpubManagerWithOptions:
    """Advanced version with customizable options"""
    
    def __init__(self, target_directory=None):
        self.default_merge_order = ['ru', 'de', 'en', 'ch', 'ar', 'hi', 'es', 'fr', 'el', 'he', 'id', 'it', 'ja', 'ko', 'la', 'pl', 'pt', 'sw', 'tr']
        self.supported_languages = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]
        
        # Language name to code mapping
        self.language_map = {
            "chinese": "ch",
            "russian": "ru", 
            "german": "de",
            "english": "en",
            "arabic": "ar",
            "hindi": "hi",
            "spanish": "es",
            "french": "fr",
            "greek": "el",
            "hebrew": "he",
            "indonesian": "id",
            "italian": "it",
            "japanese": "ja",
            "korean": "ko",
            "latin": "la",
            "polish": "pl",
            "portuguese": "pt",
            "swahili": "sw",
            "turkish": "tr"
        }
        
        # Use target_directory if provided, otherwise use current directory
        if target_directory and os.path.exists(target_directory):
            self.current_directory = target_directory
        else:
            self.current_directory = os.getcwd()
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_menu(self):
        self.clear_screen()
        print("=" * 50)
        print("       EPUB MANAGER - ADVANCED OPTIONS")
        print("=" * 50)
        print(f"Current directory: {self.current_directory}")
        print()
        print("1. Split EPUB files (with options)")
        print("2. Remove original text (with options)")
        print("3. Transliterate (with options)")
        print("4. Merge-compose (with options)")
        print("5. Simple Merge (with options)")
        print("6. Convert EPUBs to Posts")
        print("7. Back to Simple Manager")
        print("0. Exit")
        print()
    
    def detect_available_languages(self, folder_path):
        """Detect available languages from EPUB files in folder"""
        epub_files = glob.glob(os.path.join(folder_path, "*.epub"))
        available_languages = set()
        
        for epub_file in epub_files:
            try:
                language = get_language_from_epub(epub_file)
                if language:
                    available_languages.add(language)
            except Exception as e:
                print(f"Warning: Could not detect language for {epub_file}: {e}")
        
        return sorted(available_languages)

    def get_smart_merge_order(self, folder_path, custom_order=None):
        """Create merge order based on available languages and preferred order"""
        available_langs = self.detect_available_languages(folder_path)
        if not available_langs:
            return custom_order or self.default_merge_order
        
        print(f"Available languages detected: {available_langs}")
        
        # Convert language names to codes
        available_codes = set()
        for lang_name in available_langs:
            code = self.language_map.get(lang_name.lower())
            if code:
                available_codes.add(code)
            else:
                # If no mapping found, try to use first 2 letters as fallback
                code = lang_name[:2].lower()
                available_codes.add(code)
                print(f"Warning: No mapping for '{lang_name}', using '{code}' as code")
        
        print(f"Available language codes: {sorted(available_codes)}")
        
        base_order = custom_order if custom_order else self.default_merge_order
        
        # Filter base order to only include available language codes
        smart_order = [lang for lang in base_order if lang in available_codes]
        
        # Add any remaining available languages that aren't in base order
        for lang in available_codes:
            if lang not in smart_order:
                smart_order.append(lang)
        
        return smart_order

    def get_file_patterns(self):
        print("\nFile patterns (e.g., '*-db-*.epub', 'book-*.epub')")
        print("Leave empty for default ['*-db-*.epub']")
        patterns_input = input("Enter patterns (comma separated): ").strip()
        
        if patterns_input:
            return [p.strip() for p in patterns_input.split(',')]
        else:
            return ['*-db-*.epub']
    
    def get_merge_order(self, folder_path):
        print(f"\nDefault merge order: {self.default_merge_order}")
        
        # Show available languages
        available_langs = self.detect_available_languages(folder_path)
        if available_langs:
            print(f"Available languages: {available_langs}")
        
        print("Leave empty to use smart order, or specify custom order")
        order_input = input("Enter merge order (comma separated): ").strip()
        
        if order_input:
            custom_order = [lang.strip() for lang in order_input.split(',')]
            return self.get_smart_merge_order(folder_path, custom_order)
        else:
            return self.get_smart_merge_order(folder_path)
    
    def split_epubs(self):
        print("\n=== Split EPUB Files (Advanced) ===")
        
        input_folder = input(f"Enter input folder (Enter for {self.current_directory}): ").strip() or self.current_directory
        output_folder = input("Enter output folder (Enter for 'split_output'): ").strip() or "split_output"
        
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            print(f"Processing EPUBs from {input_folder} to {output_folder}...")
            process_epub_folder(input_folder, output_folder)
            print("Split operation completed successfully!")
        except Exception as e:
            print(f"Error: {e}")
        
        input("Press Enter to continue...")
    
    def remove_original(self):
        print("\n=== Remove Original Text (Advanced) ===")
        folder_path = input(f"Enter folder path (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        try:
            print(f"Removing original text from EPUBs in {folder_path}...")
            process_folder_remove_original(folder_path)
            print("Operation completed successfully!")
        except Exception as e:
            print(f"Error: {e}")
        
        input("Press Enter to continue...")
    
    def transliterate_epubs(self):
        print("\n=== Transliterate (Advanced) ===")
        folder_path = input(f"Enter folder path (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        print("\nSelect transliteration mode:")
        print("1. Main Language Detection (Default)")
        print("   - Detects the primary language of the EPUB")
        print("   - Transliterates the entire content")
        print("2. Multilingual Sentence-by-Sentence")
        print("   - Processes each sentence individually")
        print("   - Detects language per sentence and transliterates if applicable")
        
        mode_choice = input("Select mode (1 or 2, Enter for default): ").strip()
        
        try:
            if mode_choice == "2":
                print("Using multilingual sentence-by-sentence transliteration...")
                process_folder_transliterate_epub_multilingual(folder_path)
                print("Multilingual transliteration completed successfully!")
            else:
                print("Using main language detection transliteration...")
                process_folder_transliterate_epub(folder_path)
                print("Main language transliteration completed successfully!")
                
        except Exception as e:
            print(f"Error during transliteration: {e}")
        
        input("Press Enter to continue...")
    
    def merge_epubs(self):
        print("\n=== Merge-compose (Advanced) ===")
        folder_path = input(f"Enter folder path (Enter for {self.current_directory}): ").strip() or self.current_directory
        file_patterns = self.get_file_patterns()
        merge_order = self.get_merge_order(folder_path)
        output_suffix = input("Enter output suffix (Enter for 'ml'): ").strip() or "ml"
        
        try:
            print(f"Using merge order: {merge_order}")
            epub_paths, output_path, languages, final_merge_order = prep_epubs_by_pattern(
                folder_path=folder_path,
                file_patterns=file_patterns,
                merge_order=merge_order,
                output_suffix=output_suffix
            )
            
            if epub_paths:
                print(f"Found {len(epub_paths)} files to merge")
                merge_multiple_epubs(epub_paths, output_path, languages, final_merge_order)
                print("Merge operation completed successfully!")
            else:
                print("No files found matching patterns!")
        
        except Exception as e:
            print(f"Error: {e}")
        
        input("Press Enter to continue...")
    
    def simple_merge(self):
        print("\n=== Simple Merge (Advanced) ===")
        folder_path = input(f"Enter folder path (Enter for {self.current_directory}): ").strip() or self.current_directory
        file_patterns = self.get_file_patterns()
        merge_order = self.get_merge_order(folder_path)
        output_suffix = input("Enter output suffix (Enter for 'ml-simple'): ").strip() or "ml-simple"
        
        try:
            print(f"Using merge order: {merge_order}")
            prep_and_merge_simple(
                folder_path=folder_path,
                file_patterns=file_patterns,
                merge_order=merge_order,
                output_suffix=output_suffix
            )
            print("Simple merge completed successfully!")
        except Exception as e:
            print(f"Error: {e}")
        
        input("Press Enter to continue...")
    
    def convert_epubs_to_posts_advanced(self):
        """Convert EPUB files to markdown posts with advanced options"""
        print("\n=== Convert EPUBs to Posts (Advanced) ===")
        
        folder_path = input(f"Enter source folder (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        print("\nSelect destination for posts:")
        print("1. /home/zaya/Downloads/Zayas/zayaslanguage/src/posts")
        print("2. /home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts")
        print("3. Custom path")
        
        dest_choice = input("Select destination (1-3): ").strip()
        
        if dest_choice == "1":
            posts_dir = "/home/zaya/Downloads/Zayas/zayaslanguage/src/posts"
        elif dest_choice == "2":
            posts_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts"
        elif dest_choice == "3":
            posts_dir = input("Enter custom posts directory path: ").strip()
            if not posts_dir:
                print("No path provided, using default")
                posts_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts"
        else:
            print("Invalid choice, using default")
            posts_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/src/posts"
        
        images_dir = input("Enter images base directory (Enter for default): ").strip()
        if not images_dir:
            images_dir = "/home/zaya/Downloads/Zayas/zayaweb/apps/web/static/css/img"
        
        pattern = input("Enter file pattern (Enter for '*.epub'): ").strip() or "*.epub"
        
        # Additional options
        print("\nConversion options:")
        create_backup = input("Create backup of original EPUBs? (y/N): ").strip().lower() == 'y'
        delete_after = input("Delete EPUB after successful conversion? (y/N): ").strip().lower() == 'y'
        
        try:
            converter = EpubToPostConverter(
                posts_dir=posts_dir,
                images_base_dir=images_dir,
                scripts_dir="/home/zaya/Downloads/Zayas/zayaweb/apps/web/scripts"
            )
            
            results = converter.convert_folder(folder_path, pattern)
            
            # Handle post-conversion options
            if delete_after:
                for result in results:
                    if result['success']:
                        try:
                            os.remove(result['epub'])
                            print(f"Deleted: {result['epub']}")
                        except Exception as e:
                            print(f"Error deleting {result['epub']}: {e}")
            
            print("\nConversion completed!")
            
        except Exception as e:
            print(f"Error during conversion: {e}")
        
        input("Press Enter to continue...")    
    
    def run(self):
        while True:
            self.display_menu()
            choice = input("Select an option: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                sys.exit(0)
            elif choice == '1':
                self.split_epubs()
            elif choice == '2':
                self.remove_original()
            elif choice == '3':
                self.transliterate_epubs()
            elif choice == '4':
                self.merge_epubs()
            elif choice == '5':
                self.simple_merge()
            elif choice == '6':
                self.convert_epubs_to_posts_advanced()
            elif choice == '7':
                return  # Go back to simple manager
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    try:
        # Check if a directory was passed as first argument
        target_directory = None
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            target_directory = sys.argv[1]
            print(f"Target directory provided: {target_directory}")
        
        manager = SimpleEbookManager(target_directory)
        manager.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()