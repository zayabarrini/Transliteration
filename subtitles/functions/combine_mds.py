import os
import re
import random
from pathlib import Path
import subprocess
import yaml

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

def clean_markdown_content(content):
    """Applies transformations to markdown content."""
    # Reduce headers: # → ##, ## → ###
    content = re.sub(r'^(#{1,4})(\s+)', lambda m: f'{"#" * (len(m.group(1)) + 1)}{m.group(2)}', content, flags=re.MULTILINE)

    # Replace "You:\n\n" with "# "
    content = re.sub(r'(?m)^You:\s*\n\n', '# ', content)

    # Remove "Chatgpt:"
    content = re.sub(r'(?m)^Chatgpt:\s*\n', '', content)
    
    # Ensures an extra newline before tables in markdown content.
    # content = re.sub(r'(?<!\n\n)\|', r'\n\n|', content)

    return content

def process_folder(folder_path):
    """Process all text and markdown files in a folder, merging them into one file"""
    # Get all text and markdown files
    text_files = list(folder_path.glob('*.{srt,txt}'))
    md_files = list(folder_path.glob('*.md'))
    
    if not text_files and not md_files:
        print(f"No text or markdown files found in {folder_path.name}")
        return
    
    # Create output filename
    output_file = folder_path / f"{folder_path.name}.md"
    metadata = generate_metadata(folder_path.name)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"---\n{metadata}---\n\n")
        
        # Process markdown files first
        for file in sorted(md_files):
            # Add section header with filename (without extension)
            section_title = file.stem.replace('_', ' ').title()
            f.write(f"# {section_title}\n\n")
            
            # Add file content
            try:
                content = file.read_text(encoding='utf-8')
                content = clean_markdown_content(content)

                f.write(f"{content}\n\n")
            except UnicodeDecodeError:
                try:
                    content = file.read_text(encoding='latin-1')
                    f.write(f"{content}\n\n")
                except Exception as e:
                    print(f"Error reading {file}: {e}")
        
        # Process other text files
        for file in sorted(text_files):
            # Add section header with filename (without extension)
            section_title = file.stem.replace('_', ' ').title()
            f.write(f"# {section_title}\n\n")
            
            # Add file content
            try:
                content = file.read_text(encoding='utf-8')
                content = clean_markdown_content(content)

                f.write(f"```text\n{content}\n```\n\n")
            except UnicodeDecodeError:
                try:
                    content = file.read_text(encoding='latin-1')
                    f.write(f"```text\n{content}\n```\n\n")
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    
        css_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/web/static/md-table.css"
        epub_filename = folder_path / f"{folder_path.name}.epub"

        pandoc_cmd = [
            'pandoc',
            '-s', output_file,
            '-o', epub_filename,
            '--toc',
            '--toc-depth=2',
            f'--css={css_path}',
        ]
        
        try:
            subprocess.run(pandoc_cmd, check=True)
            print(f"Successfully created {epub_filename}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting to EPUB: {e}")
    
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
    directory = "/home/zaya/Downloads/Workspace/Subtitles/TVSeries/HP"
    process_all_folders(directory)