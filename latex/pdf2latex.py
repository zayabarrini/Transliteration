#!/usr/bin/env python3
"""
PDF to LaTeX converter for transliteration_tools project
Supports text extraction, equation recognition, and basic LaTeX formatting
"""

import os
import sys
import fitz  # PyMuPDF
import pdfplumber
import requests
import base64
import json
from pathlib import Path
import re
from PIL import Image
import io
import subprocess
from typing import List, Dict, Tuple, Optional

# Add parent directory to path to import project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class PDFToLaTeXConverter:
    """
    Converts PDF documents to LaTeX format with support for mathematical equations
    and multilingual text handling.
    """
    
    def __init__(self, use_mathpix: bool = False, mathpix_credentials: Optional[Dict] = None):
        """
        Initialize the converter
        
        Args:
            use_mathpix: Whether to use Mathpix API for equation recognition
            mathpix_credentials: Dict with 'app_id' and 'app_key' for Mathpix API
        """
        self.use_mathpix = use_mathpix
        self.mathpix_credentials = mathpix_credentials
        
        # Try to import pix2tex for free equation OCR
        try:
            from pix2tex.cli import LatexOCR
            self.math_ocr = LatexOCR()
            self.has_pix2tex = True
        except ImportError:
            self.has_pix2tex = False
            print("Warning: pix2tex not installed. Equations will be extracted as images.")
    
    def convert_pdf(self, pdf_path: str, output_tex: str, 
                   extract_equations: bool = True, 
                   preserve_layout: bool = True) -> Dict:
        """
        Main conversion function
        
        Args:
            pdf_path: Path to input PDF file
            output_tex: Path for output LaTeX file
            extract_equations: Whether to attempt equation recognition
            preserve_layout: Whether to try preserving original layout
        
        Returns:
            Dict with conversion statistics and metadata
        """
        pdf_path = Path(pdf_path)
        output_tex = Path(output_tex)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"Converting {pdf_path} to {output_tex}")
        
        # Extract content from PDF
        text_content, equations, images, metadata = self._extract_pdf_content(
            pdf_path, extract_equations, preserve_layout
        )
        
        # Generate LaTeX document
        latex_document = self._generate_latex_document(text_content, equations, images, metadata)
        
        # Write output file
        output_tex.parent.mkdir(parents=True, exist_ok=True)
        with open(output_tex, 'w', encoding='utf-8') as f:
            f.write(latex_document)
        
        # Generate conversion report
        report = {
            'input_file': str(pdf_path),
            'output_file': str(output_tex),
            'pages_processed': metadata.get('pages', 0),
            'equations_found': len(equations),
            'images_extracted': len(images),
            'success': True
        }
        
        print(f"Conversion complete: {report}")
        return report
    
    def _extract_pdf_content(self, pdf_path: Path, extract_equations: bool, 
                           preserve_layout: bool) -> Tuple[str, List, List, Dict]:
        """Extract text, equations, and images from PDF"""
        text_content = ""
        equations = []
        images = []
        metadata = {}
        
        # Method 1: Use pdfplumber for better text extraction
        if preserve_layout:
            text_content, metadata = self._extract_with_pdfplumber(pdf_path)
        else:
            text_content, metadata = self._extract_with_pymupdf(pdf_path)
        
        # Extract equations if requested
        if extract_equations:
            equations = self._extract_equations(pdf_path)
        
        # Extract images
        images = self._extract_images(pdf_path)
        
        return text_content, equations, images, metadata
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Tuple[str, Dict]:
        """Extract text using pdfplumber (better layout preservation)"""
        text_content = ""
        metadata = {'pages': 0}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata['pages'] = len(pdf.pages)
                metadata['author'] = pdf.metadata.get('Author', '')
                metadata['title'] = pdf.metadata.get('Title', '')
                metadata['creator'] = pdf.metadata.get('Creator', '')
                
                for page_num, page in enumerate(pdf.pages):
                    print(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                    
                    # Extract text with layout information
                    text = page.extract_text()
                    if text:
                        # Convert to LaTeX-friendly format
                        latex_text = self._text_to_latex(text, page_num + 1)
                        text_content += latex_text + "\n\\newpage\n"
                    
        except Exception as e:
            print(f"Error with pdfplumber: {e}. Falling back to PyMuPDF.")
            return self._extract_with_pymupdf(pdf_path)
        
        return text_content, metadata
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> Tuple[str, Dict]:
        """Extract text using PyMuPDF (fallback method)"""
        text_content = ""
        metadata = {}
        
        doc = fitz.open(pdf_path)
        metadata['pages'] = len(doc)
        metadata['author'] = doc.metadata.get('author', '')
        metadata['title'] = doc.metadata.get('title', '')
        metadata['creator'] = doc.metadata.get('creator', '')
        
        for page_num in range(len(doc)):
            print(f"Processing page {page_num + 1}/{len(doc)}")
            
            page = doc[page_num]
            text = page.get_text()
            
            if text:
                latex_text = self._text_to_latex(text, page_num + 1)
                text_content += latex_text + "\n\\newpage\n"
        
        doc.close()
        return text_content, metadata
    
    def _extract_equations(self, pdf_path: Path) -> List[Dict]:
        """Extract and recognize mathematical equations"""
        equations = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            # Get images that might contain equations
            image_list = doc[page_num].get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # RGB or Grayscale
                        img_data = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_data))
                        
                        # Recognize equation
                        latex_eq = self._recognize_equation(image)
                        if latex_eq:
                            equations.append({
                                'page': page_num + 1,
                                'equation': latex_eq,
                                'image_index': img_index
                            })
                    
                    pix = None  # Free memory
                    
                except Exception as e:
                    print(f"Error processing equation image: {e}")
                    continue
        
        doc.close()
        return equations
    
    def _recognize_equation(self, image: Image.Image) -> Optional[str]:
        """Recognize equation using available methods"""
        # Try Mathpix API first if configured
        if self.use_mathpix and self.mathpix_credentials:
            return self._mathpix_recognize(image)
        
        # Try pix2tex as free alternative
        if self.has_pix2tex:
            try:
                return self.math_ocr(image)
            except Exception as e:
                print(f"pix2tex recognition failed: {e}")
        
        return None
    
    def _mathpix_recognize(self, image: Image.Image) -> Optional[str]:
        """Use Mathpix API for equation recognition"""
        try:
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            headers = {
                'app_id': self.mathpix_credentials['app_id'],
                'app_key': self.mathpix_credentials['app_key'],
                'Content-type': 'application/json'
            }
            
            data = {
                'src': f'data:image/png;base64,{img_str}',
                'formats': ['latex_styled']
            }
            
            response = requests.post(
                'https://api.mathpix.com/v3/text',
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('latex_styled')
            else:
                print(f"Mathpix API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Mathpix recognition failed: {e}")
            return None
    
    def _extract_images(self, pdf_path: Path) -> List[Dict]:
        """Extract images from PDF"""
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            image_list = doc[page_num].get_images()
            
            for img_index, img in enumerate(image_list):
                images.append({
                    'page': page_num + 1,
                    'image_index': img_index,
                    'xref': img[0]
                })
        
        doc.close()
        return images
    
    def _text_to_latex(self, text: str, page_num: int) -> str:
        """Convert plain text to basic LaTeX formatting"""
        if not text.strip():
            return ""
        
        # Basic cleaning
        text = text.replace('\\', '\\textbackslash ')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('&', '\\&')
        text = text.replace('%', '\\%')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('_', '\\_')
        text = text.replace('^', '\\^{}')
        text = text.replace('~', '\\~{}')
        
        # Detect and format mathematical expressions
        text = self._format_mathematical_expressions(text)
        
        # Format sections and headings
        text = self._format_headings(text)
        
        # Handle line breaks and paragraphs
        text = self._format_paragraphs(text)
        
        return text
    
    def _format_mathematical_expressions(self, text: str) -> str:
        """Attempt to detect and format mathematical expressions"""
        # Common mathematical patterns
        patterns = [
            # Simple fractions: a/b -> \frac{a}{b}
            (r'(\w+)/(\w+)', r'\\frac{\1}{\2}'),
            # Superscripts: x^2 -> x^{2}
            (r'(\w+)\^(\d+)', r'\1^{\2}'),
            # Subscripts: x_2 -> x_{2}
            (r'(\w+)_(\d+)', r'\1_{\2}'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _format_headings(self, text: str) -> str:
        """Detect and format section headings"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Detect section headings (numbered or bold text patterns)
            if re.match(r'^\d+\.\d+\s+', stripped):  # 1.1 Section Title
                title = re.sub(r'^\d+\.\d+\s+', '', stripped)
                formatted_lines.append(f'\\subsection{{{title}}}')
            elif re.match(r'^\d+\.\s+', stripped):  # 1. Section Title
                title = re.sub(r'^\d+\.\s+', '', stripped)
                formatted_lines.append(f'\\section{{{title}}}')
            elif re.match(r'^[A-Z][A-Z\s]{10,}', stripped):  # ALL CAPS heading
                formatted_lines.append(f'\\section*{{{stripped}}}')
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_paragraphs(self, text: str) -> str:
        """Format paragraphs and line breaks"""
        # Replace multiple newlines with paragraph breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Handle single line breaks within paragraphs
        lines = text.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            if line.strip():  # Non-empty line
                if i > 0 and lines[i-1].strip():  # Previous line was also non-empty
                    formatted_lines.append('\\\\' + line)
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append('')  # Empty line for paragraph break
        
        return '\n'.join(formatted_lines)
    
    def _generate_latex_document(self, text_content: str, equations: List[Dict], 
                               images: List[Dict], metadata: Dict) -> str:
        """Generate complete LaTeX document"""
        # Document header
        latex_template = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{geometry}

\geometry{a4paper, margin=1in}

\title{%s}
\author{%s}
\date{}

\begin{document}

\maketitle

\tableofcontents

%s

%s

\end{document}"""
        
        # Prepare title and author
        title = metadata.get('title', 'Converted Document').replace('&', '\\&')
        author = metadata.get('author', '').replace('&', '\\&')
        
        # Prepare equations section if any were found
        equations_section = ""
        if equations:
            equations_section = "\n\\section*{Extracted Equations}\n\\begin{align*}\n"
            for i, eq in enumerate(equations):
                equations_section += f"    {eq['equation']} \\\\\n"
            equations_section += "\\end{align*}\n"
        
        return latex_template % (title, author, text_content, equations_section)


def main():
    """Command-line interface for PDF to LaTeX conversion"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert PDF to LaTeX')
    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('-o', '--output', help='Output LaTeX file path')
    parser.add_argument('--no-equations', action='store_true', 
                       help='Skip equation extraction')
    parser.add_argument('--simple-layout', action='store_true',
                       help='Use simple layout extraction')
    parser.add_argument('--mathpix-id', help='Mathpix App ID')
    parser.add_argument('--mathpix-key', help='Mathpix App Key')
    
    args = parser.parse_args()
    
    # Set output path if not provided
    if not args.output:
        input_path = Path(args.input_pdf)
        args.output = input_path.with_suffix('.tex')
    
    # Configure Mathpix if credentials provided
    mathpix_credentials = None
    if args.mathpix_id and args.mathpix_key:
        mathpix_credentials = {
            'app_id': args.mathpix_id,
            'app_key': args.mathpix_key
        }
    
    # Create converter and process PDF
    converter = PDFToLaTeXConverter(
        use_mathpix=bool(mathpix_credentials),
        mathpix_credentials=mathpix_credentials
    )
    
    try:
        report = converter.convert_pdf(
            pdf_path=args.input_pdf,
            output_tex=args.output,
            extract_equations=not args.no_equations,
            preserve_layout=not args.simple_layout
        )
        
        print(f"Successfully converted {report['input_file']} to {report['output_file']}")
        print(f"Pages: {report['pages_processed']}, Equations: {report['equations_found']}")
        
    except Exception as e:
        print(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()