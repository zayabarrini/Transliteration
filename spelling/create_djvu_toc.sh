#!/bin/bash

# Check if directory is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory_with_pdf_folders>"
    echo "Example: $0 /path/to/pdf/folders"
    exit 1
fi

INPUT_DIR="$1"

# Verify input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory '$INPUT_DIR' does not exist."
    exit 1
fi

# Output file (use directory name for output)
DIR_BASENAME=$(basename "$INPUT_DIR")
OUTPUT_FILE="${DIR_BASENAME}_combined.djvu"
TOC_FILE="accurate_toc.dsed"
BOOKMARKS_FILE="bookmarks.bm"
TEMP_LIST="djvu_files.list"

echo "Processing directory: $INPUT_DIR"
echo "Output file: $OUTPUT_FILE"

# Function to count pages in a PDF file
count_pdf_pages() {
    local pdf_file="$1"
    if command -v pdfinfo >/dev/null 2>&1; then
        pdfinfo "$pdf_file" 2>/dev/null | grep Pages | awk '{print $2}'
    else
        # Fallback: estimate 1 page per PDF if pdfinfo not available
        echo "1"
    fi
}

# Function to count pages in a DjVu file
count_djvu_pages() {
    local djvu_file="$1"
    djvused "$djvu_file" -e 'n' 2>/dev/null || echo "1"
}

# Initialize variables
current_page=1
temp_dir=$(mktemp -d)

echo "Creating accurate TOC with proper page numbering..."

# Start building the BOOKMARKS file (separate from commands)
cat > "$BOOKMARKS_FILE" << 'EOF'
(bookmarks
EOF

# Process each subdirectory
process_directory() {
    local dir="$1"
    local dir_name=$(basename "$dir")
    
    echo "Processing directory: $dir_name"
    
    # Check if there are PDF files in this directory
    local pdf_count=$(find "$dir" -maxdepth 1 -name "*.pdf" | wc -l)
    if [ $pdf_count -eq 0 ]; then
        echo "  No PDF files found in $dir_name, skipping..."
        return
    fi
    
    echo "  (\"$dir_name\" \"#$current_page\")" >> "$BOOKMARKS_FILE"
    
    # Process each PDF file in the directory, sorted by name
    while IFS= read -r -d '' pdf_file; do
        if [[ -f "$pdf_file" ]]; then
            filename=$(basename "$pdf_file" .pdf)
            
            # Convert PDF to DjVu temporarily to get accurate page count
            temp_djvu="$temp_dir/$(basename "$pdf_file").djvu"
            echo "    Converting: $filename.pdf"
            pdf2djvu "$pdf_file" -o "$temp_djvu" 2>/dev/null
            
            if [[ -f "$temp_djvu" ]]; then
                page_count=$(count_djvu_pages "$temp_djvu")
                echo "    (\"$filename\" \"#$current_page\")" >> "$BOOKMARKS_FILE"
                echo "  File: $filename - Pages: $page_count - Starts at: $current_page"
                ((current_page += page_count))
                rm "$temp_djvu"
            else
                # Fallback if conversion fails
                echo "    (\"$filename\" \"#$current_page\")" >> "$BOOKMARKS_FILE"
                echo "  File: $filename - Estimated 1 page - Starts at: $current_page"
                ((current_page++))
            fi
        fi
    done < <(find "$dir" -maxdepth 1 -name "*.pdf" -type f -print0 | sort -z)
}

# Install required tools if not available
if ! command -v pdfinfo >/dev/null 2>&1; then
    echo "Installing poppler-utils for pdfinfo..."
    sudo apt update
    sudo apt install poppler-utils -y
fi

if ! command -v pdf2djvu >/dev/null 2>&1; then
    echo "Installing pdf2djvu..."
    sudo apt update
    sudo apt install pdf2djvu -y
fi

if ! command -v djvm >/dev/null 2>&1; then
    echo "Installing djvulibre-bin..."
    sudo apt update
    sudo apt install djvulibre-bin -y
fi

# Process each subdirectory
echo "Scanning for PDF directories..."
> "$TEMP_LIST"

# Find and process all subdirectories containing PDF files
while IFS= read -r -d '' subdir; do
    process_directory "$subdir"
done < <(find "$INPUT_DIR" -type d -print0 | sort -z)

# Close the BOOKMARKS structure
echo ")" >> "$BOOKMARKS_FILE"

# Create the TOC command file (this goes to djvused)
cat > "$TOC_FILE" << EOF
set-outline $BOOKMARKS_FILE
save
EOF

echo "Bookmarks file created: $BOOKMARKS_FILE"
echo "TOC command file created: $TOC_FILE"
echo "Total estimated pages: $((current_page - 1))"

echo "Now creating the combined DjVu file..."

# Convert all PDFs to individual DjVu files
echo "Converting PDFs to DjVu format..."
converted_count=0
while IFS= read -r -d '' pdf_file; do
    djvu_file="${pdf_file%.pdf}.djvu"
    echo "Converting: $(basename "$pdf_file")"
    if pdf2djvu "$pdf_file" -o "$djvu_file" 2>/dev/null; then
        echo "$djvu_file" >> "$TEMP_LIST"
        ((converted_count++))
    else
        echo "  Warning: Failed to convert $pdf_file"
    fi
done < <(find "$INPUT_DIR" -name "*.pdf" -type f -print0 | sort -z)

echo "Successfully converted $converted_count PDF files"

# Create the combined DjVu file
echo "Creating combined DjVu file..."
if [[ -s "$TEMP_LIST" ]]; then
    # Method 1: Use xargs with null-terminated strings
    if command -v xargs >/dev/null 2>&1; then
        cat "$TEMP_LIST" | tr '\n' '\0' | xargs -0 djvm -c "$OUTPUT_FILE"
    else
        # Method 2: Use while read loop
        djvm -c "$OUTPUT_FILE" $(cat "$TEMP_LIST")
    fi
else
    echo "Error: No DjVu files were created. Check if PDF files exist and are valid."
    exit 1
fi

# Check if the output file was created successfully
if [[ ! -f "$OUTPUT_FILE" ]]; then
    echo "Error: Failed to create combined DjVu file."
    echo "Trying alternative method..."
    
    # Alternative: create list file and use that
    if [[ -s "$TEMP_LIST" ]]; then
        djvm -c "$OUTPUT_FILE" -i "$TEMP_LIST"
    fi
fi

if [[ -f "$OUTPUT_FILE" ]]; then
    # Apply the accurate TOC
    echo "Applying TOC..."
    djvused "$OUTPUT_FILE" -f "$TOC_FILE"
    
    # Verify the TOC was applied
    echo "Verifying TOC..."
    djvused "$OUTPUT_FILE" -e 'print-outline'
    
    echo "Done! File created: $OUTPUT_FILE"
    
    # Display file information
    echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    if command -v djvused >/dev/null 2>&1; then
        page_count=$(djvused "$OUTPUT_FILE" -e 'n')
        echo "Total pages in final DjVu: $page_count"
    fi
else
    echo "Error: Could not create $OUTPUT_FILE"
    echo "Please check if PDF files exist and pdf2djvu is working."
    exit 1
fi

# Cleanup intermediate files
echo "Cleaning up intermediate files..."
while IFS= read -r -d '' djvu_file; do
    rm -f "$djvu_file"
done < <(find "$INPUT_DIR" -name "*.pdf.djvu" -type f -print0)

rm -f "$TEMP_LIST" "$TOC_FILE" "$BOOKMARKS_FILE"
rm -rf "$temp_dir"

echo "Process completed!"
echo "Final DjVu file: $OUTPUT_FILE"