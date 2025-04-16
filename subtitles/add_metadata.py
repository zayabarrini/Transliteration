#!/usr/bin/env python3
import os
import re
import random
import yaml
from pathlib import Path

def generate_metadata(title, file_type="subtitles"):
    """Generate YAML metadata block with random cover image"""
    random_num = random.randint(1, 214)
    metadata = {
        "title": [
            {"type": "main", "text": title},
            {"type": "subtitle", "text": file_type}
        ],
        "creator": [
            {"role": "author", "text": "Zaya Barrini"},
            {"role": "editor", "text": "Zaya Barrini"}
        ],
        "cover-image": f"/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_num}.png",
        "identifier": [
            {"scheme": "DOI", "text": f"doi:10.234234.234/{random_num}"}
        ],
        "publisher": "My Press",
        "rights": "© 2024 Zaya Barrini, CC BY-NC",
        "ibooks": {"version": "1.3.4"}
    }
    return yaml.dump(metadata, sort_keys=False, allow_unicode=True)

def add_metadata_to_file(md_file):
    """Add metadata to a single markdown file"""
    # Get clean title from filename (without extension)
    title = Path(md_file).stem
    title = re.sub(r'[_-]', ' ', title)  # Replace _ and - with spaces
    title = re.sub(r'\s+', ' ', title).strip()  # Clean extra spaces
    
    # Generate metadata
    metadata = generate_metadata(title)
    
    # Read existing content
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if metadata already exists
    if content.startswith('---\n'):
        print(f"Skipping {md_file} (already has metadata)")
        return
    
    # Write new content with metadata
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"---\n{metadata}---\n\n{content}")
    
    print(f"Added metadata to: {md_file}")

def process_directory(directory):
    """Process all markdown files in a directory"""
    directory = Path(directory)
    if not directory.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return
    
    print(f"Processing markdown files in: {directory}")
    
    md_files = list(directory.glob('*.md'))
    if not md_files:
        print("No .md files found in directory")
        return
    
    for md_file in md_files:
        try:
            add_metadata_to_file(md_file)
        except Exception as e:
            print(f"Error processing {md_file.name}: {str(e)}")
    
    print("\nFinished processing all files")

if __name__ == "__main__":
    import sys
    # if len(sys.argv) != 2:
    #     print("Usage: python add_metadata.py <directory>")
    #     sys.exit(1)
    
    # target_dir = sys.argv[1]
    target_dir = "/home/zaya/Downloads/Workspace/Subtitles/TVSeries"

    process_directory(target_dir)