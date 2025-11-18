#!/usr/bin/env python3
"""
EPUB Manager - Simple version with defaults
Provides quick menu-driven access to EPUB operations with sensible defaults
"""

import os
import subprocess
import sys
from pathlib import Path

# def ensure_pipenv():
#     """Check if we're in pipenv shell and activate if not"""
#     if not os.environ.get('PIPENV_ACTIVE'):
#         print("Pipenv not active. Activating pipenv shell...")
        
#         # Get the directory of this script
#         script_dir = Path(__file__).parent.parent
#         os.chdir(script_dir)
        
#         # Try to activate pipenv
#         try:
#             # First check if pipenv is available
#             result = subprocess.run(['pipenv', '--version'], capture_output=True, text=True)
#             if result.returncode != 0:
#                 print("Error: pipenv is not installed or not in PATH")
#                 print("Please install pipenv: pip install pipenv")
#                 sys.exit(1)
            
#             # Run the script within pipenv
#             print(f"Running in directory: {os.getcwd()}")
#             subprocess.run(['pipenv', 'run', 'python', '-m', 'transliteration.epubManager'])
#             sys.exit(0)
            
#         except Exception as e:
#             print(f"Error activating pipenv: {e}")
#             print("Please run manually: pipenv shell")
#             sys.exit(1)

# # Check pipenv before importing modules
# ensure_pipenv()

# Now import the modules (we're in pipenv)
try:
    from transliteration.epubMergeFolder import (
        merge_multiple_epubs,
        prep_epubs_by_pattern,
    )
    from transliteration.epubMergeStack import prep_and_merge_simple
    from transliteration.epubSplitProcessor import process_epub_folder
    from transliteration.epubVersions import (
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
    def __init__(self):
        self.default_merge_order = ['ru', 'de', 'en', 'ch', 'ar', 'hi', 'es', 'fr', 'el', 'he', 'id', 'it', 'ja', 'ko', 'la', 'pl', 'pt', 'sw', 'tr']
        self.supported_languages = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]
        self.current_directory = os.getcwd()
        
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
        print("6. Advanced Options")
        print("0. Exit")
        print()
    
    def get_user_choice(self):
        """Get user menu choice"""
        try:
            choice = input("Select an option: ").strip()
            return choice
        except KeyboardInterrupt:
            return '0'

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
        print(f"Merge order: {self.default_merge_order}")
        print("Output suffix: ml")
        
        folder_path = self.current_directory
        file_patterns = ['*-db-*.epub']
        merge_order = self.default_merge_order
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
                print(f"Merge order: {final_merge_order}")
                
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
        print(f"Merge order: {self.default_merge_order}")
        print("Output suffix: ml-simple")
        
        folder_path = self.current_directory
        file_patterns = ['*-db-*.epub']
        merge_order = self.default_merge_order
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
                # Launch advanced version
                advanced_manager = EpubManagerWithOptions()
                advanced_manager.run()
            else:
                print("Invalid choice! Please try again.")
                input("Press Enter to continue...")


class EpubManagerWithOptions:
    """Advanced version with customizable options"""
    
    def __init__(self):
        self.default_merge_order = ['ru', 'de', 'en', 'ch', 'ar', 'hi', 'es', 'fr', 'el', 'he', 'id', 'it', 'ja', 'ko', 'la', 'pl', 'pt', 'sw', 'tr']
        self.supported_languages = ["japanese", "korean", "chinese", "hindi", "arabic", "russian"]
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
        print("6. Back to Simple Manager")
        print("0. Exit")
        print()
    
    def get_file_patterns(self):
        print("\nFile patterns (e.g., '*-db-*.epub', 'book-*.epub')")
        print("Leave empty for default ['*-db-*.epub']")
        patterns_input = input("Enter patterns (comma separated): ").strip()
        
        if patterns_input:
            return [p.strip() for p in patterns_input.split(',')]
        else:
            return ['*-db-*.epub']
    
    def get_merge_order(self):
        print(f"\nDefault merge order: {self.default_merge_order}")
        print("Leave empty to use default, or specify custom order")
        order_input = input("Enter merge order (comma separated): ").strip()
        
        if order_input:
            return [lang.strip() for lang in order_input.split(',')]
        else:
            return self.default_merge_order
    
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
        merge_order = self.get_merge_order()
        output_suffix = input("Enter output suffix (Enter for 'ml'): ").strip() or "ml"
        
        try:
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
        merge_order = self.get_merge_order()
        output_suffix = input("Enter output suffix (Enter for 'ml-simple'): ").strip() or "ml-simple"
        
        try:
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
                return  # Go back to simple manager
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    try:
        manager = SimpleEbookManager()
        manager.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()