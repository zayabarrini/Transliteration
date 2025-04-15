import os
import re


def format_filename(name):
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

def clean_filenames(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):  # Only process files, not directories
            formatted_name = format_filename(filename)
            if formatted_name != filename:
                new_path = os.path.join(directory, formatted_name)
                # Handle potential name conflicts
                if os.path.exists(new_path):
                    base, ext = os.path.splitext(formatted_name)
                    counter = 1
                    while os.path.exists(new_path):
                        new_path = os.path.join(directory, f"{base} ({counter}){ext}")
                        counter += 1
                os.rename(file_path, new_path)
                print(f'Renamed: "{filename}" -> "{os.path.basename(new_path)}"')
            else:
                print(f'Skipped: "{filename}" (already formatted)')

if __name__ == "__main__":
    # directory = input("Enter the directory containing files: ").strip()
    directory = "/home/zaya/Downloads/Workspace/Subtitles/Favorites4"
    if os.path.isdir(directory):
        clean_filenames(directory)
    else:
        print(f'Error: "{directory}" is not a valid directory.')