import os
import shutil

from lxml import etree

from transliteration.add_metadata_and_cover import add_metadata_and_cover
from transliteration.epubManagement import (
    create_epub,
    extract_epub,
    find_text_folder,
    get_xhtml_files,
)
from transliteration.epubTransliteration import get_language_from_filename

# Default configuration
# DEFAULT_CONFIG = {
#         "option": 1,
#     }

DEFAULT_CONFIG = {"option": 3, "language_to_keep": "zh", "language_after": "ru"}

# Predefined configurations for common use cases
# Add to your CONFIG_PRESETS
CONFIG_PRESETS = {
    "keep_russian_after_english": {"option": 3, "language_to_keep": "ru", "language_after": "en"},
    "keep_chinese_after_russian": {"option": 3, "language_to_keep": "zh", "language_after": "ru"},
    "keep_english_after_chinese": {"option": 3, "language_to_keep": "en", "language_after": "zh"},
    "remove_all_english": {"option": 2, "language_to_keep": "en"},
    "remove_all_russian": {"option": 2, "language_to_keep": "ru"},
    # NEW: Keep Russian paragraphs that come after paragraphs without lang attribute
    "keep_russian_after_no_lang": {
        "option": 4,
        "language_to_keep": "ru",
        "reference_has_no_lang": True,
    },
    "Remove_original_text_elements": {
        "option": 1,
    },
}

# # Option 1: Remove original text elements before dir="auto"
# remove_original_text(file_path, option=1)

# # Option 2: Remove all English elements
# remove_original_text(file_path, option=2, language_to_keep="en")

# # Option 3: Keep only Russian paragraphs that come after English paragraphs (your current use case)
# remove_original_text(file_path, option=3, language_to_keep="ru", language_after="en")

# # Option 3: Keep only English paragraphs that come after Chinese paragraphs
# remove_original_text(file_path, option=3, language_to_keep="en", language_after="zh")

# # Option 3: Keep only German paragraphs that come after French paragraphs
# remove_original_text(file_path, option=3, language_to_keep="de", language_after="fr")


