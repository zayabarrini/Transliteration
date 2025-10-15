import codecs
import os
import re
import shutil
import time
import zipfile
from pathlib import Path

import chardet
import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from transliteration.filter_language_characters import filter_language_characters
from transliteration.translationFunctions import (
    LANGUAGE_CODE_MAP,
    LANGUAGE_STYLES,
    TARGET_PATTERNS,
    transliterate,
)


def read_srt(file_path):
    """Read SRT file lines"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.readlines()
    except:
        # Fallback encoding
        with open(file_path, "r", encoding="latin-1") as f:
            return f.readlines()


def write_srt(file_path, lines):
    """Write SRT file"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def transliterate_srt(input_file, target_language):
    """
    Transliterates the Chinese text lines in a bilingual SRT file.
    The SRT file should have format: number, timestamp, english, chinese
    """
    # Read the SRT file
    lines = read_srt(input_file)

    # Prepare output lines
    output_lines = []
    i = 0
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i].strip()

        # Handle SRT block structure
        if re.match(r"^\d+$", line):  # Line number
            output_lines.append(line + "\n")
            i += 1

            if i < total_lines and re.match(
                r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$", lines[i].strip()
            ):  # Timestamp
                output_lines.append(lines[i].strip() + "\n")
                i += 1

                # English text
                if i < total_lines and lines[i].strip():
                    output_lines.append(lines[i].strip() + "\n")
                    i += 1

                # Chinese text (to be transliterated)
                if i < total_lines and lines[i].strip():
                    chinese_line = lines[i].strip()
                    # Check if this looks like Chinese text
                    if any("\u4e00" <= char <= "\u9fff" for char in chinese_line):
                        output_lines.append(chinese_line + "\n")
                        # Add transliteration
                        transliterated = transliterate(chinese_line, target_language)
                        output_lines.append(transliterated + "\n")
                    else:
                        output_lines.append(chinese_line + "\n")
                    i += 1

                # Empty line
                if i < total_lines and not lines[i].strip():
                    output_lines.append("\n")
                    i += 1
            continue

        # For any other line
        output_lines.append(line + "\n")
        i += 1

    # Write output file
    output_file = input_file.replace(".srt", f"_{target_language}_trans.srt")
    write_srt(output_file, output_lines)

    return output_file


