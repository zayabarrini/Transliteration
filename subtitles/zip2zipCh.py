import os
import re
import tempfile
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import chardet
from functools import lru_cache

# Add your project path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transliteration.translationFunctions import translate_text, transliterate, LANGUAGE_CODE_MAP
from transliteration.filter_language_characters import filter_language_characters

# Cache everything aggressively
@lru_cache(maxsize=10000)
def cached_translate_text(text, lang):
    """Cached translation with batch optimization"""
    return translate_text(text, lang)

@lru_cache(maxsize=10000)
def cached_transliterate(text, lang):
    """Cached transliteration"""
    filtered = filter_language_characters(text, target_language=LANGUAGE_CODE_MAP[lang])
    return transliterate(filtered, lang) if filtered else ""

def detect_encoding(file_path):
    """Fast encoding detection with small sample"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)  # Only read first 4KB for detection
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

def read_srt_fast(file_path):
    """Fast SRT reading with encoding detection"""
    encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.readlines()

def process_single_srt_zh_ch(srt_path):
    """Ultra-optimized processing for Chinese with transliteration"""
    print(f"Processing: {os.path.basename(srt_path)}")
    start_time = time.time()
    
    # Read file
    lines = read_srt_fast(srt_path)
    
    # Extract base name for output
    base_name = os.path.splitext(os.path.basename(srt_path))[0]
    temp_dir = tempfile.mkdtemp()
    output_srt = os.path.join(temp_dir, f"{base_name}_zh-ch.srt")
    
    # Process in one pass
    with open(output_srt, 'w', encoding='utf-8') as out_f:
        i = 0
        total_lines = len(lines)
        
        while i < total_lines:
            line = lines[i]
            stripped = line.strip()
            
            # Line number
            if stripped.isdigit():
                out_f.write(line)
                i += 1
                continue
            
            # Timestamp
            if i < total_lines and re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', stripped):
                out_f.write(line)
                i += 1
                continue
            
            # Text content (translate and transliterate)
            if stripped and not re.match(r'^\d', stripped):
                # Translate
                translated = cached_translate_text(stripped, 'zh-ch')
                out_f.write(line)  # Original line
                out_f.write(translated + '\n')  # Translated line
                
                # Transliterate
                transliterated = cached_transliterate(translated, 'zh-ch')
                if transliterated.strip():
                    out_f.write(transliterated + '\n')
            else:
                out_f.write(line)
            
            i += 1
    
    # Create individual zip
    zip_path = os.path.join(temp_dir, f"{base_name}_zh-ch.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(output_srt, arcname=os.path.basename(output_srt))
    
    # Cleanup temp files
    os.remove(output_srt)
    
    processing_time = time.time() - start_time
    print(f"Completed {os.path.basename(srt_path)} in {processing_time:.2f}s")
    
    return zip_path

def fast_process_zip_to_zh_ch(input_zip_path):
    """Process zip of SRTs to zip of Chinese-translated zips"""
    print(f"Starting processing: {input_zip_path}")
    overall_start = time.time()
    
    # Create output directory
    output_dir = os.path.dirname(input_zip_path)
    base_name = os.path.splitext(os.path.basename(input_zip_path))[0]
    final_zip_path = os.path.join(output_dir, f"{base_name}_zh-ch_collection.zip")
    
    # Extract all SRT files
    temp_extract_dir = tempfile.mkdtemp()
    srt_files = []
    
    with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)
        
        # Find all SRT files
        for root, _, files in os.walk(temp_extract_dir):
            for file in files:
                if file.lower().endswith('.srt'):
                    srt_files.append(os.path.join(root, file))
    
    if not srt_files:
        raise ValueError("No SRT files found in zip")
    
    print(f"Found {len(srt_files)} SRT files to process")
    
    # Process files in parallel with optimal workers
    max_workers = min(8, len(srt_files))  # Optimal for I/O bound tasks
    individual_zips = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_srt_zh_ch, srt_path): srt_path 
            for srt_path in srt_files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            try:
                zip_path = future.result()
                individual_zips.append(zip_path)
                print(f"✓ Completed: {os.path.basename(zip_path)}")
            except Exception as e:
                file_path = future_to_file[future]
                print(f"✗ Error processing {file_path}: {e}")
    
    # Create final collection zip
    print("Creating final collection zip...")
    with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as final_zip:
        for zip_file in individual_zips:
            final_zip.write(zip_file, arcname=os.path.basename(zip_file))
    
    # Cleanup
    print("Cleaning up temporary files...")
    for zip_file in individual_zips:
        try:
            os.remove(zip_file)
            os.rmdir(os.path.dirname(zip_file))  # Remove temp directory
        except:
            pass
    
    # Remove extracted files
    for srt_file in srt_files:
        try:
            os.remove(srt_file)
        except:
            pass
    try:
        os.rmdir(temp_extract_dir)
    except:
        pass
    
    total_time = time.time() - overall_start
    print(f"✅ Processing complete! Total time: {total_time:.2f}s")
    print(f"📦 Final output: {final_zip_path}")
    
    return final_zip_path

# Main execution
if __name__ == "__main__":
    input_zip_path = "/home/zaya/Downloads/Zayas/ZayasTransliteration/tests/all_subtitles/5.zip"
    
    final_zip = fast_process_zip_to_zh_ch(input_zip_path)
    print(f"🎉 Final collection created: {final_zip}")