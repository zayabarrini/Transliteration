import os
import sys
from pathlib import Path
from typing import List


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def display_menu():
    """Display the main menu."""
    clear_screen()
    print(
        """
╔════════════════════════════════════════╗
║            Text Processing             ║
╠════════════════════════════════════════╣
║ 1. E-book Split Sentences              ║
║ 2. E-Book Versions                     ║
║ 3. Subtitle Versions                   ║
║ 4. Webpage Version                     ║
║                                        ║
║ 0. Exit                                ║
╚════════════════════════════════════════╝
"""
    )


def get_choice(prompt: str, options: List[str]) -> str:
    """Get user choice with validation."""
    while True:
        choice = input(prompt).strip()
        if choice in options:
            return choice
        print(f"Invalid option. Please choose from {', '.join(options)}")


def process_ebook_split_sentences():
    """Handle E-book Split Sentences operations."""
    clear_screen()
    print(
        """
╔════════════════════════════════════════╗
║        E-book Split Sentences          ║
╠════════════════════════════════════════╣
║ 1. Process multiple EPUB files         ║
║ 2. Process single EPUB file            ║
║                                        ║
║ 0. Back to main menu                   ║
╚════════════════════════════════════════╝
"""
    )

    choice = get_choice("Select an option (0-2): ", ["0", "1", "2"])

    if choice == "0":
        return

    if choice == "1":
        input_folder = input("Enter input folder path: ").strip()
        output_folder = input("Enter output folder path: ").strip()

        # Validate paths
        if not os.path.isdir(input_folder):
            print(f"Error: Input folder '{input_folder}' does not exist.")
            return

        os.makedirs(output_folder, exist_ok=True)

        print(f"\nProcessing all EPUB files in {input_folder}...")
        from epubSplitProcessor import process_epub_folder

        process_epub_folder(input_folder, output_folder)

    elif choice == "2":
        epub_file = input("Enter EPUB file path: ").strip()
        output_path = input("Enter output file path: ").strip()

        if not os.path.isfile(epub_file):
            print(f"Error: File '{epub_file}' does not exist.")
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"\nProcessing {epub_file}...")
        from epubSplitProcessor import process_epub

        process_epub(epub_file, output_path)

    input("\nPress Enter to continue...")


def process_ebook_versions():
    """Handle E-Book Versions operations."""
    clear_screen()
    print(
        """
╔════════════════════════════════════════╗
║           E-Book Versions              ║
╠════════════════════════════════════════╣
║ 1. Process multiple EPUB files         ║
║ 2. Process single EPUB file            ║
║                                        ║
║ 0. Back to main menu                   ║
╚════════════════════════════════════════╝
"""
    )

    choice = get_choice("Select an option (0-2): ", ["0", "1", "2"])

    if choice == "0":
        return

    if choice == "1":
        input_folder = input("Enter folder path with EPUB files: ").strip()

        if not os.path.isdir(input_folder):
            print(f"Error: Folder '{input_folder}' does not exist.")
            return

        print(f"\nProcessing all EPUB files in {input_folder}...")
        from epubVersions import process_folder

        process_folder(input_folder)

    elif choice == "2":
        epub_file = input("Enter EPUB file path: ").strip()

        if not os.path.isfile(epub_file):
            print(f"Error: File '{epub_file}' does not exist.")
            return

        print("\nProcessing options:")
        print("1. Remove original text")
        print("2. Transliterate")
        print("3. Transliterate (no original)")

        sub_choice = get_choice("Select processing option (1-3): ", ["1", "2", "3"])

        from epubVersions import remove_original, transliterate_epub, SUPPORTED_LANGUAGES

        language = input("Enter target language: ").strip().lower()
        if language not in SUPPORTED_LANGUAGES:
            print(f"Error: Unsupported language. Choose from {SUPPORTED_LANGUAGES}")
            return

        if sub_choice == "1":
            print("\nRemoving original text...")
            epub_path_no_original = remove_original(epub_file)
            print(f"Created version without original text: {epub_path_no_original}")
        elif sub_choice == "2":
            print("\nTransliterating...")
            transliterate_epub(epub_file)
        elif sub_choice == "3":
            print("\nCreating version without original text and transliterating...")
            epub_path_no_original = remove_original(epub_file)
            transliterate_epub(epub_path_no_original)

    input("\nPress Enter to continue...")


