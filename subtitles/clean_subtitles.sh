#!/bin/bash

# Directory where the files are located
# directory="${1:-.}"
directory="/home/zaya/Downloads/Workspace/Subtitles/Glee"

# Loop over each file in the directory
for file in "$directory"/*; do
  # Skip if not a regular file
  if [[ ! -f "$file" ]]; then
    continue
  fi

  echo "Processing file: $file"

  # Run NeoVim in headless mode and apply the necessary regex commands
  nvim -es "$file" <<EOF
    " Step 1: Remove timestamps in the format of '00:01:30,556 --> 00:01:33,524'
    g/^\d\+\n\d\{2\}:\d\{2\}:\d\{2\},\d\{3\} --> \d\{2\}:\d\{2\}:\d\{2\},\d\{3\}/d2
    
    " Remove weird Characters: 
    %s/<\/\?i>//g

    " Step 3: Delete all empty lines
    g/^$/d
    
    " Remove unwanted space at the begining:
    %s/^\s\+//

    " Step 2: Join lines if the next line starts with a lowercase letter    
    %s/\n\(\l\)/ \1/g

    " Save the changes and exit
    wq
EOF

done

