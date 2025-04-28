# WordListRubyTranslation.py

def process_files(en_file_path, de_file_path, output_file_path):
    try:
        # Read the English and German files
        with open(en_file_path, 'r', encoding='utf-8') as en_file:
            en_lines = en_file.readlines()
        
        with open(de_file_path, 'r', encoding='utf-8') as de_file:
            de_lines = de_file.readlines()
        
        # Prepare the output content
        output_content = []
        translated_words = []
        
        # Process each line pair
        for en_line, de_line in zip(en_lines, de_lines):
            # Skip headers
            if en_line.startswith('#') or de_line.startswith('#'):
                output_content.append(en_line)
                continue
            
            # Remove whitespace and split by comma
            en_words = en_line.split(',')
            de_words = de_line.split(',')
            
            # Process each word pair
            line_translations = []
            for en_word, de_word in zip(en_words, de_words):
                # Skip empty words
                if not en_word.strip() or not de_word.strip():
                    continue
                
                # Create ruby annotation
                ruby_annotation = f'<ruby>{de_word.strip()}<rt>{en_word.strip()}</rt></ruby>'
                line_translations.append(ruby_annotation)
                translated_words.append(ruby_annotation)
            
            # Add processed line to output
            if line_translations:
                output_content.append(', '.join(line_translations) + '\n')
        
        # Write to output file
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.writelines(output_content)
        
        print(f"Successfully processed {len(translated_words)} word pairs to {output_file_path}")
    
    except Exception as e:
        print(f"Error processing files: {str(e)}")

if __name__ == "__main__":
    # File paths
    en_file = '/home/zaya/Documents/Gitrepos/Linktrees/Languages/Grammar/WordList/WordList-en.md'
    de_file = '/home/zaya/Documents/Gitrepos/Linktrees/Languages/Grammar/WordList/WordList-de.md'
    output_file = '/home/zaya/Documents/Gitrepos/Linktrees/Languages/Grammar/WordList/RubyTranslation.md'
    
    # Process the files
    process_files(en_file, de_file, output_file)