import os
import re
from pathlib import Path

def extract_series_info(filename):
    """Extract series name and season/episode information from filename"""
    # Remove file extension
    name = Path(filename).stem
    
    # Pattern to match series name and episode info
    match = re.match(r'^(.+?)[ ._-]([Ss]\d+[Ee]\d+).*', name, re.IGNORECASE)
    if match:
        series_name = match.group(1).replace('.', ' ').replace('_', ' ')
        episode_info = match.group(2).upper()  # Format as S01E02
        
        # Clean up series name
        series_name = re.sub(r'[^a-zA-Z0-9\s]', '', series_name)
        series_name = re.sub(r'\s+', ' ', series_name).strip()
        
        return series_name, episode_info
    return None, None

def combine_subtitles(directory):
    """Combine all subtitle files into a single markdown file"""
    # Get all subtitle files
    subtitle_files = []
    for ext in ('*.srt', '*.sub', '*.txt', '*.md'):
        subtitle_files.extend(Path(directory).glob(ext))
    
    if not subtitle_files:
        print("No subtitle files found in directory")
        return
    
    # Determine series name from files
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
    
    # Create output filename
    output_filename = f"{series_name.replace(' ', '_')}_combined.md"
    output_path = Path(directory) / output_filename
    
    # Write combined file
    with open(output_path, 'w', encoding='utf-8') as outfile:
        # Write header
        outfile.write(f"# {series_name}\n\n")
        
        # Process files in episode order
        for episode in sorted(episodes.keys()):
            file = episodes[episode]
            
            # Write episode header
            outfile.write(f"## {episode}\n\n")
            
            # Write content
            with open(file, 'r', encoding='utf-8') as infile:
                content = infile.read()
                
                # Format SRT files as code blocks
                if file.suffix.lower() == '.srt':
                    outfile.write("```srt\n")
                    outfile.write(content)
                    outfile.write("\n```\n\n")
                else:
                    outfile.write(content)
                    outfile.write("\n\n")
            
            print(f"Added: {file.name} as {episode}")
    
    print(f"\nSuccessfully created combined subtitles at:\n{output_path}")

if __name__ == "__main__":
    # directory = input("Enter directory containing subtitle files: ").strip()
    directory = "/home/zaya/Downloads/Workspace/Subtitles/Glee"

    if os.path.isdir(directory):
        combine_subtitles(directory)
    else:
        print(f"Error: {directory} is not a valid directory")