def remove_original_text(file_path: str, config: dict = None) -> None:
    """
    Removes text elements based on the selected configuration.

    Args:
        file_path: Path to the HTML file to process
        config: Configuration dictionary with options:
            option: Which removal strategy to use
                1 = Remove original text elements (immediately before dir="auto" elements)
                2 = Remove all elements with specific language
                3 = Keep only language_to_keep elements that come after language_after elements
                4 = Keep only language_to_keep elements that come after elements without lang attribute
            language_to_keep: For options 3-4, which language to keep (e.g., "ru")
            language_after: For option 3, keep elements that come after this language (e.g., "en")
            reference_has_no_lang: For option 4, look for elements without lang attribute as reference
            remove_empty_parents: Whether to remove empty parent elements after processing
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()

    print(f"Processing file for original text removal: {file_path}")

    try:
        parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()

        option = config.get("option", 3)
        # option = 1

        if option == 1:
            _remove_original_before_dir_auto(root)
        elif option == 2:
            language_to_remove = config.get("language_to_keep", "en")
            _remove_all_language_elements(root, language_to_remove)
        elif option == 3:
            language_to_keep = config.get("language_to_keep", "ru")
            language_after = config.get("language_after", "en")
            _keep_only_language_after_another(root, language_to_keep, language_after)
        elif option == 4:
            language_to_keep = config.get("language_to_keep", "ru")
            _keep_only_language_after_no_lang(root, language_to_keep)
        else:
            print(f"Invalid option: {option}")
            return

        # Optional: Remove empty parent elements
        if config.get("remove_empty_parents", True):
            _remove_empty_parents(root)

        # Save the modified file
        tree.write(file_path, encoding="utf-8", pretty_print=True, xml_declaration=True)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        import traceback

        traceback.print_exc()


def _keep_only_language_after_no_lang(root, language_to_keep: str):
    """
    Option 4: Keep only language_to_keep elements that come after elements without lang attribute.
    This handles cases where the original text has no lang attribute.
    """
    # Namespace-agnostic approach: find all elements that are paragraphs regardless of namespace
    all_elements = root.xpath('//*[local-name() = "p"]')
    # print(f"Found {len(all_elements)} total paragraph elements")

    # Filter by lang attribute
    target_paragraphs = [p for p in all_elements if p.get("lang") == language_to_keep]
    # Find paragraphs without lang attribute (the originals)
    reference_paragraphs = [p for p in all_elements if p.get("lang") is None]

    # print(f"Found {len(target_paragraphs)} {language_to_keep} paragraphs")
    # print(f"Found {len(reference_paragraphs)} paragraphs without lang attribute (originals)")

    # Debug: print first few paragraphs
    for i, p in enumerate(all_elements[:10]):
        lang = p.get("lang", "No lang")
        class_attr = p.get("class", "No class")
        text_preview = p.text[:50] + "..." if p.text and p.text.strip() else "No text"
        # print(f"  Paragraph {i}: class='{class_attr}', lang='{lang}', text='{text_preview}'")

    # For each reference paragraph (no lang), find and mark the immediately following target paragraph to keep
    paragraphs_to_keep = set()

    for ref_para in reference_paragraphs:
        current_elem = ref_para.getnext()
        found = False
        while current_elem is not None and not found:
            # Check if this element is a paragraph with the target language
            if (
                etree.QName(current_elem).localname == "p"
                and current_elem.get("lang") == language_to_keep
            ):
                paragraphs_to_keep.add(current_elem)
                found = True
                break
            current_elem = current_elem.getnext()

    # print(
    #     f"Keeping {len(paragraphs_to_keep)} {language_to_keep} paragraphs (after no-lang originals)"
    # )

    removed_count = 0
    for target_para in target_paragraphs:
        if target_para not in paragraphs_to_keep:
            parent = target_para.getparent()
            if parent is not None:
                parent.remove(target_para)
                removed_count += 1

    # print(f"Removed {removed_count} {language_to_keep} paragraphs")


def _remove_original_before_dir_auto(root):
    """Option 1: Remove original text elements (immediately before dir="auto" elements)"""
    keep_translations = True

    # Find all translated elements
    translations = root.xpath('//*[@dir="auto" or (@lang)]')

    # For each translation, remove its immediate previous sibling if it exists
    for elem in translations:
        prev = elem.getprevious()
        if keep_translations:
            # When keeping translations, remove originals
            if "dir" in elem.attrib or (prev is not None and prev.get("lang") != elem.get("lang")):
                if prev is not None and prev.tag not in ["head", "meta", "title", "link"]:
                    parent = prev.getparent()
                    if parent is not None:
                        parent.remove(prev)
        else:
            # When keeping originals, remove translations
            if "dir" in elem.attrib or (prev is not None and prev.get("lang") != elem.get("lang")):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)


def _remove_all_language_elements(root, language_to_remove: str):
    """Option 2: Remove all elements with specific language"""
    elements_to_remove = root.xpath(f'//*[@lang="{language_to_remove}"]')
    # print(f"Removing all {len(elements_to_remove)} elements with lang='{language_to_remove}'")

    for elem in elements_to_remove:
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)


def _keep_only_language_after_another(root, language_to_keep: str, language_after: str):
    """Option 3: Keep only language_to_keep elements that come after language_after elements"""
    # Namespace-agnostic approach: find all elements that are paragraphs regardless of namespace
    all_elements = root.xpath('//*[local-name() = "p"]')
    # print(f"Found {len(all_elements)} total paragraph elements")

    # Filter by lang attribute
    target_paragraphs = [p for p in all_elements if p.get("lang") == language_to_keep]
    reference_paragraphs = [p for p in all_elements if p.get("lang") == language_after]

    print(f"Found {len(target_paragraphs)} {language_to_keep} paragraphs")
    print(f"Found {len(reference_paragraphs)} {language_after} paragraphs")

    # Debug: print first few paragraphs
    for i, p in enumerate(all_elements[:5]):
        lang = p.get("lang", "No lang")
        text_preview = p.text[:50] + "..." if p.text and p.text.strip() else "No text"
        print(f"  Paragraph {i}: lang='{lang}', text='{text_preview}'")

    # For each reference paragraph, find and mark the immediately following target paragraph to keep
    paragraphs_to_keep = set()

    for ref_para in reference_paragraphs:
        current_elem = ref_para.getnext()
        found = False
        while current_elem is not None and not found:
            # Check if this element is a paragraph with the target language
            if (
                etree.QName(current_elem).localname == "p"
                and current_elem.get("lang") == language_to_keep
            ):
                paragraphs_to_keep.add(current_elem)
                found = True
                break
            current_elem = current_elem.getnext()

    print(
        f"Keeping {len(paragraphs_to_keep)} {language_to_keep} paragraphs (after {language_after})"
    )

    removed_count = 0
    for target_para in target_paragraphs:
        if target_para not in paragraphs_to_keep:
            parent = target_para.getparent()
            if parent is not None:
                parent.remove(target_para)
                removed_count += 1

    print(f"Removed {removed_count} {language_to_keep} paragraphs")


def _remove_empty_parents(root):
    """Remove parent elements that become empty after processing"""
    # Find all elements that have no children or only whitespace
    empty_elements = root.xpath("//*[not(node())] | //*[not(normalize-space())]")

    for elem in empty_elements:
        # Don't remove root element or essential structural elements
        if elem.getparent() is not None and elem.tag not in ["html", "body", "head"]:
            parent = elem.getparent()
            parent.remove(elem)


def process_epub(epub_path: str, config: dict = None) -> str:
    """
    Processes an EPUB to remove original text while preserving structure.

    Args:
        epub_path: Path to input EPUB file
        config: Configuration dictionary for text removal options

    Returns:
        Path to generated EPUB file
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()

    base_name = os.path.basename(epub_path).replace(".epub", "")
    language = get_language_from_filename(base_name)
    extract_to = epub_path.replace(".epub", "_temp")
    output_path = epub_path.replace(".epub", "_no.epub")

    try:
        extract_epub(epub_path, extract_to)
        text_folder = find_text_folder(extract_to)

        print(f"Using configuration: {config}")
        for file_path in get_xhtml_files(text_folder):
            remove_original_text(file_path, config)

        add_metadata_and_cover(extract_to, base_name + "_no", language)
        create_epub(extract_to, output_path)

        return output_path

    finally:
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)


def process_epub_with_preset(
    epub_path: str, preset_name: str = "keep_russian_after_english"
) -> str:
    """Process EPUB using a predefined configuration preset."""
    if preset_name not in CONFIG_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(CONFIG_PRESETS.keys())}")

    return process_epub(epub_path, CONFIG_PRESETS[preset_name])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python epub_no_original.py <input.epub> [preset_name]")
        print("Available presets:", list(CONFIG_PRESETS.keys()))
        sys.exit(1)

    input_epub = sys.argv[1]
    preset_name = sys.argv[2] if len(sys.argv) > 2 else "keep_russian_after_english"

    try:
        output_epub = process_epub_with_preset(input_epub, preset_name)
        print(f"Generated EPUB with original text removed: {output_epub}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
