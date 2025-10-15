import os
import shutil
import sys
import zipfile

from lxml import etree


def extract_epub(epub_path: str, extract_to: str) -> None:
    """Extracts EPUB contents to a directory."""
    with zipfile.ZipFile(epub_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def create_epub(folder_path: str, epub_path: str) -> None:
    """Creates an EPUB from a directory."""
    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


def find_content_folder(extract_to: str) -> str:
    """Locates the folder containing content files in various EPUB formats."""
    # Common EPUB content directory structures
    possible_paths = [
        os.path.join(extract_to, "OEBPS"),  # EPUB 2 standard
        os.path.join(extract_to, "EPUB"),  # EPUB 3 standard
        os.path.join(extract_to, "content"),  # Some alternative structures
        os.path.join(extract_to, "Text"),  # Older formats
        os.path.join(extract_to, "text"),  # Some Kindle formats
        os.path.join(extract_to),  # Root as fallback
    ]

    # Also check for nested Text directories
    additional_paths = []
    for path in possible_paths:
        additional_paths.extend(
            [os.path.join(path, "Text"), os.path.join(path, "text"), os.path.join(path, "content")]
        )
    possible_paths.extend(additional_paths)

    # Find the first existing path that contains content files
    for path in possible_paths:
        if os.path.exists(path):
            # Verify it contains at least one content file
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith((".xhtml", ".html", ".htm", ".xml")):
                        return path

    # Fallback to OEBPS/Text if nothing found
    default_path = os.path.join(extract_to, "OEBPS", "Text")
    os.makedirs(default_path, exist_ok=True)
    return default_path


def get_content_files(content_folder: str) -> list:
    """Returns paths to all content files in the folder."""
    content_files = []
    for root, _, files in os.walk(content_folder):
        for file in files:
            if file.lower().endswith((".xhtml", ".html", ".htm", ".xml")):
                content_files.append(os.path.join(root, file))
    return content_files


def update_manifest(content_folder: str) -> None:
    """Updates the EPUB manifest if needed after file modifications."""
    opf_path = None
    # Find the OPF file
    for root, _, files in os.walk(content_folder):
        for file in files:
            if file.endswith(".opf"):
                opf_path = os.path.join(root, file)
                break
        if opf_path:
            break

    if opf_path:
        try:
            # Parse and update the OPF file if needed
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(opf_path, parser)
            # Here you would add logic to update the manifest if you modify files
            # For example, if you rename files or add new ones
            tree.write(opf_path, pretty_print=True, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            print(f"Warning: Could not update manifest at {opf_path}: {str(e)}")


def process_epub(epub_path: str, output_path: str) -> None:
    """Processes an EPUB file with enhanced content handling."""
    temp_dir = "temp_epub"
    try:
        extract_epub(epub_path, temp_dir)
        content_folder = find_content_folder(temp_dir)

        # Process all content files
        content_files = get_content_files(content_folder)
        if not content_files:
            raise ValueError("No content files found in EPUB")

        # Here you would call your processing functions on each content file
        # For example:
        # for content_file in content_files:
        #     process_content_file(content_file)

        # Update manifest if needed
        update_manifest(content_folder)

        create_epub(temp_dir, output_path)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python epub_manager.py input.epub output.epub")
        sys.exit(1)

    input_epub = sys.argv[1]
    output_epub = sys.argv[2]

    process_epub(input_epub, output_epub)