def merge_subtitle_lines(input_file, output_file=None):
    """Merge subtitle lines and save the modified content with error handling."""
    try:
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-16"]
        content = None

        for encoding in encodings:
            try:
                with open(input_file, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            with open(input_file, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")

        blocks = re.split(r"\n\n+", content.strip())
        processed_blocks = []

        for block in blocks:
            try:
                lines = block.split("\n")
                if len(lines) < 3:
                    processed_blocks.append(block)
                    continue

                number_line = lines[0]
                time_line = lines[1]

                text_lines = [line.strip() for line in lines[2:] if line.strip()]
                merged_text = " ".join(text_lines)

                processed_block = f"{number_line}\n{time_line}\n{merged_text}"
                processed_blocks.append(processed_block)
            except Exception as e:
                processed_blocks.append(block)
                continue

        merged_content = "\n\n".join(processed_blocks)

        if output_file is None:
            output_file = input_file

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(merged_content)

        return True
    except Exception as e:
        print(f"Error merging subtitle lines in {input_file}: {e}")
        return False


def detect_encoding(file_path):
    """Detect file encoding with multiple fallbacks"""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"] if result["confidence"] > 0.7 else "utf-8"

        with open(file_path, "r", encoding=encoding) as f:
            f.read(1024)

        return encoding
    except (UnicodeDecodeError, LookupError):
        for enc in ["utf-8-sig", "latin-1", "windows-1252", "cp1252", "iso-8859-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(1024)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue

    return "utf-8"


def read_srt_with_encoding(srt_file):
    """Read SRT file with automatic encoding detection and better error handling"""
    try:
        encoding = detect_encoding(srt_file)

        with open(srt_file, "r", encoding=encoding) as f:
            content = f.read()

        # Clean BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        # Validate content
        if not content or len(content.strip()) < 10:
            print(f"Warning: File appears empty or very short: {srt_file}")

        return content

    except Exception as e:
        print(f"Error reading {srt_file}: {e}")
        # Final fallback - read as binary
        try:
            with open(srt_file, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")
            return content
        except Exception as e2:
            print(f"Complete failure reading {srt_file}: {e2}")
            return ""


def process_srt_files_with_merging(srt_files):
    """Process SRT files by merging lines for better translation"""
    processed_files = []

    for srt_file in srt_files:
        try:
            temp_file = srt_file + ".merged"
            if merge_subtitle_lines(srt_file, temp_file):
                processed_files.append(temp_file)
                print(f"Merged lines in: {os.path.basename(srt_file)}")
            else:
                processed_files.append(srt_file)
                print(f"Using original: {os.path.basename(srt_file)}")
        except Exception as e:
            print(f"Error processing {srt_file}: {e}")
            processed_files.append(srt_file)

    return processed_files


def format_srt_for_epub(srt_content, filename):
    """Format SRT content for better EPUB compatibility with robust validation"""
    if not srt_content or len(srt_content.strip()) == 0:
        print(f"Empty content in {filename}")
        return ""

    try:
        blocks = re.split(r"\n\n+", srt_content.strip())
        formatted_blocks = []
        valid_blocks = 0

        for i, block in enumerate(blocks):
            try:
                lines = block.split("\n")
                if len(lines) < 3:
                    continue

                number = lines[0].strip()
                timestamp = lines[1].strip()
                text = " ".join(line.strip() for line in lines[2:] if line.strip())

                # Validate the block structure
                if (
                    not number.isdigit()
                    or "-->" not in timestamp
                    or not text
                    or len(text.strip()) == 0
                ):
                    continue

                formatted_block = f"""
                <div class="subtitle-block" data-original-index="{i}">
                    <p class="subtitle-number">{number}</p>
                    <p class="subtitle-time">{timestamp}</p>
                    <p class="subtitle-text">{text}</p>
                </div>
                """
                formatted_blocks.append(formatted_block)
                valid_blocks += 1

            except Exception as e:
                print(f"Error formatting block {i} in {filename}: {e}")
                continue

        print(f"Found {valid_blocks} valid subtitle blocks in {filename}")
        return "\n".join(formatted_blocks)

    except Exception as e:
        print(f"Error processing SRT content in {filename}: {e}")
        return ""


def srt_to_epub(srt_files, output_epub):
    """Convert SRT files to EPUB with better structure and error handling"""
    book = epub.EpubBook()
    book.set_identifier(f"srt_collection_{os.getpid()}_{int(time.time())}")
    book.set_title("SRT Files Collection")
    book.set_language("en")

    # Add metadata
    book.add_metadata("DC", "description", "Collection of SRT subtitle files")
    book.add_metadata("DC", "creator", "SRT to EPUB Converter")

    book.toc = []
    spine = ["nav"]

    valid_chapters = 0

    for srt_file in srt_files:
        try:
            srt_content = read_srt_with_encoding(srt_file)

            # Check if we have valid content
            if not srt_content or len(srt_content.strip()) < 10:
                print(f"Skipping empty or invalid file: {srt_file}")
                continue

            chapter_title = os.path.splitext(os.path.basename(srt_file))[0]
            if chapter_title.endswith(".merged"):
                chapter_title = chapter_title[:-7]

            formatted_content = format_srt_for_epub(srt_content, chapter_title)

            # Check if we have any valid content after formatting
            if not formatted_content or len(formatted_content.strip()) < 10:
                print(f"No valid subtitle content found in: {srt_file}")
                continue

            chapter = epub.EpubHtml(
                title=chapter_title, file_name=f"{chapter_title}.xhtml", lang="en"
            )

            full_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter_title}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <link rel="stylesheet" type="text/css" href="../style/main.css"/>
</head>
<body>
    <div class="chapter">
        <h1>{chapter_title}</h1>
        <div class="srt-file" data-filename="{os.path.basename(srt_file).replace('.merged', '')}">
            {formatted_content}
        </div>
    </div>
</body>
</html>"""

            chapter.content = full_content
            book.add_item(chapter)
            book.toc.append(epub.Link(f"{chapter_title}.xhtml", chapter_title, chapter_title))
            spine.append(chapter)
            valid_chapters += 1

            print(f"Added chapter: {chapter_title}")

        except Exception as e:
            print(f"Error processing {srt_file}: {e}")
            import traceback

            traceback.print_exc()
            continue

    # Check if we have any valid content
    if valid_chapters == 0:
        raise ValueError("No valid SRT content found to create EPUB")

    # Add navigation and CSS
    book.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    book.add_item(nav)
    spine.append(nav)

    # Improved CSS
    style = """
    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; padding: 0; }
    .chapter { max-width: 800px; margin: 0 auto; }
    .srt-file { margin: 30px 0; }
    .subtitle-block { 
        margin: 20px 0; 
        padding: 15px; 
        border: 1px solid #ddd;
        border-radius: 5px;
        background: #fafafa;
    }
    .subtitle-number { 
        font-weight: bold; 
        color: #2c3e50; 
        margin: 0 0 5px 0; 
        font-size: 14px;
    }
    .subtitle-time { 
        color: #7f8c8d; 
        margin: 0 0 10px 0; 
        font-size: 12px;
        font-family: monospace;
    }
    .subtitle-text { 
        margin: 0; 
        font-size: 16px;
        line-height: 1.5;
        color: #34495e;
    }
    h1 { 
        color: #2c3e50; 
        border-bottom: 2px solid #ecf0f1; 
        padding-bottom: 15px;
        margin-bottom: 30px;
    }
    """

    nav_css = epub.EpubItem(
        uid="main_style", file_name="style/main.css", media_type="text/css", content=style
    )
    book.add_item(nav_css)

    book.spine = spine

    # Write with better options
    options = {
        "epub2_guide": False,  # Disable problematic features
        "epub3_landmark": False,
        "epub3_pages": False,
    }

    try:
        epub.write_epub(output_epub, book, options)
        print(
            f"Successfully created EPUB: {output_epub} ({(os.path.getsize(output_epub) / 1024):.1f} KB)"
        )
        return True
    except Exception as e:
        print(f"Error writing EPUB: {e}")
        # Fallback: try without options
        try:
            epub.write_epub(output_epub, book, {})
            print(f"Created EPUB with fallback method: {output_epub}")
            return True
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            raise


def process_zip_to_epub(zip_path, output_epub):
    """Process zip file to EPUB with enhanced error handling"""
    srt_files = []
    extract_dir = "temp_extract"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find all SRT files
        for root, _, files in os.walk(extract_dir):
            for file in files:
                if file.lower().endswith(".srt"):
                    full_path = os.path.join(root, file)
                    # Check file size to avoid empty files
                    if os.path.getsize(full_path) > 10:  # At least 10 bytes
                        srt_files.append(full_path)
                    else:
                        print(f"Skipping empty file: {file}")

        if not srt_files:
            raise ValueError("No valid SRT files found in the zip archive")

        print(f"Found {len(srt_files)} SRT files")
        print("Merging subtitle lines for better translation...")

        processed_files = process_srt_files_with_merging(srt_files)

        # Check if we have processed files with content
        valid_processed_files = []
        for file in processed_files:
            if os.path.exists(file) and os.path.getsize(file) > 10:
                valid_processed_files.append(file)
            else:
                print(f"Skipping empty processed file: {file}")

        if not valid_processed_files:
            raise ValueError("No valid content after processing SRT files")

        success = srt_to_epub(valid_processed_files, output_epub)
        if not success:
            raise ValueError("Failed to create EPUB")

    finally:
        # Cleanup
        for file in srt_files:
            temp_file = file + ".merged"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        shutil.rmtree(extract_dir, ignore_errors=True)

    return output_epub


def epub_to_srts(epub_path, output_zip):
    """Convert translated EPUB back to SRT files using the precise structure"""
    extract_dir = "epub_extract"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        # Extract EPUB
        with zipfile.ZipFile(epub_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        srt_files_created = []

        # Find all XHTML files in the EPUB directory
        epub_dir = os.path.join(extract_dir, "EPUB")
        for root, _, files in os.walk(epub_dir):
            for file in files:
                if file.endswith(".xhtml") and not file.startswith("nav."):
                    xhtml_path = os.path.join(root, file)

                    try:
                        with open(xhtml_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        soup = BeautifulSoup(content, "html.parser")

                        # Find the main srt-file div that contains the filename
                        main_srt_div = soup.find("div", class_="srt-file")
                        if not main_srt_div:
                            continue

                        # Get the original filename from data attribute
                        original_filename = main_srt_div.get("data-filename")
                        if not original_filename:
                            # Fallback: use the title or filename
                            title = soup.find("title")
                            if title:
                                original_filename = title.get_text().replace(".xhtml", ".srt")
                            else:
                                original_filename = file.replace(".xhtml", ".srt")

                        # Find all subtitle blocks
                        subtitle_blocks = main_srt_div.find_all("div", class_="srt-file")

                        if not subtitle_blocks:
                            # Try alternative class names
                            subtitle_blocks = main_srt_div.find_all("div", class_="subtitle-block")

                        srt_content_lines = []

                        for block in subtitle_blocks:
                            try:
                                # Extract number, timestamp, and text
                                number_elems = block.find_all("p", class_="subtitle-number")
                                if len(number_elems) < 3:
                                    continue

                                # Number is first element
                                number = number_elems[0].get_text().replace("#", "").strip()

                                # Timestamp is second element
                                timestamp = number_elems[1].get_text().strip()

                                # Original text is third element (English)
                                original_text = number_elems[2].get_text().strip()

                                # Chinese translation is in element with lang="zh"
                                chinese_text = ""
                                zh_elements = block.find_all(attrs={"lang": "zh"})
                                if zh_elements:
                                    chinese_text = zh_elements[0].get_text().strip()

                                # Reconstruct the SRT block with both languages
                                srt_content_lines.append(number)
                                srt_content_lines.append(timestamp)
                                srt_content_lines.append(original_text)
                                if chinese_text:
                                    srt_content_lines.append(chinese_text)
                                srt_content_lines.append("")

                            except Exception as e:
                                print(f"Error processing block in {original_filename}: {e}")
                                continue

                        if srt_content_lines:
                            srt_content = "\n".join(srt_content_lines)
                            srt_output_path = os.path.join(extract_dir, original_filename)

                            with open(srt_output_path, "w", encoding="utf-8") as f:
                                f.write(srt_content)

                            srt_files_created.append(srt_output_path)
                            print(
                                f"Extracted: {original_filename} with {len(subtitle_blocks)} blocks"
                            )

                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                        continue

        if not srt_files_created:
            print("No SRT files were created. Trying alternative extraction...")
            srt_files_created = extract_srts_alternative_method(extract_dir)

        # Create output zip
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for srt_file in srt_files_created:
                zipf.write(srt_file, os.path.basename(srt_file))

        print(f"Created output zip with {len(srt_files_created)} SRT files: {output_zip}")
        return srt_files_created

    except Exception as e:
        print(f"Error in epub_to_srts: {e}")
        import traceback

        traceback.print_exc()
        return []
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def extract_srts_alternative_method(extract_dir):
    """Alternative extraction method for different EPUB structures"""
    srt_files = []
    epub_dir = os.path.join(extract_dir, "EPUB")

    for root, _, files in os.walk(epub_dir):
        for file in files:
            if file.endswith(".xhtml") and not file.startswith("nav."):
                try:
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    soup = BeautifulSoup(content, "html.parser")

                    # Try to find the filename from various sources
                    original_filename = None

                    # From data-filename attribute
                    srt_div = soup.find("div", class_="srt-file")
                    if srt_div and srt_div.get("data-filename"):
                        original_filename = srt_div.get("data-filename")

                    # From title
                    if not original_filename:
                        title = soup.find("title")
                        if title:
                            original_filename = title.get_text().replace(".xhtml", ".srt")

                    # From filename itself
                    if not original_filename:
                        original_filename = file.replace(".xhtml", ".srt")

                    # Extract all text content and try to reconstruct SRT
                    all_paragraphs = soup.find_all("p")
                    srt_blocks = []
                    current_block = []

                    for p in all_paragraphs:
                        text = p.get_text().strip()
                        if text:
                            current_block.append(text)

                        # When we have a complete block (number, timestamp, text)
                        if len(current_block) >= 3:
                            # Check if this looks like an SRT block
                            if (
                                current_block[0].isdigit()
                                and "-->" in current_block[1]
                                and len(current_block[2]) > 0
                            ):
                                srt_blocks.append(current_block)
                            current_block = []

                    if srt_blocks:
                        srt_lines = []
                        for block in srt_blocks:
                            srt_lines.append(block[0])  # Number
                            srt_lines.append(block[1])  # Timestamp
                            srt_lines.append(block[2])  # Text
                            if len(block) > 3:  # Chinese translation
                                srt_lines.append(block[3])
                            srt_lines.append("")

                        srt_content = "\n".join(srt_lines)
                        output_path = os.path.join(extract_dir, original_filename)

                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(srt_content)

                        srt_files.append(output_path)
                        print(f"Extracted via alternative: {original_filename}")

                except Exception as e:
                    print(f"Error in alternative extraction for {file}: {e}")
                    continue

    return srt_files


def debug_calibre_structure(extract_dir):
    """Debug function to understand Calibre's EPUB structure"""
    print("\n=== DEBUG: Calibre EPUB Structure ===")

    # Examine a few sample files to understand the structure
    sample_files = []
    for root, _, files in os.walk(os.path.join(extract_dir, "EPUB")):
        for file in files:
            if file.endswith(".xhtml") and not file.startswith("nav."):
                sample_files.append(os.path.join(root, file))
                if len(sample_files) >= 5:  # Limit to 5 samples
                    break
        if len(sample_files) >= 5:
            break

    for file_path in sample_files:
        print(f"\n--- Examining: {os.path.basename(file_path)} ---")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")

            # Show document structure
            print("HTML structure:")
            for tag in soup.find_all():
                if tag.name in ["p", "div", "span"]:
                    class_attr = tag.get("class", [])
                    if class_attr:
                        print(f"  <{tag.name} class='{' '.join(class_attr)}'>")
                    else:
                        print(f"  <{tag.name}>")

            # Show text content
            print("\nText content (first 200 chars):")
            text = soup.get_text()[:200]
            print(f"  {text}...")

            # Look for specific patterns
            paragraphs = soup.find_all("p")
            print(f"\nFound {len(paragraphs)} paragraphs:")
            for i, p in enumerate(paragraphs[:5]):  # First 5 paragraphs
                text = p.get_text().strip()
                print(f"  {i+1}. {text[:100]}{'...' if len(text) > 100 else ''}")

        except Exception as e:
            print(f"Error examining {file_path}: {e}")


def debug_epub_structure(extract_dir):
    """Debug function to examine the structure of the extracted EPUB"""
    print("\n=== DEBUG: EPUB Structure ===")

    # Find all XHTML files and examine their content
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".xhtml"):
                xhtml_path = os.path.join(root, file)
                print(f"\nExamining: {file}")

                try:
                    with open(xhtml_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    soup = BeautifulSoup(content, "html.parser")

                    # Check for our specific classes
                    srt_divs = soup.find_all("div", class_="srt-file")
                    print(f"Found {len(srt_divs)} srt-file divs")

                    for i, srt_div in enumerate(srt_divs):
                        print(f"  srt-file #{i}:")
                        print(f"    data-filename: {srt_div.get('data-filename', 'None')}")

                        # Check for subtitle blocks
                        subtitle_blocks = srt_div.find_all("div", class_="subtitle-block")
                        print(f"    Found {len(subtitle_blocks)} subtitle-block divs")

                        # Check for text content
                        text_elems = srt_div.find_all("p", class_="subtitle-text")
                        print(f"    Found {len(text_elems)} subtitle-text paragraphs")

                        if text_elems:
                            print("    Sample text content:")
                            for j, text_elem in enumerate(text_elems[:3]):  # Show first 3
                                print(f"      {j+1}. {text_elem.get_text()[:100]}...")

                except Exception as e:
                    print(f"Error examining {file}: {e}")


def transliterate_srt_files(srt_files, target_language):
    """Apply transliteration to all SRT files"""
    transliterated_files = []

    for srt_file in srt_files:
        try:
            transliterated_file = transliterate_srt(srt_file, target_language)
            transliterated_files.append(transliterated_file)
            print(f"Transliterated: {os.path.basename(transliterated_file)}")
        except Exception as e:
            print(f"Error transliterating {srt_file}: {e}")
            transliterated_files.append(srt_file)  # Keep original if transliteration fails

    return transliterated_files


def complete_workflow(input_zip_path, target_languages=["zh-ch"]):
    try:
        # Get the directory of the input ZIP file
        zip_dir = os.path.dirname(os.path.abspath(input_zip_path))
        zip_filename = os.path.basename(input_zip_path)
        base_name = os.path.splitext(zip_filename)[0]

        # Create output paths
        epub_path = os.path.join(zip_dir, f"{base_name}.epub")
        translated_epub_path = os.path.join(zip_dir, f"{base_name}-db-{target_languages[0]}.epub")
        output_zip_path = os.path.join(zip_dir, f"translated_{base_name}.zip")
        final_zip_path = os.path.join(zip_dir, f"transliterated_{base_name}.zip")

        print(f"Input ZIP: {input_zip_path}")
        print(f"Output EPUB: {epub_path}")
        print(f"Expected translated EPUB: {translated_epub_path}")

        # Step 1: Convert ZIP of SRTs to EPUB
        process_zip_to_epub(input_zip_path, epub_path)

        print("\n" + "=" * 60)
        print("STEP 1 COMPLETE: SRTs merged into EPUB")
        print("=" * 60)
        print(f"EPUB created at: {epub_path}")
        print("\nNow please:")
        print("1. Open Calibre and load the EPUB")
        print("2. Use Calibre's translation feature to translate to Chinese")
        print(f"3. Save the translated EPUB as: {translated_epub_path}")
        print("=" * 60)

        input("Press Enter after you've completed the translation in Calibre...")

        # Step 2: Check if translated EPUB exists
        if not os.path.exists(translated_epub_path):
            print(f"Translated EPUB not found at: {translated_epub_path}")
            translated_epub_path = (
                input("Enter the full path to the translated EPUB file: ").strip().strip('"')
            )

        if not os.path.exists(translated_epub_path):
            raise FileNotFoundError(f"Translated EPUB not found: {translated_epub_path}")

        # Step 3: Debug the Calibre structure first
        print("Analyzing Calibre's EPUB structure...")
        debug_extract_dir = "debug_extract"
        os.makedirs(debug_extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(translated_epub_path, "r") as zip_ref:
                zip_ref.extractall(debug_extract_dir)
            debug_calibre_structure(debug_extract_dir)
        finally:
            shutil.rmtree(debug_extract_dir, ignore_errors=True)

        # Step 4: Convert translated EPUB back to SRTs
        print("Converting translated EPUB back to SRT files...")
        srt_files = epub_to_srts(translated_epub_path, output_zip_path)

        if not srt_files:
            print("Warning: No SRT files were extracted from the translated EPUB")
            print("The EPUB structure may be different than expected.")

        if srt_files:
            # Step 4: Apply transliteration to all SRT files
            print("Applying transliteration to SRT files...")
            transliterated_files = []

            # Extract SRT files for transliteration
            transliterate_dir = "transliterate_temp"
            os.makedirs(transliterate_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(output_zip_path, "r") as zip_ref:
                    zip_ref.extractall(transliterate_dir)

                # Find all SRT files in the extracted directory
                srt_files_to_transliterate = []
                for root, _, files in os.walk(transliterate_dir):
                    for file in files:
                        if file.lower().endswith(".srt"):
                            srt_files_to_transliterate.append(os.path.join(root, file))

                # Apply transliteration to each file
                for srt_file in srt_files_to_transliterate:
                    for target_lang in target_languages:
                        transliterated_file = transliterate_srt(srt_file, target_lang)
                        transliterated_files.append(transliterated_file)

            finally:
                shutil.rmtree(transliterate_dir, ignore_errors=True)

            # Step 5: Create final zip with transliterated files
            with zipfile.ZipFile(final_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for trans_file in transliterated_files:
                    zipf.write(trans_file, os.path.basename(trans_file))

            print(f"\nWorkflow complete!")
            print(f"Translated SRTs: {output_zip_path}")
            print(f"Transliterated SRTs: {final_zip_path}")

    except Exception as e:
        print(f"Error in workflow: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Use the specific path you provided
    input_zip = "/home/zaya/Documents/Gitrepos/Linktrees/test.zip"
    target_languages = ["zh-ch"]

    # if not os.path.exists(input_zip):
    #     print(f"File not found: {input_zip}")
    #     input_zip = input("Enter the path to your SRT files ZIP: ").strip().strip('"')

    # if os.path.exists(input_zip):
    #     complete_workflow(input_zip, target_languages)
    # else:
    #     print(f"File not found: {input_zip}")
    translated_epub_path = "/home/zaya/Documents/Gitrepos/Linktrees/all_subtitles-db-zh-ch.epub"
    output_zip_path = "/home/zaya/Documents/Gitrepos/Linktrees/all_subtitles-db-zh-ch.zip"
    final_zip_path = "/home/zaya/Documents/Gitrepos/Linktrees/transliterated_all_subtitles.zip"

    # Step 3: Debug the Calibre structure first
    print("Analyzing Calibre's EPUB structure...")
    debug_extract_dir = "debug_extract"
    os.makedirs(debug_extract_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(translated_epub_path, "r") as zip_ref:
            zip_ref.extractall(debug_extract_dir)
        debug_calibre_structure(debug_extract_dir)
    finally:
        shutil.rmtree(debug_extract_dir, ignore_errors=True)

    # Step 4: Convert translated EPUB back to SRTs
    print("Converting translated EPUB back to SRT files...")
    srt_files = epub_to_srts(translated_epub_path, output_zip_path)

    if not srt_files:
        print("Warning: No SRT files were extracted from the translated EPUB")
        print("The EPUB structure may be different than expected.")

    if srt_files:
        # Step 4: Apply transliteration to all SRT files
        print("Applying transliteration to SRT files...")
        transliterated_files = []

        # Extract SRT files for transliteration
        transliterate_dir = "transliterate_temp"
        os.makedirs(transliterate_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(output_zip_path, "r") as zip_ref:
                zip_ref.extractall(transliterate_dir)

            # Find all SRT files in the extracted directory
            srt_files_to_transliterate = []
            for root, _, files in os.walk(transliterate_dir):
                for file in files:
                    if file.lower().endswith(".srt"):
                        srt_files_to_transliterate.append(os.path.join(root, file))

            # Apply transliteration to each file
            for srt_file in srt_files_to_transliterate:
                for target_lang in target_languages:
                    transliterated_file = transliterate_srt(srt_file, target_lang)
                    transliterated_files.append(transliterated_file)

        finally:
            shutil.rmtree(transliterate_dir, ignore_errors=True)

        # Step 5: Create final zip with transliterated files
        with zipfile.ZipFile(final_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for trans_file in transliterated_files:
                zipf.write(trans_file, os.path.basename(trans_file))

        print(f"\nWorkflow complete!")
        print(f"Translated SRTs: {output_zip_path}")
        print(f"Transliterated SRTs: {final_zip_path}")
