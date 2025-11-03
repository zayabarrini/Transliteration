import glob
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup


def merge_multiple_epubs_simple(epub_paths: List[str], output_path: str, languages: List[str], merge_order: List[str] = None):
    """
    Simple EPUB merger that stacks EPUBs one after another.
    Organizes TOC with languages as main headers and chapters nested inside.
    """
    
    if len(epub_paths) != len(languages):
        raise ValueError("Number of EPUB paths must match number of languages")
    
    if merge_order is None:
        merge_order = languages
    else:
        for lang in merge_order:
            if lang not in languages:
                raise ValueError(f"Language {lang} in merge_order not found in provided languages")
    
    print(f"Simple merging {len(epub_paths)} EPUBs in order: {merge_order}")
    
    # Create temporary directories for extraction
    temp_dirs = []
    try:
        # Extract all EPUBs and organize by merge order
        epub_data = {}
        sorted_epubs = []
        sorted_languages = []
        
        # Sort EPUBs according to merge_order
        for lang in merge_order:
            idx = languages.index(lang)
            sorted_epubs.append(epub_paths[idx])
            sorted_languages.append(lang)
        
        # Extract sorted EPUBs
        for i, (epub_path, lang) in enumerate(zip(sorted_epubs, sorted_languages)):
            temp_dir = tempfile.mkdtemp()
            temp_dirs.append(temp_dir)
            
            print(f"Extracting {lang} EPUB: {os.path.basename(epub_path)}")
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            epub_data[lang] = {
                'path': temp_dir,
                'index': i
            }
        
        # Create merged directory using first EPUB as base
        merged_dir = tempfile.mkdtemp()
        temp_dirs.append(merged_dir)
        base_lang = sorted_languages[0]
        shutil.copytree(epub_data[base_lang]['path'], merged_dir, dirs_exist_ok=True)
        
        # Merge content and update TOC/Spine
        merge_content_simple(epub_data, merged_dir, sorted_languages)
        
        # Create final EPUB
        print("Creating simple merged multilingual EPUB...")
        create_epub_from_folder(merged_dir, output_path)
        print(f"Successfully created simple merged EPUB: {output_path}")
        
    finally:
        # Cleanup temporary directories
        for temp_dir in temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)

