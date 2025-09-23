import os
import sys
from pathlib import Path
from transliteration.epubSplit import process_epub  # Assuming your processing script is in epubSplit.py

def process_epub_folder(input_folder, output_folder=None):
    """Process all EPUBs in a folder, adding 's-' prefix to output files"""
    input_folder = Path(input_folder)
    
    # Use input_folder as output_folder if none specified
    output_folder = Path(output_folder) if output_folder else input_folder
    
    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    skipped_count = 0
    
    for epub_file in input_folder.glob('*.epub'):
        # Skip already processed files (those starting with 's-')
        if epub_file.name.endswith('-s'):
            skipped_count += 1
            continue
            
        output_path = output_folder / f"{epub_file.name.replace(".epub", "")}-s.epub"
        
        try:
            print(f"Processing: {epub_file.name} → {output_path.name}")
            process_epub(str(epub_file), str(output_path))
            processed_count += 1
        except Exception as e:
            print(f"Error processing {epub_file.name}: {str(e)}")
    
    print(f"\nProcessing complete!")
    print(f"Processed: {processed_count} files")
    print(f"Skipped: {skipped_count} files (already processed)")
    print(f"Output folder: {output_folder.resolve()}")

if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python process_folder.py input_folder [output_folder]")
    #     print("Note: Output filenames will get 's-' prefix")
    #     sys.exit(1)
    
    # input_folder = sys.argv[1]
    # output_folder = sys.argv[2] if len(sys.argv) > 2 else None
    # /home/zaya/Documents/Ebooks/Flow/Transliteration/Process
    input_folder = '/home/zaya/Downloads/Books/Theme/Literature/split/done/a'
    output_folder = '/home/zaya/Downloads/Books/Theme/Literature/split/done' 
    process_epub_folder(input_folder, output_folder)