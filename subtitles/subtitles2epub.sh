#!/bin/bash

# Configuration
DIRECTORY="/home/zaya/Downloads/Drag-Race"
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
    name, ext = os.path.splitext(name)
    # Check if filename contains dots or underscores (not formatted)
    if re.search(r'[._]', name.replace('-', '').replace(' ', '')):
        return False
    return True

original_name = "$1"
print(is_formatted(original_name))
END
}

# Function to format the file name
format_filename() {
    python3 - <<END
import os
import re

def format_filename(name):
    name, ext = os.path.splitext(name)
    
    # Replace dots and underscores with spaces
    name = re.sub(r'[._]', ' ', name)
    
    # Remove common subtitle tags
    name = re.sub(r'\b(English|WWW|MY|SUBS|CO|DIMENSION|AVS)\b', '', name, flags=re.IGNORECASE)
    
    # Clean up: remove extra spaces, special characters, and normalize
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.replace(' ', '-')
    
    return f"{name}{ext.lower()}"

original_name = "$1"
print(format_filename(original_name))
END
}

# Function to detect file encoding
detect_encoding() {
    python3 - <<END
import chardet

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

filepath = "$1"
print(detect_encoding(filepath))
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
cover_images = [f for f in os.listdir("$COVER_IMAGES_DIR") if f.startswith('bing') and f.endswith('.png')]
cover_image = f"$COVER_IMAGES_DIR/{random.choice(cover_images)}" if cover_images else ""

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

# Improved subtitle cleaning function
# Improved subtitle cleaning function
clean_subtitle_file() {
    local file="$1"
    local temp_file="${file}.cleaned"
    
    echo "Cleaning: $(basename "$file")"
    
    # First, ensure the file is in UTF-8 encoding
    local detected_encoding=$(detect_encoding "$file")
    echo "Detected encoding: $detected_encoding"
    
    # Convert to UTF-8 first to temp file
    if ! iconv -f "$detected_encoding" -t UTF-8 "$file" > "$temp_file" 2>/dev/null; then
        echo "Warning: Encoding conversion failed, trying fallback methods..."
        # Fallback: use Python for encoding conversion
        python3 -c "
try:
    with open('$file', 'rb') as f:
        content = f.read()
    # Try to decode with common encodings
    for encoding in ['utf-8', 'latin-1', 'windows-1252', 'cp1252']:
        try:
            text = content.decode(encoding)
            with open('$temp_file', 'w', encoding='utf-8') as out:
                out.write(text)
            print(f'Successfully converted with {encoding}')
            break
        except UnicodeDecodeError:
            continue
except Exception as e:
    print(f'Error in fallback conversion: {e}')
    # Last resort: copy as is
    import shutil
    shutil.copy2('$file', '$temp_file')
"
    fi
    
    # Now clean the UTF-8 temp file with more robust Perl processing
    perl -CSD -0777 -pe '
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

            # Remove hash symbols
            s/#//g;

            # THE KEY PART: Convert single newlines to double newlines (Vim equivalent)
            # This is the Perl equivalent of: %s/\([^\n]\)\n\([^\n]\)/\1\r\r\2/g
            s/([^\n])\n([^\n])/$1\n\n$2/g;

            # Clean up excessive newlines
            s/\n{3,}/\n\n/g;

            # Clean up any extra spaces
            s/ +/ /g;
            s/^\s+//;
            s/\s+$//;
    ' "$temp_file" > "${temp_file}.cleaned"
    
    # Replace original with the final cleaned file
    mv "${temp_file}.cleaned" "$file"
    rm -f "$temp_file"
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
        clean_subtitle_file "$file"
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
    encodings = ['utf-8', 'latin-1', 'windows-1252', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read(), encoding
        except UnicodeDecodeError:
            continue
    # Last resort: read as binary and decode with error handling
    with open(filepath, 'rb') as f:
        return f.read().decode('utf-8', errors='replace'), 'utf-8 (with errors)'

def format_header(name):
    """Format the filename into a nice header title"""
    name = re.sub(r'[._]', ' ', name)  # Replace dots/underscores with spaces
    name = re.sub(r'\s+', ' ', name).strip()  # Collapse multiple spaces
    # Remove common subtitle tags
    name = re.sub(r'\b(english|www|my|subs|co|dimension|avs|srt)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

def combine_files(directory, output_filename):
    """
    Combine all .md and .srt files in a directory into a single markdown file.
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
                content, used_encoding = try_read_file(file)
                print(f"Added: {file.name} (encoding: {used_encoding})")
                
                # Additional cleaning for markdown
                if file.suffix == '.srt':
                    # Remove any remaining timestamp artifacts
                    content = re.sub(r'\d{1,2}:\d{2}:\d{2}[,.]\d{3}.*?\n', '', content)
                    content = re.sub(r'\n{3,}', '\n\n', content)
                
                outfile.write(content.strip())
                outfile.write("\n\n---\n\n")

            except Exception as e:
                print(f"Error processing {file.name}: {str(e)}")
                error_msg = f"*[Error reading this file: {str(e)}]*\n\n"
                outfile.write(error_msg)
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

    # Get a random cover image
    cover_images=("$COVER_IMAGES_DIR"/bing*.png)
    if [ ${#cover_images[@]} -gt 0 ]; then
        random_cover="${cover_images[RANDOM % ${#cover_images[@]}]}"
        echo "Using cover image: $random_cover"
        
        # Create EPUB with metadata and cover image
        echo "Creating EPUB with metadata..."
        pandoc "$WORKING_DIR/$OUTPUT_MD" \
            --metadata-file="$WORKING_DIR/metadata.yaml" \
            --epub-cover-image="$random_cover" \
            -o "$DIRECTORY/$OUTPUT_EPUB" \
            --toc --toc-depth=2
        
        echo "EPUB generated at: $DIRECTORY/$OUTPUT_EPUB"
    else
        echo "Warning: No cover images found in $COVER_IMAGES_DIR"
        pandoc "$WORKING_DIR/$OUTPUT_MD" \
            --metadata-file="$WORKING_DIR/metadata.yaml" \
            -o "$DIRECTORY/$OUTPUT_EPUB" \
            --toc --toc-depth=2
    fi

    # Clean up working directory
    rm -rf "$WORKING_DIR"
    echo "Working directory removed."
else
    echo "Pandoc not found. EPUB generation skipped."
    echo "Combined markdown file kept at: $WORKING_DIR/$OUTPUT_MD"
    echo "Working directory preserved at: $WORKING_DIR"
fi

echo "All operations completed!"