def process_subtitle_versions():
    """Handle Subtitle Versions operations."""
    clear_screen()
    print(
        """
╔════════════════════════════════════════╗
║         Subtitle Versions              ║
╠════════════════════════════════════════╣
║ 1. Process multiple SRT files          ║
║ 2. Process single SRT file             ║
║                                        ║
║ 0. Back to main menu                   ║
╚════════════════════════════════════════╝
"""
    )

    choice = get_choice("Select an option (0-2): ", ["0", "1", "2"])

    if choice == "0":
        return

    if choice == "1":
        input_dir = input("Enter folder path with SRT files: ").strip()

        if not os.path.isdir(input_dir):
            print(f"Error: Folder '{input_dir}' does not exist.")
            return

        target_languages = (
            input("Enter target languages (comma-separated, e.g., 'de,zh-ch'): ").strip().split(",")
        )
        target_languages = [lang.strip() for lang in target_languages]

        enable_transliteration = input("Enable transliteration? (y/n): ").strip().lower() == "y"

        print(f"\nProcessing all SRT files in {input_dir}...")
        # Note: You'll need to implement or import a multi-file processing function
        # For now, we'll process each file individually
        from subMultilingualVersions import process_multilingual_srt

        for filename in os.listdir(input_dir):
            if filename.lower().endswith(".srt"):
                filepath = os.path.join(input_dir, filename)
                process_multilingual_srt(filepath, target_languages, enable_transliteration)

    elif choice == "2":
        input_file = input("Enter SRT file path: ").strip()

        if not os.path.isfile(input_file):
            print(f"Error: File '{input_file}' does not exist.")
            return

        print("\nProcessing options:")
        print("1. Transliterate only")
        print("2. Create multilingual versions")

        sub_choice = get_choice("Select processing option (1-2): ", ["1", "2"])

        from subMultilingualVersions import transliterate_srt, process_multilingual_srt

        if sub_choice == "1":
            target_language = input("Enter target language (e.g., 'de', 'zh-ch'): ").strip()
            print("\nTransliterating subtitle file...")
            transliterate_srt(input_file, target_language)
        elif sub_choice == "2":
            target_languages = (
                input("Enter target languages (comma-separated, e.g., 'de,zh-ch'): ")
                .strip()
                .split(",")
            )
            target_languages = [lang.strip() for lang in target_languages]
            enable_transliteration = input("Enable transliteration? (y/n): ").strip().lower() == "y"
            print("\nCreating multilingual versions...")
            process_multilingual_srt(input_file, target_languages, enable_transliteration)

    input("\nPress Enter to continue...")


def process_webpage_versions():
    """Handle Webpage Version operations."""
    clear_screen()
    print(
        """
╔════════════════════════════════════════╗
║          Webpage Version               ║
╠════════════════════════════════════════╣
║ 1. Process multiple HTML files         ║
║ 2. Process single HTML file            ║
║                                        ║
║ 0. Back to main menu                   ║
╚════════════════════════════════════════╝
"""
    )

    choice = get_choice("Select an option (0-2): ", ["0", "1", "2"])

    if choice == "0":
        return

    target_language = input("Enter target language (e.g., 'japanese', 'chinese'): ").strip().lower()
    enable_transliteration = input("Enable transliteration? (y/n): ").strip().lower() == "y"

    if choice == "1":
        html_folder = input("Enter folder path with HTML files: ").strip()

        if not os.path.isdir(html_folder):
            print(f"Error: Folder '{html_folder}' does not exist.")
            return

        epub_folder = input(
            "(Optional) Enter EPUB folder path for context (leave blank if none): "
        ).strip()
        if epub_folder and not os.path.isdir(epub_folder):
            print(f"Error: Folder '{epub_folder}' does not exist.")
            return

        print(f"\nProcessing all HTML files in {html_folder}...")
        from html2transliteration import process_folder

        process_folder(
            html_folder,
            target_language,
            enable_transliteration,
            epub_folder if epub_folder else None,
        )

    elif choice == "2":
        input_file = input("Enter HTML file path: ").strip()

        if not os.path.isfile(input_file):
            print(f"Error: File '{input_file}' does not exist.")
            return

        epub_folder = input(
            "(Optional) Enter EPUB folder path for context (leave blank if none): "
        ).strip()
        if epub_folder and not os.path.isdir(epub_folder):
            print(f"Error: Folder '{epub_folder}' does not exist.")
            return

        print(f"\nProcessing {input_file}...")
        from html2transliteration import process_file

        process_file(
            input_file,
            target_language,
            enable_transliteration,
            epub_folder if epub_folder else None,
        )

    input("\nPress Enter to continue...")


def main():
    """Main program loop."""
    # Test everything
    # --------------------- Subtitles

    ## Only Transliteration
    input_dir = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles"
    target_languages = ["de", "zh-ch"]

    # input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Gosford-de-(ja).srt"
    # target_language = "japanese"
    # input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Fargo-de-(ch).srt"
    # target_language = "chinese"
    # input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Ghandi-ru-(ar).srt"
    # target_language = "arabic"
    # input_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/Little-hi.srt"
    # target_language = "hindi"
    from sub2translate_literate import process_csv

    csv_file = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles/trans.csv"
    process_csv(csv_file)

    # from subMultilingualVersions import process_multilingual_srt
    # for filename in os.listdir(input_dir):
    #     if filename.lower().endswith('.srt'):
    #         filepath = os.path.join(input_dir, filename)
    #         process_multilingual_srt(filepath, target_languages, True)

    ## Zip File
    input_zip_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/subtitles/subtitles.zip"
    target_languages = ["de", "zh-ch"]  # Your target languages
    from subtitles.zip2zip import process_zip_of_srts

    process_zip_of_srts(input_zip_path, target_languages)

    # --------------------- Ebook: Transliteration
    input_folder_ebooks = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks"
    from epubVersions import process_folder

    process_folder(input_folder_ebooks)

    # --------------------- Ebook: Split Sentences
    input_folder = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks/ebook.epub"  # Update this path to your folder containing EPUB files
    output_folder = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/ebooks/Output"

    from epubSplitProcessor import process_epub_folder

    process_epub_folder(input_folder, output_folder)

    # --------------------- Webpage: Transliteration
    from web.webflask import _main_

    # run main.py, which is a Flask app
    # pass some initial string = "I'm just testing"
    _main_()

    while True:
        display_menu()
        choice = get_choice("Select an option (0-4): ", ["0", "1", "2", "3", "4"])

        if choice == "0":
            print("\nExiting program. Goodbye!")
            break
        elif choice == "1":
            process_ebook_split_sentences()
        elif choice == "2":
            process_ebook_versions()
        elif choice == "3":
            process_subtitle_versions()
        elif choice == "4":
            process_webpage_versions()


if __name__ == "__main__":
    main()
