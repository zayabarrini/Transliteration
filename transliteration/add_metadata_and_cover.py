import os
import random
import shutil
from bs4 import BeautifulSoup
from datetime import datetime


def add_metadata_and_cover(epub_folder, base_name, language, date=None):
    """
    Adds metadata and a cover image to the EPUB.

    Args:
        epub_folder (str): Path to the extracted EPUB folder.
        base_name (str): Base name of the EPUB (used for title).
        language (str): Language of the EPUB (e.g., 'en', 'ja', 'ar').
        date (str, optional): Date in YYYY-MM-DD format. Defaults to today's date.
    """
    # Set default date to today if not provided
    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    # Define metadata
    metadata = {
        "title": base_name,
        "author": "Zaya Barrini",
        "website": "https://zayabarrini.vercel.app/",
        "language": language,
        "date": date,
    }

    # Find the content.opf file
    opf_path = None
    for root, dirs, files in os.walk(epub_folder):
        if "content.opf" in files:
            opf_path = os.path.join(root, "content.opf")
            break

    if not opf_path:
        print("Warning: content.opf file not found. Metadata and cover will not be added.")
        return

    # Parse the content.opf file
    with open(opf_path, "r", encoding="utf-8") as opf_file:
        opf_soup = BeautifulSoup(opf_file, "xml")

    # Update <dc:title>
    dc_title = opf_soup.find("dc:title")
    if dc_title:
        dc_title.string = metadata["title"]
    else:
        dc_title = opf_soup.new_tag("dc:title")
        dc_title.string = metadata["title"]
        opf_soup.metadata.append(dc_title)

    # Update <dc:creator>
    dc_creator = opf_soup.find("dc:creator")
    if dc_creator:
        dc_creator.string = metadata["author"]
        dc_creator["opf:file-as"] = "Barrini, Zaya"  # Update opf:file-as
    else:
        dc_creator = opf_soup.new_tag(
            "dc:creator", attrs={"opf:role": "aut", "opf:file-as": "Barrini, Zaya"}
        )
        dc_creator.string = metadata["author"]
        opf_soup.metadata.append(dc_creator)

    # Update <dc:date>
    dc_date = opf_soup.find("dc:date")
    if dc_date:
        dc_date.string = metadata["date"]
    else:
        dc_date = opf_soup.new_tag("dc:date")
        dc_date.string = metadata["date"]
        opf_soup.metadata.append(dc_date)

    # Update <dc:language>
    dc_language = opf_soup.find("dc:language")
    if dc_language:
        dc_language.string = metadata["language"]
    else:
        dc_language = opf_soup.new_tag("dc:language")
        dc_language.string = metadata["language"]
        opf_soup.metadata.append(dc_language)

    # Add website as <dc:identifier>
    dc_identifier = opf_soup.new_tag("dc:identifier", attrs={"id": "website", "opf:scheme": "url"})
    dc_identifier.string = metadata["website"]
    opf_soup.metadata.append(dc_identifier)

    # Copy the cover image to the EPUB folder
    random_number = random.randint(1, 211)
    source_image_path = (
        f"/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_number}.png"
    )
    media_folder = (
        os.path.join(epub_folder, "EPUB", "media")
        if os.path.exists(os.path.join(epub_folder, "EPUB"))
        else os.path.join(epub_folder, "OEBPS", "media")
    )
    os.makedirs(media_folder, exist_ok=True)
    dest_image_path = os.path.join(media_folder, f"bing{random_number}.png")
    shutil.copy(source_image_path, dest_image_path)

    # Add cover image to the manifest
    cover_item = opf_soup.find("item", id="cover")
    if cover_item:
        cover_item["href"] = os.path.relpath(dest_image_path, os.path.dirname(opf_path))
    else:
        cover_item = opf_soup.new_tag(
            "item",
            attrs={
                "id": "cover",
                "href": os.path.relpath(dest_image_path, os.path.dirname(opf_path)),
                "media-type": "image/png",
            },
        )
        opf_soup.manifest.append(cover_item)

    # Add <meta name="cover">
    meta_cover = opf_soup.find("meta", attrs={"name": "cover"})
    if meta_cover:
        meta_cover["content"] = "cover"
    else:
        meta_cover = opf_soup.new_tag("meta", attrs={"name": "cover", "content": "cover"})
        opf_soup.metadata.append(meta_cover)

    # Update <guide> section
    guide = opf_soup.find("guide")
    if guide:
        for reference in guide.find_all("reference"):
            if reference.get("type") == "toc":
                reference["title"] = metadata["title"]  # Update title in guide

    # Save the updated content.opf file
    with open(opf_path, "w", encoding="utf-8") as opf_file:
        opf_file.write(str(opf_soup))

    print(f"Updated metadata and cover in {opf_path}")
