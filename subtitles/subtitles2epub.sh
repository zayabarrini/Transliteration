#!/bin/bash

# Configuration
DIRECTORY="/home/zaya/Downloads/Workspace/Subtitles/Survivor/AU/SurvivorAuS13"
OUTPUT_MD="combined_notes.md"
directory_name=$(basename "$DIRECTORY")
OUTPUT_EPUB="${directory_name}.epub"
COVER_IMAGES_DIR="/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing"

# Function to format the file name using Python for more sophisticated processing
format_filename() {
    python3 - <<END
import os
import re

def format_filename(name):
    # Remove file extension
    name, ext = os.path.splitext(name)
    
    # Replace dots or underscores with spaces
    name = re.sub(r'[._]', ' ', name)
    
    # Keep only the name and the year (if available)
    match = re.match(r'(.*?)(\s\d{4})', name)
    if match:
        name = match.group(1) + match.group(2)  # Name and year
    else:
        # Remove everything after the first non-alphabetic group
        name = re.sub(r'[^a-zA-Z0-9\s]+.*$', '', name)
        
    # Remove extra spaces and replace with single hyphen
    name = re.sub(r'\s+', '-', name).strip()
    # Add the extension back
    return f"{name.strip()}{ext.lower()}"

original_name = "$1"
print(format_filename(original_name))
END
}

# Generate metadata YAML file
generate_metadata() {
    python3 - <<END
import random
import uuid
from datetime import datetime
import os

# Generate random values
random_number = random.randint(1, 211)
date = datetime.today().strftime('%Y-%m-%d')
directory_name = os.path.basename("$DIRECTORY")
cover_image = f"$COVER_IMAGES_DIR/bing{random_number}.png"

# Create metadata YAML
metadata = f"""---
title:
  - type: main
    text: "{directory_name}"
  - type: subtitle
    text: "Cinema Screenplays"
creator:
  - role: author
    text: "Zaya Barrini"
  - role: editor
    text: "Zaya Barrini"
date: "{date}"
cover-image: "{cover_image}"
identifier:
  - scheme: UUID
    text: "{str(uuid.uuid4())}"
publisher: "Zaya's Language Press"
rights: "© {datetime.today().year} Zaya Barrini, CC BY-NC"
language: "en"
ibooks:
  version: 1.3.4
...
"""

# Write to temporary file
with open("$DIRECTORY/metadata.yaml", "w") as f:
    f.write(metadata)

print("Metadata file generated with random cover image:", cover_image)
END
}

# Step 1: Format filenames
# echo "Step 1/4: Formatting filenames..."
# find "$DIRECTORY" -type f | while read -r file; do
#     echo "Processing: $file"
#     base_name=$(basename "$file")
#     formatted_filename=$(format_filename "$base_name")
#     dir_path=$(dirname "$file")
    
#     # Only rename if the filename changed
#     if [ "$base_name" != "$formatted_filename" ]; then
#         mv "$file" "${dir_path}/$formatted_filename"
#         echo "Renamed to: ${dir_path}/$formatted_filename"
#     else
#         echo "No change needed for: $base_name"
#     fi
# done

# Step 2: Clean subtitle files
echo "Step 2/4: Cleaning subtitle files..."
for file in "$DIRECTORY"/*; do
    if [[ ! -f "$file" ]]; then
        continue
    fi

    echo "Cleaning: $file"
    nvim -es "$file" <<EOF
    " Step 1: Remove SRT timestamps and line numbers
    g/^\d\+\n\d\{2\}:\d\{2\}:\d\{2\},\d\{3\} --> \d\{2\}:\d\{2\}:\d\{2\},\d\{3\}/d2

    " Remove HTML italic tags
    %s/<\/\?i>//g

    " Delete all remaining empty lines (leaving only paragraph separators)
    g/^$/d

    " Remove unwanted space at beginning of lines
    %s/^\s\+//

    " Join lines if the next line starts with a lowercase letter
    %s/\n\(\l\)/ \1/g

    " Convert single newlines into double newlines (paragraph breaks)
    %s/\([^\n]\)\n\([^\n]\)/\1\r\r\2/g

    " Save the changes and exit
    wq
EOF
done

# Step 3: Combine files into a single markdown
echo "Step 3/4: Combining files into markdown..."
python3 - <<END
import os
import re
from pathlib import Path

def try_read_file(filepath):
    """Try reading a file with different encodings."""
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Could not decode {filepath} with any of the tried encodings")

def format_header(name):
    """Format the filename into a nice header title"""
    name = re.sub(r'[._]', ' ', name)  # Replace dots/underscores with spaces
    name = re.sub(r'\s+', ' ', name).strip()  # Collapse multiple spaces
    return name

def combine_files(directory, output_filename):
    """
    Combine all .md and .srt files in a directory into a single markdown file.
    Each file's content is preceded by its filename as a header.
    """
    files = []
    for ext in ('*.md', '*.srt'):
        files.extend(Path(directory).glob(ext))
    
    if not files:
        print(f"No .md or .srt files found in {directory}")
        return
    
    files.sort()
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for file in files:
            # Format header from filename (without extension)
            header_title = format_header(file.stem)
            header = f"# {header_title}\n\n"
            outfile.write(header)
            
            try:
                content = try_read_file(file)
                
                if file.suffix == '.srt':
                    outfile.write(content)
                    outfile.write("\n\n")
                else:
                    outfile.write(content)
                    outfile.write("\n\n")
                
                print(f"Added: {file.name}")
            
            except UnicodeDecodeError as e:
                print(f"Error reading {file.name}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing {file.name}: {str(e)}")
                continue
    
    print(f"\nSuccessfully created combined file at:\n{output_filename}")

combine_files("$DIRECTORY", "$DIRECTORY/$OUTPUT_MD")
END

# Step 4: Generate EPUB with metadata
echo "Step 4/4: Generating EPUB..."
if command -v pandoc &> /dev/null; then
    # Generate metadata file
    echo "Generating metadata..."
    generate_metadata
    
    # Create EPUB with metadata and cover image
    echo "Creating EPUB with metadata..."
    pandoc "$DIRECTORY/$OUTPUT_MD" \
        --metadata-file="$DIRECTORY/metadata.yaml" \
        --epub-cover-image="$COVER_IMAGES_DIR/$(ls $COVER_IMAGES_DIR | shuf -n 1)" \
        -o "$DIRECTORY/$OUTPUT_EPUB"
    
    # Clean up temporary files
    rm "$DIRECTORY/$OUTPUT_MD" "$DIRECTORY/metadata.yaml"
    echo "Temporary files removed."
    
    echo "EPUB generated at: $DIRECTORY/$OUTPUT_EPUB"
else
    echo "Pandoc not found. EPUB generation skipped."
    echo "Combined markdown file kept at: $DIRECTORY/$OUTPUT_MD"
fi

echo "All operations completed!"