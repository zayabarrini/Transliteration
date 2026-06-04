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
    from transliteration.epubMergeFolder import (merge_multiple_epubs,
                                                 prep_epubs_by_pattern)
    from transliteration.epubMergeStack import prep_and_merge_simple
    from transliteration.epubSplitProcessor import process_epub_folder
    from transliteration.epubVersions import (
        get_language_from_epub, process_folder_remove_original,
        process_folder_transliterate_epub,
        process_folder_transliterate_epub_multilingual)
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the correct directory with transliteration package")
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path)
    sys.exit(1)


class SimpleEbookManager:
    def __init__(self, target_directory=None):
        self.default_merge_order = ['ru', 'de', 'en', 'ch', 'ar', 'hi', 'es', 'fr', 'el', 'he', 'id', 'it', 'ja', 'ko', 'la', 'pl', 'pt', 'sw', 'th', 'tr', 'bn', 'ur', 'pa', 'mr', 'te', 'ta', 'vi']
        self.supported_languages = ["japanese", "korean", "chinese", "hindi", "arabic", "russian", "german", "english", "spanish", "french", "greek", "hebrew", "indonesian", "italian", "latin", "polish", "portuguese", "swahili", "turkish", "bengali", "urdu", "punjabi", "marathi", "telugu", "tamil", "vietnamese"]        
        
        # Language name to code mapping
        self.language_map = {
            "chinese": "zh",
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
            "turkish": "tr",
            "bengali": "bn",
            "urdu": "ur",
            "punjabi": "pa",
            "marathi": "mr",
            "telugu": "te",
            "tamil": "ta",
            "vietnamese": "vi"
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
        os.system("cls" if os.name == "nt" else "clear")

    def convert_epub_to_json_ordered(self):
        """Convert ordered multilingual EPUB to JSON with specified language order"""
        print("\n=== Convert Ordered Multilingual EPUB to JSON ===")
        print("This is for EPUBs where paragraphs appear in a consistent language order")
        print("without explicit language attributes.")
        print("\nJSON files will be saved to:")
        print("  /home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml/")
        
        folder_path = input(f"Enter folder containing EPUB files (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        # Find all EPUB files
        epub_files = []
        for ext in ['*.epub', '*.EPUB']:
            epub_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        # Specifically look for Milano_Multilingual.epub
        milano_file = None
        other_files = []
        
        for f in epub_files:
            if 'Milano_Multilingual' in f or 'milano_multilingual' in f.lower():
                milano_file = f
            else:
                other_files.append(f)
        
        if milano_file:
            print(f"\nFound Milano_Multilingual.epub!")
            selected_files = [milano_file]
            
            # Ask if they want to process other files
            if other_files:
                process_others = input(f"\nAlso found {len(other_files)} other EPUB files. Process them too? (y/N): ").strip().lower()
                if process_others == 'y':
                    selected_files.extend(other_files)
        else:
            # Show all files
            epub_files = sorted(epub_files)
            if not epub_files:
                print("No EPUB files found!")
                input("Press Enter to continue...")
                return
            
            print(f"\nFound {len(epub_files)} EPUB files:")
            for i, epub_file in enumerate(epub_files, 1):
                print(f"{i}. {os.path.basename(epub_file)}")
            
            print(f"{len(epub_files)+1}. Process all")
            print("0. Cancel")
            
            choice = input("\nSelect files to process: ").strip()
            
            if choice == '0':
                return
            
            selected_files = []
            if choice == str(len(epub_files) + 1):
                selected_files = epub_files
            else:
                indices = [int(x.strip()) for x in choice.split(',') if x.strip()]
                for idx in indices:
                    if 1 <= idx <= len(epub_files):
                        selected_files.append(epub_files[idx-1])
        
        if not selected_files:
            print("No valid files selected")
            input("Press Enter to continue...")
            return
        
        # Default language order for Milano
        default_order = ['en', 'de', 'ru', 'ar', 'hi', 'zh', 'ja', 'ko', 'fr', 'pt', 'it', 'es', 'pl', 'el', 'he']
        
        print(f"\nDefault language order: {', '.join(default_order)}")
        use_default = input("Use this language order? (Y/n): ").strip().lower()
        
        language_order = default_order
        if use_default == 'n':
            custom_order = input("Enter comma-separated language codes in order: ").strip()
            if custom_order:
                language_order = [lang.strip() for lang in custom_order.split(',')]
        
        print(f"\nProcessing {len(selected_files)} files with language order: {', '.join(language_order)}")
        
        # Path to epub2jsonOrdered.py script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        epub2json_script = os.path.join(script_dir, "epub2jsonOrdered.py")
        
        if not os.path.exists(epub2json_script):
            print(f"Error: Could not find epub2jsonOrdered.py at {epub2json_script}")
            input("Press Enter to continue...")
            return
        
        success_count = 0
        for epub_file in selected_files:
            print(f"\n{'-'*50}")
            print(f"Processing: {os.path.basename(epub_file)}")
            
            # Build lang-order argument
            lang_order_arg = ','.join(language_order)
            
            try:
                cmd = [
                    sys.executable, 
                    epub2json_script, 
                    epub_file,
                    '--output-base',
                    '/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml',
                    '--lang-order',
                    lang_order_arg
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Success: {os.path.basename(epub_file)}")
                    # Extract summary from output
                    for line in result.stdout.split('\n'):
                        if 'Complete groups' in line or 'Total translation groups' in line:
                            print(f"   {line.strip()}")
                    success_count += 1
                else:
                    print(f"❌ Failed: {os.path.basename(epub_file)}")
                    if result.stderr:
                        print(f"   Error: {result.stderr[:200]}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        print(f"\n{'='*50}")
        print(f"Successfully processed: {success_count} / {len(selected_files)}")
        print(f"JSON files saved to: /home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml/")
        input("\nPress Enter to continue...")

    def process_for_readaloud(self):
        """Process EPUB for @Voice read-aloud functionality"""
        print("\n=== Process EPUB for @Voice Read Aloud ===")
        print("This adds hidden language markers for multilingual TTS support")
        print("Creates a version optimized for @Voice Aloud Reader\n")
        
        folder_path = input(f"Enter folder containing EPUB files (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        # Find all EPUB files
        epub_files = []
        for ext in ['*.epub', '*.EPUB']:
            epub_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        epub_files = sorted(epub_files)
        
        if not epub_files:
            print("No EPUB files found!")
            input("Press Enter to continue...")
            return
        
        print(f"\nFound {len(epub_files)} EPUB files:")
        for i, epub_file in enumerate(epub_files, 1):
            print(f"{i}. {os.path.basename(epub_file)}")
        
        print(f"{len(epub_files)+1}. Process all")
        print("0. Cancel")
        
        choice = input("\nSelect files to process: ").strip()
        
        if choice == '0':
            return
        
        selected_files = []
        if choice == str(len(epub_files) + 1):
            selected_files = epub_files
        else:
            indices = [int(x.strip()) for x in choice.split(',') if x.strip()]
            for idx in indices:
                if 1 <= idx <= len(epub_files):
                    selected_files.append(epub_files[idx-1])
        
        if not selected_files:
            print("No valid files selected")
            input("Press Enter to continue...")
            return
        
        # Ask for configuration options
        print("\nConfiguration Options:")
        print("-" * 40)
        
        # Source language
        source_lang = input(f"Source language code (Enter for 'en'): ").strip() or 'en'
        
        # Marker patterns
        print("\nMarker patterns (use {LANG} as placeholder for language code)")
        print(f"Default start marker: '[{{LANG}}]'")
        use_custom_markers = input("Use custom markers? (y/N): ").strip().lower()
        
        marker_start = None
        marker_end = None
        
        if use_custom_markers == 'y':
            marker_start = input("Start marker pattern: ").strip()
            marker_end = input("End marker pattern: ").strip()
        
        # Verbose mode
        verbose = input("\nVerbose output? (y/N): ").strip().lower() == 'y'
        
        # Output suffix
        output_suffix = input(f"Output suffix (Enter for '_readaloud'): ").strip() or '_readaloud'
        
        # Path to epub2readAloud.py script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        readaloud_script = os.path.join(script_dir, "epub2readAloud.py")
        
        if not os.path.exists(readaloud_script):
            # Try current directory
            readaloud_script = os.path.join(os.getcwd(), "epub2readAloud.py")
            if not os.path.exists(readaloud_script):
                print(f"Error: Could not find epub2readAloud.py")
                print(f"Expected at: {script_dir}/epub2readAloud.py")
                input("Press Enter to continue...")
                return
        
        print(f"\n{'='*60}")
        print(f"Processing {len(selected_files)} file(s)")
        print(f"{'='*60}")
        
        success_count = 0
        failed_files = []
        
        for i, epub_file in enumerate(selected_files, 1):
            filename = os.path.basename(epub_file)
            print(f"\n[{i}/{len(selected_files)}] Processing: {filename}")
            print("-" * 40)
            
            try:
                # Build command
                cmd = [sys.executable, readaloud_script, epub_file]
                
                # Add options
                cmd.extend(['--source-lang', source_lang])
                
                if marker_start:
                    cmd.extend(['--marker-start', marker_start])
                if marker_end:
                    cmd.extend(['--marker-end', marker_end])
                if output_suffix != '_readaloud':
                    cmd.extend(['--output-suffix', output_suffix])
                if verbose:
                    cmd.append('--verbose')
                
                # Run the command
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Success: {filename}")
                    # Show detected languages from output
                    for line in result.stdout.split('\n'):
                        if 'Detected languages:' in line:
                            print(f"   {line.strip()}")
                        elif 'Markers added by language:' in line:
                            print(f"   {line.strip()}")
                            # Also show next few lines for language breakdown
                    success_count += 1
                else:
                    print(f"❌ Failed: {filename}")
                    if result.stderr:
                        # Show first few lines of error
                        error_lines = result.stderr.strip().split('\n')[:3]
                        for line in error_lines:
                            print(f"   Error: {line}")
                    failed_files.append(filename)
                    
            except Exception as e:
                print(f"❌ Exception processing {filename}: {e}")
                failed_files.append(filename)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Successfully processed: {success_count} / {len(selected_files)}")
        
        if failed_files:
            print(f"\nFailed files ({len(failed_files)}):")
            for f in failed_files:
                print(f"  - {f}")
        
        # Show output location and config files
        if success_count > 0:
            print(f"\n📱 Output files created in: {folder_path}")
            print(f"   Pattern: *{output_suffix}.epub")
            print(f"\n📄 @Voice configuration files saved alongside each processed EPUB")
            print(f"   Look for: *_@voice_config.txt")
            print("\n💡 Next steps:")
            print("   1. Open @Voice Aloud Reader")
            print("   2. Settings → Text-to-Speech → Pattern/Replace")
            print("   3. Enable 'Pattern/Replace mode'")
            print("   4. Add the patterns from the generated config file")
            print("   5. Enable only the language patterns you want to hear")
        
        input("\nPress Enter to continue...")

    def display_menu(self):
        """Display the main menu"""
        self.clear_screen()
        print("=" * 50)
        print("          EPUB MANAGER - SIMPLE")
        print("=" * 50)
        print(f"Current directory: {self.current_directory}")
        print(f"Pipenv active: {'Yes' if os.environ.get('PIPENV_ACTIVE') else 'No'}")
        print()
        print("1. Split p into sentences")
        print("2. Remove original text")
        print("3. Transliterate EPUBs (Default - Main Language Detection)")
        print("4. Merge-compose EPUBs by Languages/Line by Line")
        print("5. Simple Merge/Epub Stacking")
        print("6. Convert EPUBs to Blog Posts")
        print("7. Convert EPUB to JSON (for language learning readers)")
        print("8. Convert Multilingual EPUB to JSON (all languages)")
        print("9. Convert Ordered Multilingual EPUB to JSON (specify language order)")
        print("10. Process for @Voice Read Aloud (add language markers)")
        print("11. Advanced Options")
        print("0. Exit")
        print()

    def get_user_choice(self):
        """Get user menu choice"""
        try:
            choice = input("Select an option: ").strip()
            return choice
        except KeyboardInterrupt:
            return "0"

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
    
    def convert_epub_to_json_multilingual(self):
        """Convert multilingual EPUB files to JSON with all languages"""
        print("\n=== Convert Multilingual EPUB to JSON ===")
        print("This will create a single JSON file with all language translations")
        print("JSON files will be saved to:")
        print("  /home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml/")
        
        folder_path = input(f"Enter folder containing EPUB files (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        # Find all EPUB files
        epub_files = []
        for ext in ['*.epub', '*.EPUB']:
            epub_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        epub_files = sorted(epub_files)
        
        if not epub_files:
            print("No EPUB files found!")
            input("Press Enter to continue...")
            return
        
        print(f"\nFound {len(epub_files)} EPUB files:")
        for i, epub_file in enumerate(epub_files, 1):
            print(f"{i}. {os.path.basename(epub_file)}")
        
        print(f"{len(epub_files)+1}. Process all")
        print("0. Cancel")
        
        try:
            choice = input("\nSelect files to process: ").strip()
            
            if choice == '0':
                return
            
            selected_files = []
            if choice == str(len(epub_files) + 1):
                selected_files = epub_files
            else:
                indices = [int(x.strip()) for x in choice.split(',') if x.strip()]
                for idx in indices:
                    if 1 <= idx <= len(epub_files):
                        selected_files.append(epub_files[idx-1])
            
            if not selected_files:
                print("No valid files selected")
                input("Press Enter to continue...")
                return
            
            print(f"\nProcessing {len(selected_files)} files...")
            
            # Path to epub2jsonMulti.py script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            epub2json_script = os.path.join(script_dir, "epub2jsonMulti.py")
            
            if not os.path.exists(epub2json_script):
                print(f"Error: Could not find epub2jsonMulti.py at {epub2json_script}")
                input("Press Enter to continue...")
                return
            
            success_count = 0
            for epub_file in selected_files:
                print(f"\n{'-'*50}")
                print(f"Processing: {os.path.basename(epub_file)}")
                
                try:
                    cmd = [
                        sys.executable, 
                        epub2json_script, 
                        epub_file,
                        '--output-base',
                        '/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml'
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✅ Success: {os.path.basename(epub_file)}")
                        if result.stdout:
                            # Show summary
                            for line in result.stdout.split('\n'):
                                if 'Language distribution:' in line:
                                    print(f"   {line}")
                                elif line.strip().startswith('  ') and ':' in line:
                                    print(f"   {line.strip()}")
                        success_count += 1
                    else:
                        print(f"❌ Failed: {os.path.basename(epub_file)}")
                        if result.stderr:
                            print(f"   Error: {result.stderr[:200]}")
                        
                except Exception as e:
                    print(f"❌ Exception: {e}")
            
            print(f"\n{'='*50}")
            print(f"Successfully processed: {success_count} / {len(selected_files)}")
            print(f"JSON files saved to: /home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/ml/")
            
        except Exception as e:
            print(f"Error during conversion: {e}")
        
        input("\nPress Enter to continue...")

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
        smart_order = [
            lang for lang in self.default_merge_order if lang in available_codes
        ]

        # Add any remaining available languages that aren't in default order
        for lang in available_codes:
            if lang not in smart_order:
                smart_order.append(lang)

        return smart_order

    def split_epubs(self):
        """Split EPUB files with defaults"""
        print("\n=== Split into Sentences ===")
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
            print(
                f"Transliterating EPUBs in {folder_path} using main language detection..."
            )
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
        file_patterns = ["*-db-*.epub"]

        # Use smart merge order based on available languages
        merge_order = self.get_smart_merge_order(folder_path)
        print(f"Smart merge order: {merge_order}")

        output_suffix = "ml"

        try:
            print(f"Merging EPUBs in {folder_path}...")
            epub_paths, output_path, languages, final_merge_order = (
                prep_epubs_by_pattern(
                    folder_path=folder_path,
                    file_patterns=file_patterns,
                    merge_order=merge_order,
                    output_suffix=output_suffix,
                )
            )

            if epub_paths:
                print(f"Found {len(epub_paths)} files to merge")
                print(f"Languages: {languages}")
                print(f"Final merge order: {final_merge_order}")

                merge_multiple_epubs(
                    epub_paths, output_path, languages, final_merge_order
                )
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
        file_patterns = ["*-db-*.epub"]

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
                output_suffix=output_suffix,
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
                scripts_dir="/home/zaya/Downloads/Zayas/zayaweb/apps/web/scripts",
            )

            # Ask for pattern
            pattern = (
                input("\nEnter file pattern (Enter for '*.epub'): ").strip() or "*.epub"
            )

            # Ask if they want to review each file
            review_each = (
                input("Review each file before conversion? (y/N): ").strip().lower()
                == "y"
            )

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

                        if proceed == "y":
                            # Ask for custom title/slug
                            use_custom = (
                                input("Use custom title/slug? (y/N): ").strip().lower()
                            )
                            custom_title = None
                            custom_slug = None

                            if use_custom == "y":
                                custom_title = (
                                    input(
                                        "Enter title (Enter to auto-detect): "
                                    ).strip()
                                    or None
                                )
                                custom_slug = (
                                    input("Enter slug (Enter to generate): ").strip()
                                    or None
                                )

                            converter.convert_epub_to_post(
                                epub_file,
                                custom_title=custom_title,
                                custom_slug=custom_slug,
                            )
                        else:
                            print("Skipping...")
            else:
                # Bulk convert all
                results = converter.convert_folder(folder_path, pattern)

                # Show summary
                successful = [r for r in results if r["success"]]
                if successful:
                    print(
                        f"\n✅ Successfully converted {len(successful)} EPUBs to posts"
                    )

            print("\nConversion process completed!")

        except Exception as e:
            print(f"Error during conversion: {e}")

        input("Press Enter to continue...")

    def convert_epub_to_json(self):
        """Convert EPUB files directly to JSON format - Batch processing"""
        print("\n=== Convert EPUB to JSON (Batch Processing) ===")
        print("This will convert EPUB files directly to JSON format")
        print("JSON files will be saved to language-specific directories:")
        print("  /home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/[lang]/")
        
        folder_path = input(f"Enter folder containing EPUB files (Enter for {self.current_directory}): ").strip() or self.current_directory
        
        # Find all EPUB files
        print("\nScanning for EPUB files...")
        
        epub_files = []
        for ext in ['*.epub', '*.EPUB']:
            epub_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        # Also check in subdirectories if needed
        recursive = input("Search recursively in subdirectories? (y/N): ").strip().lower() == 'y'
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.epub'):
                        epub_files.append(os.path.join(root, file))
            # Remove duplicates
            epub_files = list(set(epub_files))
        
        epub_files = sorted(epub_files)
        
        if not epub_files:
            print("No EPUB files found!")
            input("Press Enter to continue...")
            return
        
        print(f"\nFound {len(epub_files)} EPUB files:")
        
        # Group by language if possible
        files_by_lang = {}
        for epub_file in epub_files:
            filename = os.path.basename(epub_file)
            # Try to detect language from filename
            lang = self.detect_language_from_filename(filename)
            if lang:
                files_by_lang.setdefault(lang, []).append(epub_file)
            else:
                files_by_lang.setdefault('unknown', []).append(epub_file)
        
        if len(files_by_lang) > 1 or 'unknown' not in files_by_lang:
            print("\nDetected languages:")
            for lang, files in files_by_lang.items():
                print(f"  {lang}: {len(files)} files")
        
        print("\nProcessing options:")
        print("1. Process ALL files (batch mode)")
        print("2. Process by language")
        print("3. Select specific files")
        print("4. Process with pattern filter")
        print("0. Cancel")
        
        try:
            choice = input("\nSelect option: ").strip()
            
            if choice == '0':
                return
            
            selected_files = []
            
            if choice == '1':
                # Process all
                selected_files = epub_files
                print(f"Selected all {len(selected_files)} files")
                
            elif choice == '2':
                # Process by language
                if not files_by_lang:
                    print("No languages could be detected")
                    input("Press Enter to continue...")
                    return
                
                print("\nAvailable languages:")
                lang_list = list(files_by_lang.keys())
                for i, lang in enumerate(lang_list, 1):
                    print(f"{i}. {lang} ({len(files_by_lang[lang])} files)")
                
                lang_choice = input("\nSelect language number (or comma-separated): ").strip()
                if lang_choice:
                    try:
                        lang_indices = [int(x.strip()) for x in lang_choice.split(',') if x.strip()]
                        selected_langs = [lang_list[i-1] for i in lang_indices if 1 <= i <= len(lang_list)]
                        
                        for lang in selected_langs:
                            selected_files.extend(files_by_lang[lang])
                        
                        print(f"Selected {len(selected_files)} files from languages: {', '.join(selected_langs)}")
                    except (ValueError, IndexError):
                        print("Invalid selection")
                        input("Press Enter to continue...")
                        return
                
            elif choice == '3':
                # Select specific files
                print("\nAvailable files (first 50 shown):")
                for i, epub_file in enumerate(epub_files[:50], 1):
                    filename = os.path.basename(epub_file)
                    lang = self.detect_language_from_filename(filename)
                    lang_tag = f" [{lang}]" if lang else ""
                    print(f"{i}. {filename}{lang_tag}")
                
                if len(epub_files) > 50:
                    print(f"... and {len(epub_files) - 50} more files")
                
                file_choice = input("\nEnter file numbers to process (comma-separated, e.g., 1,3,5): ").strip()
                if file_choice:
                    try:
                        file_indices = [int(x.strip()) for x in file_choice.split(',') if x.strip()]
                        selected_files = [epub_files[i-1] for i in file_indices if 1 <= i <= len(epub_files)]
                        print(f"Selected {len(selected_files)} files")
                    except (ValueError, IndexError):
                        print("Invalid selection")
                        input("Press Enter to continue...")
                        return
                
            elif choice == '4':
                # Process with pattern filter
                pattern = input("Enter pattern to match filenames (e.g., '*-db-*.epub'): ").strip()
                if pattern:
                    import fnmatch
                    selected_files = [f for f in epub_files if fnmatch.fnmatch(os.path.basename(f), pattern)]
                    print(f"Found {len(selected_files)} files matching pattern '{pattern}'")
                else:
                    print("No pattern provided")
                    input("Press Enter to continue...")
                    return
            else:
                print("Invalid option")
                input("Press Enter to continue...")
                return
            
            if not selected_files:
                print("No files selected")
                input("Press Enter to continue...")
                return
            
            # Ask for confirmation
            print(f"\nReady to process {len(selected_files)} files:")
            for f in selected_files[:10]:  # Show first 10
                print(f"  - {os.path.basename(f)}")
            if len(selected_files) > 10:
                print(f"  ... and {len(selected_files) - 10} more")
            
            confirm = input("\nProceed with conversion? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Conversion cancelled")
                input("Press Enter to continue...")
                return
            
            # Path to epub2json.py script (assuming it's in the same directory)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            epub2json_script = os.path.join(script_dir, "epub2json.py")
            
            if not os.path.exists(epub2json_script):
                print(f"Error: Could not find epub2json.py at {epub2json_script}")
                # Try to find it in the current directory
                epub2json_script = os.path.join(os.getcwd(), "epub2json.py")
                if not os.path.exists(epub2json_script):
                    print("Error: Could not find epub2json.py in current directory either")
                    input("Press Enter to continue...")
                    return
            
            print(f"\n{'='*60}")
            print(f"Starting batch conversion of {len(selected_files)} files")
            print(f"{'='*60}")
            
            success_count = 0
            failed_files = []
            
            for i, epub_file in enumerate(selected_files, 1):
                filename = os.path.basename(epub_file)
                print(f"\n[{i}/{len(selected_files)}] Processing: {filename}")
                print("-" * 40)
                
                try:
                    # Run epub2json.py on this file
                    cmd = [
                        sys.executable, 
                        epub2json_script, 
                        epub_file,
                        '--output-base', 
                        '/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json'
                    ]
                    
                    print(f"Running conversion...")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✅ Success: {filename}")
                        if result.stdout:
                            # Extract and show summary
                            for line in result.stdout.split('\n'):
                                if 'Summary:' in line or 'Sections:' in line or 'Total paragraphs:' in line:
                                    print(f"   {line.strip()}")
                        success_count += 1
                    else:
                        print(f"❌ Failed: {filename}")
                        if result.stderr:
                            error_msg = result.stderr.strip().split('\n')[0]  # First line of error
                            print(f"   Error: {error_msg[:100]}...")
                        failed_files.append(filename)
                        
                except Exception as e:
                    print(f"❌ Exception processing {filename}: {e}")
                    failed_files.append(filename)
            
            print(f"\n{'='*60}")
            print(f"BATCH CONVERSION COMPLETE")
            print(f"{'='*60}")
            print(f"Successfully processed: {success_count} / {len(selected_files)}")
            
            if failed_files:
                print(f"\nFailed files ({len(failed_files)}):")
                for f in failed_files[:10]:
                    print(f"  - {f}")
                if len(failed_files) > 10:
                    print(f"  ... and {len(failed_files) - 10} more")
            
            # Show summary by language
            print(f"\nJSON files saved to language-specific directories:")
            output_base = "/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json"
            if os.path.exists(output_base):
                for lang in os.listdir(output_base):
                    lang_dir = os.path.join(output_base, lang)
                    if os.path.isdir(lang_dir):
                        json_files = list(Path(lang_dir).glob('*.json'))
                        if json_files:
                            print(f"  {lang}/: {len(json_files)} files")
            
        except KeyboardInterrupt:
            print("\n\nConversion interrupted by user")
        except Exception as e:
            print(f"Error during batch conversion: {e}")
        
        input("\nPress Enter to continue...")

    def detect_language_from_filename(self, filename):
        """Detect language code from EPUB filename - More robust version"""
        stem = Path(filename).stem
        
        # List of all supported language codes
        language_codes = ['ar', 'de', 'el', 'es', 'fr', 'he', 'id', 'it', 'ja', 'ko', 
                        'la', 'pl', 'pt', 'ru', 'sw', 'tr', 'zh']
        
        # First, try to find language code at the end with various separators
        # Common patterns: -ru, _ru, .ru, -ru., _ru., etc.
        import re

        # Look for language code at the end of the stem (before any extension)
        # This pattern looks for a hyphen or underscore followed by a 2-letter code at the end
        for code in language_codes:
            # Pattern: ends with -code, _code, .code, or -code., _code.
            patterns = [
                rf'-{code}$',           # ends with -ru
                rf'_{code}$',           # ends with _ru
                rf'\.{code}$',          # ends with .ru
                rf'-{code}\.',          # -ru. (with dot after)
                rf'_{code}\.',          # _ru. (with dot after)
            ]
            
            for pattern in patterns:
                if re.search(pattern, stem, re.IGNORECASE):
                    return code
            
            # Also try to find it as a separate word at the end
            # This handles cases with spaces: "filename -ru" or "filename ru"
            words = re.split(r'[\s_\-\.]+', stem)
            if words and words[-1].lower() == code:
                return code
        
        # Also check for full language names
        for lang_name, code in self.language_map.items():
            # Look for language name at the end
            words = re.split(r'[\s_\-\.]+', stem.lower())
            if words and words[-1] == lang_name.lower():
                return code
        
        return None

    def run(self):
        """Main program loop"""
        while True:
            self.display_menu()
            choice = self.get_user_choice()

            if choice == "0":
                print("Goodbye!")
                break
            elif choice == "1":
                self.split_epubs()
            elif choice == "2":
                self.remove_original()
            elif choice == "3":
                self.transliterate_epubs()
            elif choice == "4":
                self.merge_epubs()
            elif choice == "5":
                self.simple_merge()
            elif choice == "6":
                self.convert_epubs_to_posts()
            elif choice == "7":
                self.convert_epub_to_json()
            elif choice == '8':
                self.convert_epub_to_json_multilingual()
            elif choice == '9':
                self.convert_epub_to_json_ordered()
            elif choice == '10':
                self.process_for_readaloud()
            elif choice == '11':
                # Launch advanced version
                advanced_manager = EpubManagerWithOptions(self.current_directory)
                advanced_manager.run()
            else:
                print("Invalid choice! Please try again.")
                input("Press Enter to continue...")


class EpubManagerWithOptions:
    """Advanced version with customizable options"""

    def __init__(self, target_directory=None):
        self.default_merge_order = [
            "ru",
            "de",
            "en",
            "ch",
            "ar",
            "hi",
            "es",
            "fr",
            "el",
            "he",
            "id",
            "it",
            "ja",
            "ko",
            "la",
            "pl",
            "pt",
            "sw",
            "tr",
        ]
        self.supported_languages = [
            "japanese",
            "korean",
            "chinese",
            "hindi",
            "arabic",
            "russian",
        ]

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
            "turkish": "tr",
        }

        # Use target_directory if provided, otherwise use current directory
        if target_directory and os.path.exists(target_directory):
            self.current_directory = target_directory
        else:
            self.current_directory = os.getcwd()

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def display_menu(self):
        self.clear_screen()
        print("=" * 50)
        print("       EPUB MANAGER - ADVANCED OPTIONS")
        print("=" * 50)
        print(f"Current directory: {self.current_directory}")
        print()
        print("1. Split into Sentences (with options)")
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
            return [p.strip() for p in patterns_input.split(",")]
        else:
            return ["*-db-*.epub"]

    def get_merge_order(self, folder_path):
        print(f"\nDefault merge order: {self.default_merge_order}")

        # Show available languages
        available_langs = self.detect_available_languages(folder_path)
        if available_langs:
            print(f"Available languages: {available_langs}")

        print("Leave empty to use smart order, or specify custom order")
        order_input = input("Enter merge order (comma separated): ").strip()

        if order_input:
            custom_order = [lang.strip() for lang in order_input.split(",")]
            return self.get_smart_merge_order(folder_path, custom_order)
        else:
            return self.get_smart_merge_order(folder_path)

    def split_epubs(self):
        print("\n=== Split into Sentences (Advanced) ===")

        input_folder = (
            input(f"Enter input folder (Enter for {self.current_directory}): ").strip()
            or self.current_directory
        )
        output_folder = (
            input("Enter output folder (Enter for 'split_output'): ").strip()
            or "split_output"
        )

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
        folder_path = (
            input(f"Enter folder path (Enter for {self.current_directory}): ").strip()
            or self.current_directory
        )

        try:
            print(f"Removing original text from EPUBs in {folder_path}...")
            process_folder_remove_original(folder_path)
            print("Operation completed successfully!")
        except Exception as e:
            print(f"Error: {e}")

        input("Press Enter to continue...")

    def transliterate_epubs(self):
        print("\n=== Transliterate (Advanced) ===")
        folder_path = (
            input(f"Enter folder path (Enter for {self.current_directory}): ").strip()
            or self.current_directory
        )

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
        folder_path = (
            input(f"Enter folder path (Enter for {self.current_directory}): ").strip()
            or self.current_directory
        )
        file_patterns = self.get_file_patterns()
        merge_order = self.get_merge_order(folder_path)
        output_suffix = input("Enter output suffix (Enter for 'ml'): ").strip() or "ml"

        try:
            print(f"Using merge order: {merge_order}")
            epub_paths, output_path, languages, final_merge_order = (
                prep_epubs_by_pattern(
                    folder_path=folder_path,
                    file_patterns=file_patterns,
                    merge_order=merge_order,
                    output_suffix=output_suffix,
                )
            )

            if epub_paths:
                print(f"Found {len(epub_paths)} files to merge")
                merge_multiple_epubs(
                    epub_paths, output_path, languages, final_merge_order
                )
                print("Merge operation completed successfully!")
            else:
                print("No files found matching patterns!")

        except Exception as e:
            print(f"Error: {e}")

        input("Press Enter to continue...")

    def simple_merge(self):
        print("\n=== Simple Merge (Advanced) ===")
        folder_path = (
            input(f"Enter folder path (Enter for {self.current_directory}): ").strip()
            or self.current_directory
        )
        file_patterns = self.get_file_patterns()
        merge_order = self.get_merge_order(folder_path)
        output_suffix = (
            input("Enter output suffix (Enter for 'ml-simple'): ").strip()
            or "ml-simple"
        )

        try:
            print(f"Using merge order: {merge_order}")
            prep_and_merge_simple(
                folder_path=folder_path,
                file_patterns=file_patterns,
                merge_order=merge_order,
                output_suffix=output_suffix,
            )
            print("Simple merge completed successfully!")
        except Exception as e:
            print(f"Error: {e}")

        input("Press Enter to continue...")

    def convert_epubs_to_posts_advanced(self):
        """Convert EPUB files to markdown posts with advanced options"""
        print("\n=== Convert EPUBs to Posts (Advanced) ===")

        folder_path = (
            input(f"Enter source folder (Enter for {self.current_directory}): ").strip()
            or self.current_directory
        )

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
        create_backup = (
            input("Create backup of original EPUBs? (y/N): ").strip().lower() == "y"
        )
        delete_after = (
            input("Delete EPUB after successful conversion? (y/N): ").strip().lower()
            == "y"
        )

        try:
            converter = EpubToPostConverter(
                posts_dir=posts_dir,
                images_base_dir=images_dir,
                scripts_dir="/home/zaya/Downloads/Zayas/zayaweb/apps/web/scripts",
            )

            results = converter.convert_folder(folder_path, pattern)

            # Handle post-conversion options
            if delete_after:
                for result in results:
                    if result["success"]:
                        try:
                            os.remove(result["epub"])
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

            if choice == "0":
                print("Goodbye!")
                sys.exit(0)
            elif choice == "1":
                self.split_epubs()
            elif choice == "2":
                self.remove_original()
            elif choice == "3":
                self.transliterate_epubs()
            elif choice == "4":
                self.merge_epubs()
            elif choice == "5":
                self.simple_merge()
            elif choice == "6":
                self.convert_epubs_to_posts_advanced()
            elif choice == "7":
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