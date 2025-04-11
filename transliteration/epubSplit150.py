def split_paragraphs(soup):
    """Split paragraphs at sentence boundaries or at commas for long phrases"""
    paragraphs = soup.find_all('p')
    
    for p in paragraphs:
        text = p.get_text()
        # Skip if too short
        if len(text) < 15:
            continue
            
        # Split sentences using our enhanced regex
        sentences = SPLIT_REGEX.split(text)
        
        # Process each sentence
        current = p
        current.clear()  # Clear original paragraph to rebuild
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # For normal length sentences
            if len(sentence) <= 150:
                if current.contents and not current.contents[-1].endswith(' '):
                    current.append(' ')
                current.append(sentence)
                continue
                
            # For long sentences (>150 chars), we need to split further
            remaining = sentence
            while len(remaining) > 150:
                # Try to find last comma in first 150 chars
                comma_pos = remaining[:150].rfind(',')
                # If no comma, find last space
                split_pos = comma_pos if comma_pos != -1 else remaining[:150].rfind(' ')
                
                if split_pos == -1:  # No good split point found
                    split_pos = 150  # Force split at 150 chars
                
                # Split the sentence
                first_part = remaining[:split_pos+1].strip()
                remaining = remaining[split_pos+1:].strip()
                
                # Add the first part
                if current.contents and not current.contents[-1].endswith(' '):
                    current.append(' ')
                current.append(first_part)
                
                # Create new paragraph for remaining text
                new_p = soup.new_tag('p')
                current.insert_after(new_p)
                current = new_p
                current.append(remaining[:remaining.find(' ', 50)] if ' ' in remaining else remaining)
                remaining = remaining[remaining.find(' ', 50)+1:] if ' ' in remaining else ''
            
            # Add any remaining text
            if remaining:
                if current.contents and not current.contents[-1].endswith(' '):
                    current.append(' ')
                current.append(remaining)
    
    return soup