#!/bin/bash

# Directory where the files are located
directory="/home/zaya/Downloads/Zayas/zayascinema/trans/test"

# " First pass: Combine multiline subtitles under the same timestamp
#     " This matches timestamp lines followed by text lines until next timestamp or empty line
#     " Format: [number]\n[timestamp]\n[text lines...] and combines the text lines into one line per subtitle
#     g/^\d\+$\n\d\{2\}:\d\{2\}:\d\{2\},\d\{3\} --> \d\{2\}:\d\{2\}:\d\{2\},\d\{3\}/norm Vj:s/\n/ /ge

# Loop over each file in the directory
for file in "$directory"/*; do
    # Skip if not a regular file
    if [[ ! -f "$file" ]]; then
        continue
    fi

    echo "Processing file: $file"

    # Run NeoVim in headless mode and apply the necessary regex commands
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