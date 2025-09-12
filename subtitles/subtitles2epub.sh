#!/bin/bash

# Configuration
DIRECTORY="/home/zaya/Documents/Gitrepos/Linktrees/ch-ru"
WORKING_DIR="/tmp/subtitle_processing"
OUTPUT_MD="combined_notes.md"
directory_name=$(basename "$DIRECTORY")
OUTPUT_EPUB="${directory_name}.epub"
COVER_IMAGES_DIR="/home/zaya/Downloads/Zayas/zayaweb/static/css/img/Bing"

mkdir -p "$WORKING_DIR"

# Function to check if filename is already formatted
is_filename_formatted() {
    python3 - <<END
import os
import re

def is_formatted(name):
    # Check if filename is already formatted (no dots/underscores in main part)
    name, ext = os.path.splitext(name)
    
    # If it contains dots or underscores in the main part, it's not formatted
    if re.search(r'[._]', name):
        return False
    
    # If it has spaces or hyphens instead of dots/underscores, it's formatted
    return True

original_name = "$1"
print(is_formatted(original_name))
END
}

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
with open("$WORKING_DIR/metadata.yaml", "w") as f:
    f.write(metadata)

print("Metadata file generated with random cover image:", cover_image)
END
}

# Step 1: Copy files to working directory, format only if needed
echo "Step 1/4: Copying files to working directory (formatting only if needed)..."
find "$DIRECTORY" -type f \( -name "*.srt" -o -name "*.md" \) | while read -r file; do
    echo "Processing: $file"
    base_name=$(basename "$file")
    
    # Check if filename is already formatted
    if is_filename_formatted "$base_name"; then
        formatted_filename="$base_name"
        echo "Filename already formatted: $base_name"
    else
        formatted_filename=$(format_filename "$base_name")
        echo "Formatting filename: $base_name -> $formatted_filename"
    fi

    # Copy file to working directory
    cp "$file" "$WORKING_DIR/$formatted_filename"
    echo "Copied to: $WORKING_DIR/$formatted_filename"
done

# Step 2: Clean subtitle files (working on copies)
echo "Step 2/4: Cleaning subtitle files..."
for file in "$WORKING_DIR"/*.srt; do
    if [[ -f "$file" ]]; then
        echo "Cleaning with perl: $(basename "$file")"

        # Use perl to process the file (your working regex)
        perl -CSD -i -0777 -pe '
            # Remove BOM character
            s/^\x{FEFF}//;

            # Remove HTML tags
            s/<[^>]*>//g;

            # Remove timestamp blocks (line number + timestamp line)
            s/^\d+\R\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\R//mg;

            # Remove any remaining individual timestamp lines
            s/^\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\R//mg;

            # Remove remaining line numbers
            s/^\d+\R//mg;

            # Remove leading/trailing whitespace from each line
            s/^\s+|\s+$//mg;

            # Join lines that should be together (continuations)
            s/\R([a-z,])/ $1/g;

            # THE KEY PART: Convert single newlines to double newlines (Vim equivalent)
            # This is the Perl equivalent of: %s/\([^\n]\)\n\([^\n]\)/\1\r\r\2/g
            s/([^\n])\n([^\n])/$1\n\n$2/g;

            # Clean up excessive newlines
            s/\n{3,}/\n\n/g;

            # Clean up any extra spaces
            s/ +/ /g;
            s/^\s+//;
            s/\s+$//;

        ' "$file"
        
        # Ensure UTF-8 encoding for non-Latin characters
        iconv -f "$(file -bi "$file" | sed -e 's/.*charset=//')" -t UTF-8 "$file" > "${file}.utf8"
        mv "${file}.utf8" "$file"
    fi
done

# Step 3: Combine files into a single markdown
echo "Step 3/4: Combining files into markdown..."
python3 - <<END
import os
import re
from pathlib import Path

def try_read_file(filepath):
    """Try reading a file with different encodings."""
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'utf-16']
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

combine_files("$WORKING_DIR", "$WORKING_DIR/$OUTPUT_MD")
END

# Step 4: Generate EPUB with metadata
echo "Step 4/4: Generating EPUB..."
if command -v pandoc &> /dev/null; then
    # Generate metadata file
    echo "Generating metadata..."
    generate_metadata

    # Create EPUB with metadata and cover image
    echo "Creating EPUB with metadata..."
    pandoc "$WORKING_DIR/$OUTPUT_MD" \
        --metadata-file="$WORKING_DIR/metadata.yaml" \
        --epub-cover-image="$COVER_IMAGES_DIR/$(ls $COVER_IMAGES_DIR | shuf -n 1)" \
        -o "$DIRECTORY/$OUTPUT_EPUB"

    # Clean up working directory
    rm -rf "$WORKING_DIR"
    echo "Working directory removed."

    echo "EPUB generated at: $DIRECTORY/$OUTPUT_EPUB"
else
    echo "Pandoc not found. EPUB generation skipped."
    echo "Combined markdown file kept at: $WORKING_DIR/$OUTPUT_MD"
    echo "Working directory preserved at: $WORKING_DIR"
fi

echo "All operations completed!"