import os
import re
from pathlib import Path

def format_filename(name):
    """Clean up filenames according to specified rules"""
    # Remove file extension
    name, ext = os.path.splitext(name)
    
    # Replace dots or underscores with spaces
    name = re.sub(r'[._]', ' ', name)
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Keep only the name and the year (if available)
    match = re.match(r'(.*?)(\s\d{4})', name)
    if match:
        name = match.group(1) + match.group(2)  # Name and year
    else:
        # Remove everything after the first non-alphabetic group
        name = re.sub(r'[^a-zA-Z0-9\s]+.*$', '', name)
    
    # Add the extension back
    return f"{name.strip()}{ext.lower()}"

def clean_filenames_in_folder(folder_path):
    """Rename all files in folder using format_filename"""
    for item in folder_path.iterdir():
        if item.is_file():
            new_name = format_filename(item.name)
            if new_name != item.name:
                new_path = item.with_name(new_name)
                # Handle name conflicts
                counter = 1
                while new_path.exists():
                    stem = new_path.stem.split('(')[0].strip()
                    new_path = new_path.with_name(f"{stem} ({counter}){new_path.suffix}")
                    counter += 1
                item.rename(new_path)
                print(f"  Renamed: {item.name} → {new_path.name}")

def combine_files_in_folder(folder_path):
    """
    Combine all .md and .srt files in a single folder into a markdown file.
    Uses the folder name as the output filename.
    """
    # Get all .md and .srt files in the directory
    files = []
    for ext in ('*.md', '*.srt'):
        files.extend(folder_path.glob(ext))
    
    if not files:
        print(f"No .md or .srt files found in {folder_path.name}")
        return None
    
    # Sort files alphabetically
    files.sort()
    
    # Create output filename from folder name
    output_filename = f"{folder_path.name}.md"
    output_path = folder_path / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for file in files:
                # Add filename as header (using cleaned name without extension)
                header = f"# {Path(format_filename(file.name)).stem}\n\n"
                outfile.write(header)
                
                # Read and write file content
                try:
                    with open(file, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                        # For SRT files
                        if file.suffix == '.srt':
                            outfile.write(content)
                        else:  # MD files
                            outfile.write(content)
                        outfile.write("\n\n")
                    
                    print(f"  Added: {file.name}")
                except UnicodeDecodeError:
                    # Try different encodings if UTF-8 fails
                    try:
                        with open(file, 'r', encoding='latin-1') as infile:
                            content = infile.read()
                            outfile.write(content)
                            outfile.write("\n\n")
                        print(f"  Added (latin-1): {file.name}")
                    except Exception as e:
                        print(f"  Error processing {file.name}: {str(e)}")
                        continue
                except Exception as e:
                    print(f"  Error processing {file.name}: {str(e)}")
                    continue
        
        print(f"  Created: {output_path.name}")
        return output_path
    except Exception as e:
        print(f"Error creating output file: {str(e)}")
        return None

def process_all_folders(root_directory):
    """
    Process all subfolders in the given directory:
    1. First clean filenames in each folder
    2. Then combine files in each folder
    """
    root_path = Path(root_directory)
    if not root_path.is_dir():
        print(f"Error: {root_directory} is not a valid directory")
        return
    
    print(f"\nProcessing all subfolders in: {root_path}")
    
    results = []
    for subfolder in sorted(root_path.iterdir()):
        if subfolder.is_dir():
            print(f"\nProcessing folder: {subfolder.name}")
            
            # Step 1: Clean filenames
            print("Cleaning filenames...")
            clean_filenames_in_folder(subfolder)
            
            # Step 2: Combine files
            print("Combining files...")
            result_path = combine_files_in_folder(subfolder)
            if result_path:
                results.append(result_path)
    
    if results:
        print("\nSuccessfully created combined files in:")
        for path in results:
            print(f"  - {path}")
    else:
        print("\nNo valid files found in any subfolders")

if __name__ == "__main__":
    # directory = input("Enter root directory containing movie folders: ").strip()
    directory = "/home/zaya/Downloads/Workspace/Subtitles/Horror"
    process_all_folders(directory)