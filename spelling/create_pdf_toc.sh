#!/bin/bash

# Output file
OUTPUT_FILE="Doutorado_Exames_Qualifications.pdf"
TOC_FILE="pdf_bookmarks.txt"
MERGE_LIST="pdf_list.txt"

echo "Creating PDF with accurate bookmarks and proper page numbering..."

# Function to count pages in a PDF file
count_pdf_pages() {
    local pdf_file="$1"
    if command -v pdfinfo >/dev/null 2>&1; then
        pdfinfo "$pdf_file" 2>/dev/null | grep Pages | awk '{print $2}'
    else
        # Fallback: use pdftk if available
        if command -v pdftk >/dev/null 2>&1; then
            pdftk "$pdf_file" dump_data 2>/dev/null | grep NumberOfPages | awk '{print $2}'
        else
            # Final fallback: estimate 1 page per PDF
            echo "1"
        fi
    fi
}

# Initialize variables
current_page=1
temp_dir=$(mktemp -d)

# Start building the bookmarks file for PDF
cat > "$TOC_FILE" << 'EOF'
BookmarkBegin
BookmarkTitle: Doutorado Exams Qualifications
BookmarkLevel: 1
BookmarkPageNumber: 1
EOF

# Process each directory
process_directory() {
    local dir="$1"
    local dir_name="$2"
    
    # Add main section bookmark
    cat >> "$TOC_FILE" << EOF
BookmarkBegin
BookmarkTitle: $dir_name
BookmarkLevel: 2
BookmarkPageNumber: $current_page
EOF
    
    # Process each PDF file in the directory
    for pdf_file in "$dir"/*.pdf; do
        if [[ -f "$pdf_file" ]]; then
            filename=$(basename "$pdf_file" .pdf)
            page_count=$(count_pdf_pages "$pdf_file")
            
            # Add individual file bookmark
            cat >> "$TOC_FILE" << EOF
BookmarkBegin
BookmarkTitle: $filename
BookmarkLevel: 3
BookmarkPageNumber: $current_page
EOF
            
            echo "File: $filename - Pages: $page_count - Starts at: $current_page"
            ((current_page += page_count))
            
            # Add to merge list
            echo "$pdf_file" >> "$MERGE_LIST"
        fi
    done
}

# Install required tools if not available
if ! command -v pdfinfo >/dev/null 2>&1; then
    echo "Installing poppler-utils for pdfinfo..."
    sudo apt update
    sudo apt install poppler-utils -y
fi

if ! command -v pdftk >/dev/null 2>&1; then
    echo "Installing pdftk for PDF manipulation..."
    sudo apt update
    sudo apt install pdftk -y
fi

# Check for alternative PDF tools
if ! command -v pdftk >/dev/null 2>&1 && ! command -v pdfunite >/dev/null 2>&1; then
    echo "Installing poppler-utils for pdfunite..."
    sudo apt update
    sudo apt install poppler-utils -y
fi

# Initialize merge list
> "$MERGE_LIST"

# Process each subject directory
echo "Processing directories and counting pages..."

process_directory "Algebraic" "Algebraic"
process_directory "Analysis" "Analysis" 
process_directory "Content" "Content"
process_directory "EDPs" "EDPs"
process_directory "Geometria" "Geometria"
process_directory "Numeric" "Numeric"
process_directory "Otimization" "Otimization"

echo "Bookmarks file created: $TOC_FILE"
echo "Total estimated pages: $((current_page - 1))"

echo "Now creating the combined PDF file..."

# Method 1: Using pdftk (preferred - supports bookmarks)
if command -v pdftk >/dev/null 2>&1; then
    echo "Merging PDFs with pdftk (with bookmarks support)..."
    
    # Create temporary merged PDF without bookmarks first
    pdftk $(cat "$MERGE_LIST") cat output temp_merged.pdf
    
    # Add bookmarks to the merged PDF
    pdftk temp_merged.pdf update_info "$TOC_FILE" output "$OUTPUT_FILE"
    
    rm -f temp_merged.pdf

# Method 2: Using pdfunite (fallback - no bookmark support)
elif command -v pdfunite >/dev/null 2>&1; then
    echo "Merging PDFs with pdfunite (bookmarks not supported)..."
    pdfunite $(cat "$MERGE_LIST") "$OUTPUT_FILE"
    echo "Warning: pdfunite does not support bookmarks. PDF will be created without table of contents."

# Method 3: Using ghostscript (fallback)
elif command -v gs >/dev/null 2>&1; then
    echo "Merging PDFs with ghostscript..."
    gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile="$OUTPUT_FILE" $(cat "$MERGE_LIST")
    echo "Warning: Ghostscript may not preserve bookmarks perfectly."

else
    echo "Error: No PDF merging tool found. Please install pdftk, pdfunite, or ghostscript."
    exit 1
fi

# Verify the PDF was created
if [[ -f "$OUTPUT_FILE" ]]; then
    echo "PDF created successfully: $OUTPUT_FILE"
    
    # Display PDF information
    if command -v pdfinfo >/dev/null 2>&1; then
        echo "PDF Information:"
        pdfinfo "$OUTPUT_FILE" | grep -E "Pages|File size"
    fi
    
    # For pdftk method, verify bookmarks were added
    if command -v pdftk >/dev/null 2>&1; then
        echo "Verifying bookmarks..."
        pdftk "$OUTPUT_FILE" dump_data | grep -A 3 -B 1 Bookmark | head -20
        echo "..."
    fi
    
else
    echo "Error: Failed to create $OUTPUT_FILE"
    exit 1
fi

# Cleanup
rm -rf "$temp_dir"
rm -f "$MERGE_LIST"

echo "Process completed! Final PDF: $OUTPUT_FILE"

# Display final instructions
echo ""
echo "=== IMPORTANT NOTES ==="
echo "1. For best bookmark support, use Adobe Acrobat Reader to view the PDF"
echo "2. If bookmarks don't appear, try:"
echo "   - View → Show/Hide → Navigation Panes → Bookmarks"
echo "   - Or look for the bookmark icon (usually looks like a ribbon or tag)"
echo "3. The PDF contains $(($(count_pdf_pages "$OUTPUT_FILE"))) total pages"