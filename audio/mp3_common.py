import os
import re
from urllib.parse import quote
from pathlib import Path


def get_clean_md_content(md_file_path):
    """Read and clean markdown content"""
    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r"^#.*$", "", content, flags=re.MULTILINE)
    return " ".join(content.split())


def split_text(text, chunk_size):
    """Split text into chunks respecting word boundaries"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks


def combine_audio_files(input_files, output_path):
    """Combine multiple audio files using simple binary concatenation"""
    with open(output_path, "wb") as outfile:
        for filename in input_files:
            with open(filename, "rb") as infile:
                outfile.write(infile.read())
            os.remove(filename)