def merge_content_simple(epub_data: Dict, merged_dir: str, languages: List[str]):
    """
    Merge content by stacking EPUBs and organizing TOC with language headers.
    """
    
    # Find all HTML files in each EPUB and organize them
    all_html_files = {}
    for lang, data in epub_data.items():
        html_files = []
        for root, dirs, files in os.walk(data['path']):
            for file in files:
                if file.lower().endswith(('.html', '.htm', '.xhtml')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, data['path'])
                    html_files.append((full_path, rel_path))
        
        # Sort HTML files to maintain reading order
        html_files.sort(key=lambda x: x[1])
        all_html_files[lang] = html_files
    
    # Copy all HTML files to merged directory with language prefixes
    copied_files = {}
    for lang in languages:
        lang_files = []
        for source_path, rel_path in all_html_files[lang]:
            # Create new filename with language prefix
            filename = os.path.basename(rel_path)
            dir_part = os.path.dirname(rel_path)
            new_filename = f"{lang}_{filename}"
            new_rel_path = os.path.join(dir_part, new_filename) if dir_part != '.' else new_filename
            new_full_path = os.path.join(merged_dir, new_rel_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Copy and update the file
            update_html_file_with_lang(source_path, new_full_path, lang)
            lang_files.append(new_rel_path)
        
        copied_files[lang] = lang_files
    
    # Update the OPF file to include all new files and organize spine
    update_opf_file_simple(merged_dir, copied_files, languages)
    
    # Update TOC files (both NCX and HTML)
    update_toc_files(merged_dir, copied_files, languages)

def update_html_file_with_lang(source_path: str, dest_path: str, lang: str):
    """Copy HTML file and add language attribute to body tag if not present."""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse and add lang attribute to body if not present
        is_xml = source_path.endswith('.xhtml')
        soup = BeautifulSoup(content, 'xml' if is_xml else 'html.parser')
        body = soup.find('body')
        if body and not body.get('lang'):
            body['lang'] = lang
            body['dir'] = 'auto'
        
        # Write updated content
        with open(dest_path, 'w', encoding='utf-8') as f:
            if is_xml:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(str(soup))
            else:
                f.write(soup.prettify())
    except Exception as e:
        print(f"Warning: Could not update HTML file {source_path}: {e}")
        # Fallback: simple copy
        shutil.copy2(source_path, dest_path)

def update_opf_file_simple(merged_dir: str, copied_files: Dict, languages: List[str]):
    """Update the OPF package file to include all files and organize spine."""
    
    # Find OPF file
    opf_files = []
    for root, dirs, files in os.walk(merged_dir):
        for file in files:
            if file.endswith('.opf'):
                opf_files.append(os.path.join(root, file))
    
    if not opf_files:
        print("Warning: No OPF file found")
        return
    
    opf_path = opf_files[0]
    print(f"Updating OPF file: {opf_path}")
    
    try:
        # Parse OPF file
        with open(opf_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'xml')
        
        # Get or create manifest and spine
        manifest = soup.find('manifest')
        spine = soup.find('spine')
        
        if not manifest or not spine:
            print("Warning: Invalid OPF structure - missing manifest or spine")
            return
        
        # Clear existing spine (we'll rebuild it)
        for itemref in spine.find_all('itemref'):
            itemref.decompose()
        
        # Remove existing HTML files from manifest to avoid duplicates
        existing_items = manifest.find_all('item')
        for item in existing_items:
            href = item.get('href', '')
            if href and any(href.endswith(ext) for ext in ['.html', '.htm', '.xhtml']):
                item.decompose()
        
        # Add all files to manifest and spine in language order
        item_id_counter = 1
        for lang in languages:
            for file_path in copied_files[lang]:
                # Create manifest item
                item_id = f"item_{item_id_counter:04d}"
                item_id_counter += 1
                
                # Determine media type
                if file_path.endswith('.xhtml'):
                    media_type = 'application/xhtml+xml'
                else:
                    media_type = 'application/xhtml+xml'
                
                # Add to manifest
                item = soup.new_tag('item')
                item['id'] = item_id
                item['href'] = file_path
                item['media-type'] = media_type
                manifest.append(item)
                
                # Add to spine
                itemref = soup.new_tag('itemref')
                itemref['idref'] = item_id
                spine.append(itemref)
        
        # Write updated OPF
        with open(opf_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print("Successfully updated OPF file")
        
    except Exception as e:
        print(f"Error updating OPF file: {e}")

def update_toc_files(merged_dir: str, copied_files: Dict, languages: List[str]):
    """Update both NCX and HTML TOC files."""
    update_ncx_toc_simple(merged_dir, copied_files, languages)
    update_html_toc_simple(merged_dir, copied_files, languages)

def update_ncx_toc_simple(merged_dir: str, copied_files: Dict, languages: List[str]):
    """Update NCX TOC to organize by languages with chapters nested inside."""
    
    # Find NCX file
    ncx_files = []
    for root, dirs, files in os.walk(merged_dir):
        for file in files:
            if file.endswith('.ncx'):
                ncx_files.append(os.path.join(root, file))
    
    if not ncx_files:
        print("Warning: No NCX file found")
        return
    
    ncx_path = ncx_files[0]
    print(f"Updating NCX TOC: {ncx_path}")
    
    try:
        # Parse NCX file
        with open(ncx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'xml')
        
        # Find or create navMap
        nav_map = soup.find('navmap')
        if not nav_map:
            # Try to find the navMap in different namespaces
            nav_map = soup.find('navMap') or soup.find('ncx:navmap')
            if not nav_map:
                # Create new navMap if it doesn't exist
                ncx = soup.find('ncx') or soup.find('ncx:ncx')
                if ncx:
                    nav_map = soup.new_tag('navMap')
                    ncx.append(nav_map)
                else:
                    print("Warning: Could not find or create navMap in NCX")
                    return
        
        # Clear existing navMap content
        for child in nav_map.find_all(recursive=False):
            child.decompose()
        
        # Build new TOC structure with language headers
        play_order = 1
        
        for lang_idx, lang in enumerate(languages):
            # Create language-level navPoint
            lang_navpoint = soup.new_tag('navPoint')
            lang_navpoint['id'] = f'navpoint-lang-{lang}'
            lang_navpoint['playOrder'] = str(play_order)
            play_order += 1
            
            # Language label
            nav_label = soup.new_tag('navLabel')
            text = soup.new_tag('text')
            text.string = f"Language: {lang.upper()}"
            nav_label.append(text)
            
            # Language content (first file of this language)
            content = soup.new_tag('content')
            content['src'] = copied_files[lang][0]
            
            # Assemble language navpoint
            lang_navpoint.append(nav_label)
            lang_navpoint.append(content)
            
            # Add chapter navpoints for this language
            for file_idx, file_path in enumerate(copied_files[lang]):
                chapter_navpoint = soup.new_tag('navPoint')
                chapter_navpoint['id'] = f'navpoint-{lang}-{file_idx}'
                chapter_navpoint['playOrder'] = str(play_order)
                play_order += 1
                
                # Chapter label
                chapter_nav_label = soup.new_tag('navLabel')
                chapter_text = soup.new_tag('text')
                chapter_text.string = f"Chapter {file_idx + 1}"
                chapter_nav_label.append(chapter_text)
                
                # Chapter content
                chapter_content = soup.new_tag('content')
                chapter_content['src'] = file_path
                
                chapter_navpoint.append(chapter_nav_label)
                chapter_navpoint.append(chapter_content)
                
                lang_navpoint.append(chapter_navpoint)
            
            nav_map.append(lang_navpoint)
        
        # Write updated NCX
        with open(ncx_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print("Successfully updated NCX TOC")
        
    except Exception as e:
        print(f"Error updating NCX TOC: {e}")

def update_html_toc_simple(merged_dir: str, copied_files: Dict, languages: List[str]):
    """Update HTML TOC/Nav file if it exists (for EPUB3)."""
    
    # Find HTML TOC files (common patterns)
    toc_patterns = ['toc.xhtml', 'nav.xhtml', 'toc.html', 'nav.html', '*.xhtml', '*.html']
    toc_path = None
    
    for pattern in toc_patterns:
        matches = glob.glob(os.path.join(merged_dir, '**', pattern), recursive=True)
        for match in matches:
            # Check if this file contains TOC structure
            with open(match, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'toc' in content.lower() or 'nav' in content.lower() or 'epub:type="toc"' in content:
                    toc_path = match
                    break
        if toc_path:
            break
    
    if not toc_path:
        print("Warning: No HTML TOC file found")
        return
    
    print(f"Updating HTML TOC: {toc_path}")
    
    try:
        # Parse HTML TOC
        with open(toc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        is_xml = toc_path.endswith('.xhtml')
        soup = BeautifulSoup(content, 'xml' if is_xml else 'html.parser')
        
        # Find nav element with epub:type="toc"
        nav = None
        for elem in soup.find_all('nav'):
            if elem.get('epub:type') == 'toc' or 'toc' in elem.get('class', []):
                nav = elem
                break
        
        # If no specific nav found, look for any ol/ul that might be TOC
        if not nav:
            nav = soup.find('ol') or soup.find('ul')
            if nav and (nav.find('a') or nav.find('link')):
                # This looks like a TOC
                pass
            else:
                nav = None
        
        if not nav:
            print("Warning: Could not find TOC structure in HTML file")
            return
        
        # Clear existing TOC content
        nav.clear()
        
        # Build new TOC structure
        for lang in languages:
            # Create language section
            lang_li = soup.new_tag('li')
            
            lang_link = soup.new_tag('a', href=copied_files[lang][0])
            lang_link.string = f"Language: {lang.upper()}"
            lang_li.append(lang_link)
            
            # Create nested list for chapters
            chapter_ol = soup.new_tag('ol')
            
            for file_idx, file_path in enumerate(copied_files[lang]):
                chapter_li = soup.new_tag('li')
                chapter_link = soup.new_tag('a', href=file_path)
                chapter_link.string = f"Chapter {file_idx + 1}"
                
                chapter_li.append(chapter_link)
                chapter_ol.append(chapter_li)
            
            lang_li.append(chapter_ol)
            nav.append(lang_li)
        
        # Write updated HTML TOC
        with open(toc_path, 'w', encoding='utf-8') as f:
            if is_xml:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(str(soup))
            else:
                f.write(soup.prettify())
        print("Successfully updated HTML TOC")
        
    except Exception as e:
        print(f"Error updating HTML TOC: {e}")

def create_epub_from_folder(folder_path: str, output_path: str):
    """Create EPUB file from folder contents with proper mimetype handling."""
    # Ensure mimetype exists and is correct
    mimetype_path = os.path.join(folder_path, "mimetype")
    if not os.path.exists(mimetype_path):
        with open(mimetype_path, 'w') as f:
            f.write("application/epub+zip")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add mimetype first and uncompressed (EPUB requirement)
        if os.path.exists(mimetype_path):
            zipf.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # Add all other files
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file == "mimetype":
                    continue  # Already added
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def prep_and_merge_simple(folder_path, file_patterns, merge_order=None, output_suffix="ml-simple"):
    """
    Prepare EPUB files and merge using simple stacking approach.
    """
    from transliteration.epubMergeFolder import prep_epubs_by_pattern
    
    epub_paths, output_path, languages, merge_order = prep_epubs_by_pattern(
        folder_path=folder_path,
        file_patterns=file_patterns,
        merge_order=merge_order,
        output_suffix=output_suffix
    )
    
    merge_multiple_epubs_simple(epub_paths, output_path, languages, merge_order)

# Usage example
if __name__ == "__main__":
    folder_path = '/home/zaya/Downloads/Zayas/ZayasBooks/Language/t'
    file_patterns = ['*-db-*.epub']
    
    # Example with simple merging
    print("=== Simple Merging Example ===")
    try:
        prep_and_merge_simple(
            folder_path=folder_path,
            file_patterns=file_patterns,
            merge_order=['ar','ch','de','es','fr','el','he','hi','id','it','ja','ko','la','pl','pt','ru','sw','tr'],
            output_suffix="ml-simple"
        )
    except ValueError as e:
        print(f"Error: {e}")