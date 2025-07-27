import os
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

def combine_files(directory, output_filename="combined_notes.md"):
    """
    Combine all .md and .srt files in a directory into a single markdown file.
    Each file's content is preceded by its filename as a header.
    """
    # Get all .md and .srt files in the directory
    files = []
    for ext in ('*.md', '*.srt'):
        files.extend(Path(directory).glob(ext))
    
    if not files:
        print(f"No .md or .srt files found in {directory}")
        return
    
    # Sort files alphabetically
    files.sort()
    
    # Create the output file
    output_path = Path(directory) / output_filename
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for file in files:
            # Add filename as header (remove extension)
            header = f"# {file.stem}\n\n"
            outfile.write(header)
            
            try:
                # Read file content with appropriate encoding
                content = try_read_file(file)
                
                # For SRT files, add markdown code block formatting
                if file.suffix == '.srt':
                    outfile.write(content)
                    outfile.write("\n\n")
                else:  # MD files
                    outfile.write(content)
                    outfile.write("\n\n")
                
                print(f"Added: {file.name}")
            
            except UnicodeDecodeError as e:
                print(f"Error reading {file.name}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing {file.name}: {str(e)}")
                continue
    
    print(f"\nSuccessfully created combined file at:\n{output_path}")

if __name__ == "__main__":
    target_directory = "/home/zaya/Downloads/Workspace/Subtitles/TVSeries/HP"
    
    if os.path.isdir(target_directory):
        combine_files(target_directory)
    else:
        print(f"Error: {target_directory} is not a valid directory")