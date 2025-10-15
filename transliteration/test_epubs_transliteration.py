import os
import unittest
import zipfile
from bs4 import BeautifulSoup
from transliteration.epubsTransliteration import (
    process_epub,
    get_language_from_filename,
    get_css_file,
)
from transliteration.add_metadata_and_cover import add_metadata_and_cover


class TestEpubsTransliteration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_epub_folder = "test_epubs"
        os.makedirs(cls.test_epub_folder, exist_ok=True)

        # Create a sample EPUB structure
        cls.sample_epub_path = os.path.join(cls.test_epub_folder, "test-book.epub")
        cls.create_sample_epub(cls.sample_epub_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if os.path.exists(cls.test_epub_folder):
            shutil.rmtree(cls.test_epub_folder)

    @staticmethod
    def create_sample_epub(epub_path):
        """Create a sample EPUB file for testing."""
        with zipfile.ZipFile(epub_path, "w") as zipf:
            # Create a minimal EPUB structure
            zipf.writestr("mimetype", "application/epub+zip")
            zipf.writestr(
                "META-INF/container.xml",
                """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            )
            zipf.writestr(
                "OEBPS/content.opf",
                """<?xml version="1.0"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf">
  <metadata>
    <dc:title id="title">Test Book</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="cover" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
</package>""",
            )
            zipf.writestr(
                "OEBPS/Text/cover.xhtml",
                """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Cover</title>
  </head>
  <body>
    <img src="cover.png" alt="Cover"/>
  </body>
</html>""",
            )

    def test_transliteration(self):
        """Test if transliteration is applied to HTML files."""
        process_epub(self.sample_epub_path)
        extract_to = self.sample_epub_path.replace(".epub", "")
        text_folder = os.path.join(extract_to, "OEBPS", "Text")

        # Check if transliteration is applied
        for filename in os.listdir(text_folder):
            if filename.endswith(".xhtml"):
                with open(os.path.join(text_folder, filename), "r", encoding="utf-8") as file:
                    content = file.read()
                    self.assertIn(
                        "Transliterated", content
                    )  # Replace with actual transliteration check

    def test_css_styles(self):
        """Test if CSS styles are applied based on the language."""
        language = get_language_from_filename("japanese-test-book.epub")
        css_file = get_css_file(language)
        self.assertEqual(
            css_file, "/home/zaya/Downloads/Zayas/ZayasTransliteration/styles-ch-jp.css"
        )

    def test_metadata(self):
        """Test if metadata is properly applied."""
        extract_to = self.sample_epub_path.replace(".epub", "")
        add_metadata_and_cover(extract_to, "Test Book", "en")

        # Check metadata in content.opf
        opf_path = os.path.join(extract_to, "OEBPS", "content.opf")
        with open(opf_path, "r", encoding="utf-8") as opf_file:
            opf_soup = BeautifulSoup(opf_file, "xml")
            dc_title = opf_soup.find("dc:title")
            dc_creator = opf_soup.find("dc:creator")
            dc_date = opf_soup.find("dc:date")
            dc_language = opf_soup.find("dc:language")

            self.assertEqual(dc_title.string, "Test Book")
            self.assertEqual(dc_creator.string, "Zaya Barrini")
            self.assertEqual(dc_language.string, "en")
            self.assertIsNotNone(dc_date)  # Date should be added

    def test_cover_image(self):
        """Test if the cover image is added."""
        extract_to = self.sample_epub_path.replace(".epub", "")
        add_metadata_and_cover(extract_to, "Test Book", "en")

        # Check cover.xhtml for the cover image
        cover_xhtml_path = os.path.join(extract_to, "OEBPS", "Text", "cover.xhtml")
        with open(cover_xhtml_path, "r", encoding="utf-8") as cover_file:
            cover_soup = BeautifulSoup(cover_file, "html.parser")
            img_tag = cover_soup.find("img")
            self.assertIsNotNone(img_tag)
            self.assertTrue(img_tag["src"].endswith(".png"))  # Cover image should be a PNG


if __name__ == "__main__":
    unittest.main()
