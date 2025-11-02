import glob
import os
import re

from transliteration.epubMerge import merge_multiple_epubs


def prep_epubs_by_pattern(folder_path, file_patterns, merge_order=None, output_suffix="ml"):
    """
    Prepare EPUB files data based on file patterns and merge order
    
    Args:
        folder_path (str): Base folder path to search for files
        file_patterns (list): List of file patterns to match
        merge_order (list, optional): Order in which to merge languages. If None, uses file order.
        output_suffix (str): Suffix for output file (default: "ml")
    
    Returns:
        tuple: (epub_paths, output_path, languages, merge_order)
    """
    
    # Find all files matching the patterns
    epub_paths = []
    for pattern in file_patterns:
        full_pattern = os.path.join(folder_path, pattern)
        epub_paths.extend(glob.glob(full_pattern))
    
    if not epub_paths:
        raise ValueError(f"No files found matching patterns: {file_patterns} in {folder_path}")
    
    print(f"Found {len(epub_paths)} files:")
    for path in epub_paths:
        print(f"  - {path}")
    
    # Extract base name and languages from file paths
    file_info = []
    for path in epub_paths:
        filename = os.path.basename(path)
        # Extract language code (assuming pattern like *-db-*.epub)
        match = re.search(r'-db-([a-z]{2,3})\.epub$', filename)
        if match:
            lang = match.group(1)
            base_name = filename.replace(f'-db-{lang}.epub', '')
            file_info.append({
                'path': path,
                'lang': lang,
                'base_name': base_name
            })
        else:
            print(f"Warning: Could not extract language from filename: {filename}")
    
    # If no merge_order provided, use the natural file order
    if merge_order is None:
        merge_order = [info['lang'] for info in file_info]
        print(f"No merge_order provided, using natural order: {merge_order}")
    
    # Verify we have all required languages if merge_order is specified
    available_langs = {info['lang'] for info in file_info}
    missing_langs = set(merge_order) - available_langs
    if missing_langs:
        raise ValueError(f"Missing files for languages: {missing_langs}. Available: {available_langs}")
    
    # Sort files according to merge_order and get languages in correct order
    sorted_files = []
    sorted_languages = []
    for lang in merge_order:
        for info in file_info:
            if info['lang'] == lang:
                sorted_files.append(info)
                sorted_languages.append(lang)
                break
    
    # Generate output path
    if sorted_files:
        first_file = sorted_files[0]
        # Use the language codes as they appear in filenames (ch stays as ch)
        lang_string = '-'.join(sorted_languages)
        output_filename = f"{first_file['base_name']}-{output_suffix}-{lang_string}.epub"
        output_path = os.path.join(folder_path, output_filename)
        
        # Get the sorted epub paths
        epub_paths_sorted = [info['path'] for info in sorted_files]
        
        print(f"Prepared data:")
        print(f"  EPUB paths: {epub_paths_sorted}")
        print(f"  Output path: {output_path}")
        print(f"  Languages: {sorted_languages}")
        print(f"  Merge order: {merge_order}")
        
        return epub_paths_sorted, output_path, sorted_languages, merge_order
    else:
        raise ValueError("No files to merge after sorting.")

# Usage examples
if __name__ == "__main__":
    folder_path = '/home/zaya/Downloads/Zayas/ZayasBooks/Language/t'
    file_patterns = ['*-db-*.epub']
    
    # Example 1: With merge_order
    print("=== Example 1: With merge_order ===")
    try:
        epub_paths, output_path, languages, merge_order = prep_epubs_by_pattern(
            folder_path=folder_path,
            file_patterns=file_patterns,
            merge_order=['de', 'ru', 'ch'],  # Use 'ch' here
            output_suffix="ml"
        )
        merge_multiple_epubs(epub_paths, output_path, languages, merge_order)
    except ValueError as e:
        print(f"Error: {e}")
    
    # Example 2: Without merge_order (uses natural file order)
    # print("\n=== Example 2: Without merge_order ===")
    # try:
    #     epub_paths, output_path, languages, merge_order = prep_epubs_by_pattern(
    #         folder_path=folder_path,
    #         file_patterns=file_patterns,
    #         output_suffix="ml"
    #     )
    #     # merge_multiple_epubs(epub_paths, output_path, languages, merge_order)
    # except ValueError as e:
    #     print(f"Error: {e}")