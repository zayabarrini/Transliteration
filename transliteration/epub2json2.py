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
            # Find all XHTML files in text directory
            split_files = []
            for file in zip_ref.namelist():
                if file.startswith('EPUB/text/') and file.endswith('.xhtml'):
                    split_files.append(file)
            
            # Sort files to maintain chapter order
            split_files.sort()
            
            # Process each split file
            for split_file in split_files:
                print(f"Processing: {split_file}")
                with zip_ref.open(split_file) as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    self._process_split_file(soup, split_file)
    
    def _process_split_file(self, soup, filename):
        """Process a single split file containing content"""
        # Find the body or section
        body = soup.find('body')
        if not body:
            body = soup.find('section')
        if not body:
            return
        
        # Get section ID from filename
        section_id = Path(filename).stem
        
        # Initialize section data
        section_data = {
            'section_id': section_id,
            'filename': filename,
            'paragraphs': [],
            'title': None
        }
        
        # Check for title (h1)
        title = body.find('h1')
        if title:
            title_text = title.get_text().strip()
            if title_text:
                section_data['title'] = {
                    'text': title_text,
                    'html': str(title)
                }
        
        # Process paragraphs in order
        current_english = None
        for element in body.find_all(['p', 'h1'], recursive=True):
            if element.name == 'p':
                # Check if it's Chinese (has lang="zh" attribute)
                if element.get('lang') == 'zh':
                    # This is a Chinese paragraph
                    chinese_text = element.get_text().strip()
                    
                    # Extract style if present (often has color)
                    style = element.get('style', '')
                    
                    para_data = {
                        'english': current_english if current_english else "",
                        'chinese': chinese_text,
                        'chinese_style': style,
                        'full_html': str(element)
                    }
                    section_data['paragraphs'].append(para_data)
                    current_english = None
                else:
                    # This is an English paragraph (no lang="zh" attribute)
                    current_english = element.get_text().strip()
            
            elif element.name == 'h1' and element != title:
                # Handle any additional headings
                heading_text = element.get_text().strip()
                if heading_text:
                    section_data['paragraphs'].append({
                        'type': 'heading',
                        'text': heading_text,
                        'full_html': str(element)
                    })
        
        self.sections[section_id] = section_data
    
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
                'title': section.get('title', {}).get('text') if section.get('title') else None,
                'paragraphs': []
            }
            
            # Process paragraphs
            i = 0
            while i < len(section['paragraphs']):
                para = section['paragraphs'][i]
                
                # If it's a regular paragraph with both English and Chinese
                if 'english' in para and 'chinese' in para:
                    web_para = {
                        'en': para['english'],
                        'zh': para['chinese'],
                        'zh_style': para.get('chinese_style', '')
                    }
                    web_section['paragraphs'].append(web_para)
                
                # If it's a heading
                elif para.get('type') == 'heading':
                    web_section['paragraphs'].append({
                        'type': 'heading',
                        'text': para['text']
                    })
                
                i += 1
            
            web_optimized.append(web_section)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(web_optimized, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def create_flat_paragraph_list(self, output_path):
        """Create a flat list of all paragraph pairs for easy navigation"""
        flat_list = []
        pair_id = 0
        
        for section_id, section in self.sections.items():
            for para in section['paragraphs']:
                if 'english' in para and 'chinese' in para:
                    flat_list.append({
                        'id': pair_id,
                        'section_id': section_id,
                        'filename': section['filename'],
                        'en': para['english'],
                        'zh': para['chinese'],
                        'zh_style': para.get('chinese_style', ''),
                        'html': para.get('full_html', '')
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
        'full_json': full_json_path,
        'web_json': web_json_path,
        'flat_json': flat_json_path
    }

# Web display component (JavaScript) - Updated for simple structure
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
                    ${section.title}
                </div>
            `;
        }
        
        // Check if it's a heading
        if (para.type === 'heading') {
            html += `
                <div class="heading">
                    <h2>${para.text}</h2>
                </div>
            `;
        } else {
            // Regular paragraph with English and Chinese
            const zhStyle = para.zh_style ? `style="${para.zh_style}"` : '';
            
            html += `
                <div class="paragraph-card">
                    <div class="english-text">${para.en}</div>
                    <div class="chinese-text" ${zhStyle}>${para.zh}</div>
                </div>
            `;
        }
        
        // Add navigation
        html += `
            <div class="navigation">
                <button onclick="display.previousPair()" ${this.currentParagraph === 0 ? 'disabled' : ''}>Previous</button>
                <button onclick="display.nextPair()" ${this.currentParagraph === section.paragraphs.length - 1 ? 'disabled' : ''}>Next</button>
                <select onchange="display.goToSection(this.value)">
                    ${this.data.map((s, i) => `<option value="${i}" ${i === this.currentSection ? 'selected' : ''}>Section ${i+1}${s.title ? ': ' + s.title.substring(0, 30) : ''}</option>`).join('')}
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
        })
        .catch(error => {
            console.error('Error loading data:', error);
            document.getElementById('content-container').innerHTML = 
                '<div class="error">Error loading content. Please check the console.</div>';
        });
});
"""

# CSS for web display - Updated for simple structure
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
    font-weight: bold;
}

.heading {
    text-align: center;
    margin: 30px 0 20px 0;
    padding: 10px;
    background: #f0f7ff;
    border-radius: 5px;
}

.heading h2 {
    margin: 0;
    color: #333;
    font-size: 1.3em;
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
    font-weight: 500;
    line-height: 1.6;
}

/* Preserve the blue color from EPUB */
.chinese-text[style*="color:#00557f"] {
    color: #00557f !important;
}

.navigation {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 20px;
    flex-wrap: wrap;
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
    min-width: 200px;
}

.error {
    color: #721c24;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 5px;
    padding: 20px;
    text-align: center;
    margin: 20px;
}
"""

# Example usage
if __name__ == "__main__":
    # Use the specific EPUB file path
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
    <title>Bilingual Reader - Cinema Quotes</title>
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