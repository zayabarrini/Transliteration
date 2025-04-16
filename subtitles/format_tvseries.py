import os
import re
from pathlib import Path

def detect_encoding(file_path):
    """Try to detect the file encoding"""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
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
    match = re.match(r'^(.+?)[ ._-]([Ss]\d+[Ee]\d+).*', name, re.IGNORECASE)
    if match:
        series_name = match.group(1).replace('.', ' ').replace('_', ' ')
        episode_info = match.group(2).upper()
        series_name = re.sub(r'[^a-zA-Z0-9\s]', '', series_name)
        series_name = re.sub(r'\s+', ' ', series_name).strip()
        return series_name, episode_info
    return None, None

def combine_subtitles(directory):
    """Combine all subtitle files into a single markdown file"""
    subtitle_files = []
    for ext in ('*.srt', '*.sub', '*.txt', '*.md'):
        subtitle_files.extend(Path(directory).glob(ext))
    
    if not subtitle_files:
        print("No subtitle files found in directory")
        return
    
    series_name = None
    episodes = {}
    
    for file in subtitle_files:
        current_series, episode = extract_series_info(file.name)
        if current_series:
            if series_name is None:
                series_name = current_series
            episodes[episode] = file
    
    if not series_name:
        series_name = "Combined_Subtitles"
    
    output_filename = f"{series_name.replace(' ', '_')}.md"
    output_path = Path(directory) / output_filename
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# {series_name}\n\n")
        
        for episode in sorted(episodes.keys()):
            file = episodes[episode]
            outfile.write(f"## {episode}\n\n")
            
            encoding = detect_encoding(file)
            try:
                with open(file, 'r', encoding=encoding) as infile:
                    content = infile.read()
                    
                    if file.suffix.lower() == '.srt':
                        # outfile.write("```srt\n")
                        outfile.write(content)
                        # outfile.write("\n```\n\n")
                        outfile.write("\n\n")
                    else:
                        outfile.write(content)
                        outfile.write("\n\n")
                
                print(f"Added: {file.name} as {episode} (encoding: {encoding})")
            except Exception as e:
                print(f"Error processing {file.name}: {str(e)}")
                continue
    
    print(f"\nSuccessfully created combined subtitles at:\n{output_path}")

if __name__ == "__main__":
    # directory = input("Enter directory containing subtitle files: ").strip()
    directory = "/home/zaya/Downloads/Workspace/Subtitles/The-Wire"

    if os.path.isdir(directory):
        combine_subtitles(directory)
    else:
        print(f"Error: {directory} is not a valid directory")