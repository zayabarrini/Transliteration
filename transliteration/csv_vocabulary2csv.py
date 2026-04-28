#!/usr/bin/env python3
"""
generate_vocab_csv.py - Exports Hindi vocabulary to CSV template for translation
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def flatten_vocabulary(data: Dict) -> List[Dict]:
    """Flatten nested vocabulary structure into rows"""
    rows = []
    counter = 1
    
    # Handle different category types
    categories = {
        'nouns': data.get('nouns', {}),
        'pronouns': data.get('pronouns', {}),
        'verbs': data.get('verbs', {}),
        'adjectives': data.get('adjectives', {}),
        'adverbs': data.get('adverbs', {}),
        'postpositions': data.get('postpositions', []),
        'conjunctions': data.get('conjunctions', {}),
        'interjections': data.get('interjections', []),
        'quantifiers': data.get('quantifiers', {}),
        'loanwords': data.get('loanwords', {})
    }
    
    for category, content in categories.items():
        if isinstance(content, dict):
            # Handle nested subcategories
            for subcat, words in content.items():
                if isinstance(words, list):
                    for word in words:
                        rows.append({
                            'id': f"{category[:3].upper()}{counter:04d}",
                            'category': category,
                            'subcategory': subcat,
                            'hindi': word.get('hindi', ''),
                            'translit': word.get('translit', ''),
                            'english': word.get('english', ''),
                            'ru': '',
                            'zh': '',
                            'ja': '',
                            'ko': '',
                            'ar': ''
                        })
                        counter += 1
                elif isinstance(words, dict):
                    # Handle nested objects (like loanwords)
                    for loan_source, loan_words in words.items():
                        if isinstance(loan_words, list):
                            for word in loan_words:
                                rows.append({
                                    'id': f"{category[:3].upper()}{counter:04d}",
                                    'category': category,
                                    'subcategory': f"{subcat}_{loan_source}",
                                    'hindi': word.get('hindi', ''),
                                    'translit': word.get('translit', ''),
                                    'english': word.get('english', ''),
                                    'ru': '', 'zh': '', 'ja': '', 'ko': '', 'ar': ''
                                })
                                counter += 1
        elif isinstance(content, list):
            # Handle top-level arrays
            for word in content:
                rows.append({
                    'id': f"{category[:3].upper()}{counter:04d}",
                    'category': category,
                    'subcategory': 'main',
                    'hindi': word.get('hindi', ''),
                    'translit': word.get('translit', ''),
                    'english': word.get('english', ''),
                    'ru': '', 'zh': '', 'ja': '', 'ko': '', 'ar': ''
                })
                counter += 1
    
    return rows

def generate_csv(vocab_json_path: Path, output_csv_path: Path):
    """Generate CSV template from vocabulary JSON"""
    with open(vocab_json_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    
    rows = flatten_vocabulary(vocab_data)
    
    fieldnames = ['id', 'category', 'subcategory', 'hindi', 'translit', 'english', 
                  'ru', 'zh', 'ja', 'ko', 'ar']
    
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Generated {len(rows)} rows to {output_csv_path}")

if __name__ == "__main__":
    # Adjust paths as needed
    vocab_json = Path("/home/zaya/Downloads/Zayas/zaya-monorepo/apps/signflow/static/json/wordList/Vocabulary.json")
    output_csv = Path("/home/zaya/Downloads/vocabulary_template.csv")
    
    generate_csv(vocab_json, output_csv)