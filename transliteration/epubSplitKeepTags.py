from bs4 import BeautifulSoup, Tag
import re

def debug_print(title, content):
    print(f"\n=== {title} ===")
    print(content if len(content) < 500 else content[:500] + "... [truncated]")

def split_sentences(text):
    """Enhanced multilingual sentence splitting that handles quotes"""
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.!?…。！？])(?:\s+|(?=[’”"»›]|$))', text)

def process_paragraph(p, soup, para_num):
    original_html = str(p)
    original_text = p.get_text(strip=True)
    
    # Don't process if too short or only one sentence
    sentences = split_sentences(original_text)
    if len(sentences) <= 1 or len(original_text) < 15:
        debug_print(f"Paragraph {para_num} - Kept intact (single phrase)", original_html)
        return False
    
    debug_print(f"Original Paragraph {para_num}", original_html)
    parent = p.parent
    p.extract()  # Remove original paragraph
    
    new_paragraphs = []
    current_paragraph = soup.new_tag('p')
    current_spans = []  # Track nested span hierarchy
    
    for content in p.contents:
        if isinstance(content, str):
            parts = split_sentences(content)
            for part in parts:
                if not part.strip():
                    continue
                
                # If we have spans to reopen
                if current_spans:
                    for span in current_spans:
                        new_span = soup.new_tag('span')
                        for attr, value in span.attrs.items():
                            new_span[attr] = value
                        current_paragraph.append(new_span)
                        current_paragraph = new_span  # Nest further
                
                current_paragraph.append(part)
                
                # If this looks like sentence end, finalize paragraph
                if re.search(r'[.!?…。！？][’”"»›]?$', part.strip()):
                    if len(current_paragraph.contents) > 0:
                        # Close all nested spans
                        while current_paragraph.name == 'span':
                            current_paragraph = current_paragraph.parent
                        new_paragraphs.append(current_paragraph)
                        current_paragraph = soup.new_tag('p')
                        current_spans = []  # Reset span stack
        
        elif isinstance(content, Tag) and content.name == 'span':
            # Handle span opening
            current_spans.append(content)
            new_span = soup.new_tag('span')
            for attr, value in content.attrs.items():
                new_span[attr] = value
            current_paragraph.append(new_span)
            current_paragraph = new_span
        
        elif content.name in ['br', 'sup', 'sub', 'em', 'strong']:
            # Handle other inline elements
            new_tag = soup.new_tag(content.name)
            for attr, value in content.attrs.items():
                new_tag[attr] = value
            new_tag.string = content.get_text()
            current_paragraph.append(new_tag)
    
    # Add any remaining content
    if len(current_paragraph.contents) > 0:
        new_paragraphs.append(current_paragraph)
    
    # Insert all new paragraphs where original was
    for i, new_p in enumerate(new_paragraphs):
        parent.append(new_p)
        debug_print(f"Created new paragraph {i+1}", str(new_p))
    
    return True

def process_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    para_num = 0
    for p in soup.find_all(['p', 'blockquote']):
        if p.name == 'blockquote':
            for bp in p.find_all('p'):
                para_num += 1
                process_paragraph(bp, soup, para_num)
        else:
            para_num += 1
            process_paragraph(p, soup, para_num)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n')
        f.write(str(soup))

# Test case with nested spans
test_html = """
<p><span class="font6">Questo brano dovrebbe sorprendere chiunque conosca Lacan. <span style="font-style:italic">In quanto fa coincidere il grande Altro</span> con l'impenetrabilità di un altro soggetto. Che cos'è, dunque, il grande Altro?</span></p>
"""

with open("test_nested_spans.html", "w", encoding="utf-8") as f:
    f.write(test_html)

print("Starting processing...")
process_html_file("test_nested_spans.html")
print("\nProcessing complete!")