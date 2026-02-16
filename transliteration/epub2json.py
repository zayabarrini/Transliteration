import json
import os
import re
from collections import OrderedDict
from pathlib import Path
from zipfile import ZipFile

from bs4 import BeautifulSoup


class EpubToJsonConverter:
    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.sections = OrderedDict()  # Use OrderedDict to maintain order
        
    def extract_epub_content(self):
        """Extract and parse EPUB content from split files"""
        with ZipFile(self.epub_path, 'r') as zip_ref:
            # Find all split XHTML files in text directory
            split_files = []
            for file in zip_ref.namelist():
                if file.startswith('EPUB/text/ch') and file.endswith('.xhtml'):
                    split_files.append(file)
            
            # Sort files to maintain chapter order
            split_files.sort()
            
            # Process each split file
            for split_file in split_files:
                print(f"Processing: {split_file}")
                with zip_ref.open(split_file) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    self._process_split_file(soup, split_file)
    
    def _process_split_file(self, soup, filename):
        """Process a single split file containing one section"""
        # Find the section
        section = soup.find('section')
        if not section:
            return
        
        # Get section ID
        section_id = section.get('id', Path(filename).stem)
        
        # Initialize section data
        section_data = {
            'section_id': section_id,
            'filename': filename,
            'paragraphs': [],
            'title': None
        }
        
        # Check if first element is a title (h1 with Chinese)
        title = section.find('h1', attrs={'lang': 'zh'})
        if title:
            title_data = self._process_paragraph_or_title(title, is_title=True)
            section_data['title'] = title_data
        
        # Find all paragraphs in order
        current_english = None
        for element in section.children:
            if element.name == 'p':
                # Check if it's English or Chinese
                if element.get('lang') == 'zh':
                    # This is a Chinese paragraph
                    if current_english:
                        # Pair with previous English
                        para_data = self._process_paragraph_pair(current_english, element)
                        section_data['paragraphs'].append(para_data)
                        current_english = None
                    else:
                        # Chinese without preceding English (maybe standalone)
                        para_data = self._process_paragraph_pair(None, element)
                        section_data['paragraphs'].append(para_data)
                else:
                    # This is an English paragraph, store it for next Chinese
                    current_english = element
        
        self.sections[section_id] = section_data
    
    def _process_paragraph_pair(self, english_para, chinese_para):
        """Process a pair of English and Chinese paragraphs"""
        # Extract English text
        english_text = english_para.get_text().strip() if english_para else ""
        
        # Find the chinese-dual-display div in Chinese paragraph
        dual_display = chinese_para.find('div', class_='chinese-dual-display')
        if not dual_display:
            return None
        
        # Extract clean version (original Chinese text)
        clean_version = dual_display.find('div', class_='clean-version')
        original_text = clean_version.get_text().strip() if clean_version else ""
        
        # Extract transliterated version HTML
        transliterated_div = dual_display.find('div', class_='transliterated-version')
        transliterated_html = str(transliterated_div) if transliterated_div else ""
        
        # Extract ruby annotations
        ruby_annotations = []
        if transliterated_div:
            for element in transliterated_div.children:
                if element.name == 'ruby':
                    annotation = self._parse_ruby_element(element)
                    ruby_annotations.append(annotation)
                elif element.name == 'span' and element.get('class') and 'punctuation-token' in element.get('class', []):
                    ruby_annotations.append({
                        'type': 'punctuation',
                        'content': element.get_text(),
                        'html': str(element)
                    })
        
        return {
            'english': english_text,
            'chinese': original_text,
            'transliterated_html': transliterated_html,
            'ruby_annotations': ruby_annotations,
            'full_html': str(dual_display)
        }
    
    def _process_paragraph_or_title(self, element, is_title=False):
        """Process a title element (h1 with Chinese)"""
        dual_display = element.find('div', class_='chinese-dual-display')
        if not dual_display:
            return None
        
        clean_version = dual_display.find('div', class_='clean-version')
        original_text = clean_version.get_text().strip() if clean_version else ""
        
        transliterated_div = dual_display.find('div', class_='transliterated-version')
        
        ruby_annotations = []
        if transliterated_div:
            for element in transliterated_div.children:
                if element.name == 'ruby':
                    annotation = self._parse_ruby_element(element)
                    ruby_annotations.append(annotation)
                elif element.name == 'span' and 'punctuation-token' in element.get('class', []):
                    ruby_annotations.append({
                        'type': 'punctuation',
                        'content': element.get_text(),
                        'html': str(element)
                    })
        
        return {
            'type': 'title' if is_title else 'paragraph',
            'chinese': original_text,
            'transliterated_html': str(transliterated_div) if transliterated_div else "",
            'ruby_annotations': ruby_annotations,
            'full_html': str(dual_display)
        }
    
    def _parse_ruby_element(self, ruby):
        """Parse ruby element into structured data"""
        result = {
            'type': 'ruby',
            'syntax': '',
            'grammatical_class': '',
            'word': '',
            'pinyin': '',
            'html': str(ruby)
        }
        
        # Extract syntax from class
        classes = ruby.get('class', [])
        for cls in classes:
            if cls != 'chinese':
                result['syntax'] = cls
        
        # Find grammatical class (if present)
        gram_class = ruby.find('span', class_='grammatical-class')
        if gram_class:
            result['grammatical_class'] = gram_class.get_text()
        
        # Find syntax label (fallback for color-coded mode)
        syntax_label = ruby.find('span', class_='syntax-label')
        if syntax_label and not result['grammatical_class']:
            result['syntax'] = syntax_label.get_text()
        
        # Find word token
        word_token = ruby.find('span', class_='word-token')
        if word_token:
            result['word'] = word_token.get_text()
        
        # Find pinyin
        pinyin = ruby.find('rt', class_='pinyin')
        if pinyin:
            result['pinyin'] = pinyin.get_text()
        
        return result
    
    def convert_to_json(self, output_path, pretty_print=True):
        """Convert extracted content to JSON"""
        output = {
            'metadata': {
                'source_epub': os.path.basename(self.epub_path),
                'total_sections': len(self.sections),
                'version': '1.0'
            },
            'sections': list(self.sections.values())
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty_print:
                json.dump(output, f, ensure_ascii=False, indent=2)
            else:
                json.dump(output, f, ensure_ascii=False)
        
        return output_path
    
    def create_web_optimized_json(self, output_path):
        """Create a web-optimized version with simplified structure"""
        web_optimized = []
        
        for section_id, section in self.sections.items():
            web_section = {
                'id': section_id,
                'filename': section['filename'],
                'title': None,
                'paragraphs': []
            }
            
            # Add title if exists
            if section.get('title'):
                web_section['title'] = {
                    'zh': section['title']['chinese'],
                    'annotations': self._simplify_annotations(section['title']['ruby_annotations'])
                }
            
            # Add paragraphs
            for para in section['paragraphs']:
                if para:  # Skip None paragraphs
                    web_para = {
                        'en': para['english'],
                        'zh': para['chinese'],
                        'annotations': self._simplify_annotations(para['ruby_annotations'])
                    }
                    web_section['paragraphs'].append(web_para)
            
            web_optimized.append(web_section)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(web_optimized, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def _simplify_annotations(self, ruby_annotations):
        """Simplify ruby annotations for web use"""
        simplified = []
        for ann in ruby_annotations:
            if ann['type'] == 'ruby':
                simplified.append({
                    'word': ann['word'],
                    'pinyin': ann['pinyin'],
                    'syntax': ann['syntax'],
                    'grammatical_class': ann['grammatical_class']
                })
            else:  # punctuation
                simplified.append({
                    'type': 'punct',
                    'content': ann['content']
                })
        return simplified
    
    def create_flat_paragraph_list(self, output_path):
        """Create a flat list of all paragraph pairs for easy navigation"""
        flat_list = []
        pair_id = 0
        
        for section_id, section in self.sections.items():
            for para in section['paragraphs']:
                if para:
                    flat_list.append({
                        'id': pair_id,
                        'section_id': section_id,
                        # 'filename': section['filename'],
                        # 'en': para['english'],
                        # 'zh': para['chinese'],
                        # 'annotations': self._simplify_annotations(para['ruby_annotations']),
                        'html': para['full_html']
                    })
                    pair_id += 1
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(flat_list, f, ensure_ascii=False, indent=2)
        
        return output_path

# Usage example
def process_epub_for_web(epub_file_path, output_dir):
    """Main function to process EPUB and generate JSON files"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize converter
    converter = EpubToJsonConverter(epub_file_path)
    
    # Extract content
    print("Extracting EPUB content...")
    converter.extract_epub_content()
    
    # Generate full JSON (with all details)
    full_json_path = os.path.join(output_dir, 'epub_content_full.json')
    converter.convert_to_json(full_json_path)
    print(f"Full JSON saved to: {full_json_path}")
    
    # Generate web-optimized JSON
    web_json_path = os.path.join(output_dir, 'epub_content_web.json')
    converter.create_web_optimized_json(web_json_path)
    print(f"Web-optimized JSON saved to: {web_json_path}")
    
    # Generate flat paragraph list (for easy navigation/display)
    flat_json_path = os.path.join(output_dir, 'epub_paragraphs_flat.json')
    converter.create_flat_paragraph_list(flat_json_path)
    print(f"Flat paragraph list saved to: {flat_json_path}")
    
    return {
        # 'full_json': full_json_path,
        'web_json': web_json_path,
        # 'flat_json': flat_json_path
    }

# Web display component (JavaScript)
WEB_COMPONENT = """
// Web display component for the bilingual content
class BilingualDisplay {
    constructor(containerId, data) {
        this.container = document.getElementById(containerId);
        this.data = data;
        this.currentSection = 0;
        this.currentParagraph = 0;
    }
    
    renderCurrent() {
        const section = this.data[this.currentSection];
        if (!section) return;
        
        const para = section.paragraphs[this.currentParagraph];
        if (!para) return;
        
        let html = `
            <div class="bilingual-section">
                <div class="section-header">
                    <span class="section-id">${section.id}</span>
                    <span class="position">${this.currentParagraph + 1}/${section.paragraphs.length}</span>
                </div>
        `;
        
        // Add title if exists and we're at first paragraph
        if (this.currentParagraph === 0 && section.title) {
            html += `
                <div class="section-title">
                    <div class="chinese-title">${section.title.zh}</div>
                </div>
            `;
        }
        
        html += `
                <div class="paragraph-card">
                    <div class="english-text">${para.en}</div>
                    <div class="chinese-text">${para.zh}</div>
                    <div class="annotations">
        `;
        
        // Build annotated version
        let annotatedHtml = '';
        para.annotations.forEach(ann => {
            if (ann.type === 'punct') {
                annotatedHtml += ann.content;
            } else {
                annotatedHtml += `
                    <ruby class="chinese ${ann.syntax}">
                        <span class="grammatical-class">${ann.grammatical_class || ''}</span>
                        <span class="word-token ${ann.syntax}">${ann.word}</span>
                        <rt class="pinyin">${ann.pinyin}</rt>
                    </ruby>
                `;
            }
        });
        
        html += annotatedHtml + '</div></div>';
        
        // Add navigation
        html += `
            <div class="navigation">
                <button onclick="display.previousPair()" ${this.currentParagraph === 0 ? 'disabled' : ''}>Previous</button>
                <button onclick="display.nextPair()" ${this.currentParagraph === section.paragraphs.length - 1 ? 'disabled' : ''}>Next</button>
                <select onchange="display.goToSection(this.value)">
                    ${this.data.map((s, i) => `<option value="${i}" ${i === this.currentSection ? 'selected' : ''}>Section ${i+1}</option>`).join('')}
                </select>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    nextPair() {
        const section = this.data[this.currentSection];
        if (this.currentParagraph < section.paragraphs.length - 1) {
            this.currentParagraph++;
            this.renderCurrent();
        } else if (this.currentSection < this.data.length - 1) {
            this.currentSection++;
            this.currentParagraph = 0;
            this.renderCurrent();
        }
    }
    
    previousPair() {
        if (this.currentParagraph > 0) {
            this.currentParagraph--;
            this.renderCurrent();
        } else if (this.currentSection > 0) {
            this.currentSection--;
            this.currentParagraph = this.data[this.currentSection].paragraphs.length - 1;
            this.renderCurrent();
        }
    }
    
    goToSection(sectionIndex) {
        this.currentSection = parseInt(sectionIndex);
        this.currentParagraph = 0;
        this.renderCurrent();
    }
}

// Initialize display
document.addEventListener('DOMContentLoaded', function() {
    fetch('epub_content_web.json')
        .then(response => response.json())
        .then(data => {
            window.display = new BilingualDisplay('content-container', data);
            window.display.renderCurrent();
        });
});
"""

# CSS for web display
CSS_STYLES = """
.bilingual-section {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 5px;
    margin-bottom: 20px;
    font-size: 0.9em;
    color: #666;
}

.section-title {
    text-align: center;
    margin: 20px 0;
    font-size: 1.5em;
    color: #00557f;
}

.paragraph-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.english-text {
    font-size: 1.2em;
    color: #333;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

.chinese-text {
    font-size: 1.3em;
    color: #00557f;
    margin-bottom: 15px;
    font-weight: 500;
}

.annotations {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 5px;
    line-height: 2.5;
}

ruby {
    ruby-align: center;
    margin: 0 2px;
}

rt {
    font-size: 0.7em;
    color: #666;
}

.grammatical-class {
    font-size: 0.6em;
    color: #999;
    margin-right: 2px;
    vertical-align: super;
}

.word-token {
    font-size: 1.1em;
}

/* Syntax coloring */
.chinese.n .word-token { color: #2c3e50; }
.chinese.v .word-token { color: #27ae60; }
.chinese.adj .word-token { color: #e67e22; }
.chinese.adv .word-token { color: #3498db; }
.chinese.p .word-token { color: #9b59b6; }
.chinese.r .word-token { color: #e74c3c; }
.chinese.x .word-token { color: #7f8c8d; }
.chinese.o .word-token { color: #95a5a6; }

.navigation {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 20px;
}

.navigation button {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    background: #00557f;
    color: white;
    cursor: pointer;
    font-size: 1em;
}

.navigation button:hover:not(:disabled) {
    background: #003d5e;
}

.navigation button:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.navigation select {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1em;
}
"""

# Example usage
if __name__ == "__main__":
    epub_file = "/home/zaya/Downloads/Zayas/ZayasBooks/t/Cinema-Quotes-Doubt-Primordial-Scence-Fantasy-Abuse-db-ch_transliterated_ccs.epub"
    output_directory = "/home/zaya/Downloads/Zayas/ZayasBooks/t"
    
    # Process the EPUB
    result = process_epub_for_web(epub_file, output_directory)
    
    # Save the web component files
    with open(os.path.join(output_directory, 'chinese-display.js'), 'w', encoding='utf-8') as f:
        f.write(WEB_COMPONENT)
    
    with open(os.path.join(output_directory, 'styles.css'), 'w', encoding='utf-8') as f:
        f.write(CSS_STYLES)
    
    # Create a simple HTML viewer
    html_viewer = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bilingual Reader</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="content-container"></div>
    <script src="chinese-display.js"></script>
</body>
</html>"""
    
    with open(os.path.join(output_directory, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_viewer)
    
    print("\nProcessing complete!")
    print(f"Generated files in {output_directory}:")
    for key, path in result.items():
        print(f"  - {key}: {path}")
    print("  - index.html: Web viewer")
    print("  - styles.css: CSS styles")
    print("  - chinese-display.js: JavaScript component")
