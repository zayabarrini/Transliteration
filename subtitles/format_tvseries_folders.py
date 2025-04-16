import os
import re
from pathlib import Path

def detect_encoding(file_path):
    """Try to detect the file encoding"""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    return 'utf-8'  # fallback

def extract_series_info(filename):
    """Extract series name and season/episode information from filename"""
    name = Path(filename).stem
    # Enhanced pattern to match various episode formats
    patterns = [
        r'^(.+?)[ ._-]([Ss]\d+[Ee]\d+).*',  # S01E01
        r'^(.+?)[ ._-](\d+x\d+).*',         # 1x01
        r'^(.+?)[ ._-](\d{3}).*'            # 101 (S1E01)
    ]
    
    for pattern in patterns:
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            series_name = match.group(1).replace('.', ' ').replace('_', ' ')
            episode_info = match.group(2).upper()
            
            # Convert formats like 1x01 to S01E01
            if 'x' in episode_info:
                season, episode = episode_info.split('x')
                episode_info = f"S{int(season):02d}E{int(episode):02d}"
            elif len(episode_info) == 3 and episode_info.isdigit():  # 101 format
                episode_info = f"S{int(episode_info[0]):01d}E{int(episode_info[1:]):02d}"
            
            # Clean up series name
            series_name = re.sub(r'[^a-zA-Z0-9\s]', '', series_name)
            series_name = re.sub(r'\s+', ' ', series_name).strip()
            
            return series_name, episode_info
    return None, None

def process_subfolder(subfolder_path):
    """Process a single subfolder containing subtitle files"""
    subtitle_files = []
    for ext in ('*.srt', '*.sub', '*.txt', '*.md', '*.ass', '*.ssa'):
        subtitle_files.extend(subfolder_path.glob(ext))
    
    if not subtitle_files:
        print(f"\nNo subtitle files found in {subfolder_path.name}")
        return None
    
    series_name = None
    episodes = {}
    
    for file in subtitle_files:
        current_series, episode = extract_series_info(file.name)
        if current_series:
            if series_name is None:
                series_name = current_series
            if episode:  # Only add if we found episode info
                episodes[episode] = file
    
    if not series_name:
        series_name = subfolder_path.name
    
    output_filename = f"{series_name.replace(' ', '_')}.md"
    output_path = subfolder_path / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(f"# {series_name}\n\n")
            
            for episode in sorted(episodes.keys()):
                file = episodes[episode]
                outfile.write(f"## {episode}\n\n")
                
                encoding = detect_encoding(file)
                try:
                    with open(file, 'r', encoding=encoding) as infile:
                        content = infile.read()
                        
                        if file.suffix.lower() in ('.srt', '.ass', '.ssa', '.sub'):
                            # outfile.write(f"```{file.suffix[1:]}\n")
                            outfile.write(content)
                            outfile.write("\n\n")
                        else:
                            outfile.write(content)
                            outfile.write("\n\n")
                    
                    print(f"  Added: {file.name} as {episode}")
                except Exception as e:
                    print(f"  Error processing {file.name}: {str(e)}")
                    continue
        
        return output_path
    except Exception as e:
        print(f"Error creating output file: {str(e)}")
        return None

def process_all_folders(root_directory):
    """Process all subfolders in the given directory"""
    root_path = Path(root_directory)
    if not root_path.is_dir():
        print(f"Error: {root_directory} is not a valid directory")
        return
    
    print(f"\nProcessing all subfolders in: {root_path}")
    
    results = []
    for subfolder in sorted(root_path.iterdir()):
        if subfolder.is_dir():
            print(f"\nProcessing folder: {subfolder.name}")
            result_path = process_subfolder(subfolder)
            if result_path:
                results.append(result_path)
    
    if results:
        print("\nSuccessfully created combined files for:")
        for path in results:
            print(f"  - {path}")
    else:
        print("\nNo valid subtitle files found in any subfolders")

if __name__ == "__main__":
    # directory = input("Enter root directory containing TV series folders: ").strip()
    directory = "/home/zaya/Downloads/Workspace/Subtitles/Horror"

    process_all_folders(directory)