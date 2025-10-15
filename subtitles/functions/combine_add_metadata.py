import os
import re
import random
from pathlib import Path
import yaml


def generate_metadata(title, file_type="subtitles"):
    """Generate YAML metadata block with random cover image"""
    random_num = random.randint(1, 214)
    metadata = {
        "title": [{"type": "main", "text": title}, {"type": "subtitle", "text": file_type}],
        "creator": [
            {"role": "author", "text": "Zaya Barrini"},
            {"role": "editor", "text": "Zaya Barrini"},
        ],
        "cover-image": f"/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing/bing{random_num}.png",
        "identifier": [{"scheme": "DOI", "text": f"doi:10.234234.234/{random_num}"}],
        "publisher": "My Press",
        "rights": "© 2024 Zaya Barrini, CC BY-NC",
        "ibooks": {"version": "1.3.4"},
    }
    return yaml.dump(metadata, sort_keys=False, allow_unicode=True)


def process_folder(folder_path):
    """Process a folder to create combined file with metadata"""
    # Determine if it's a TV series or movie
    is_tv_series = any(re.search(r"[Ss]\d+[Ee]\d+", f.name) for f in folder_path.iterdir())

    # Get all text files
    text_files = list(folder_path.glob("*.{srt,md,txt}"))

    if not text_files:
        print(f"No text files found in {folder_path.name}")
        return

    # Create output filename
    output_file = folder_path / f"{folder_path.name}.md"

    # Generate metadata
    metadata = generate_metadata(
        folder_path.name, "TV Subtitles" if is_tv_series else "Movie Subtitles"
    )

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"---\n{metadata}---\n\n")

        for file in sorted(text_files):
            # Add section header
            if is_tv_series:
                ep_match = re.search(r"([Ss]\d+[Ee]\d+)", file.stem)
                if ep_match:
                    f.write(f"## {ep_match.group(1)}\n\n")

            # Add file content
            try:
                content = file.read_text(encoding="utf-8")
                if file.suffix == ".{srt,md,txt}":
                    f.write(f"{content}\n\n")
                else:
                    f.write(f"{content}\n\n")
            except UnicodeDecodeError:
                try:
                    content = file.read_text(encoding="latin-1")
                    f.write(f"{content}\n\n")
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    print(f"Created: {output_file}")


def process_all_folders(root_dir):
    """Process all subfolders in the root directory"""
    root_path = Path(root_dir)
    if not root_path.exists():
        print(f"Directory not found: {root_dir}")
        return

    print(f"Processing folders in: {root_dir}")

    for folder in root_path.iterdir():
        if folder.is_dir():
            print(f"\nProcessing: {folder.name}")
            process_folder(folder)

    print("\nProcessing complete!")


if __name__ == "__main__":
    # directory = input("Enter directory path: ").strip()
    directory = "/home/zaya/Downloads/Topology"
    process_all_folders(directory)
