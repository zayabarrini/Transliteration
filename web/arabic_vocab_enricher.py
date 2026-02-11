import importlib.util
import logging
import re
from pathlib import Path

import pandas as pd
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.morphology.database import MorphologyDB
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.charmap import CharMapper
from camel_tools.utils.dediac import dediac_ar
from camel_tools.utils.normalize import (
    normalize_alef_ar,
    normalize_alef_maksura_ar,
    normalize_teh_marbuta_ar,
)

# Import examples from external file
try:
    spec = importlib.util.spec_from_file_location(
        "examples_ar", 
        Path(__file__).parent / "examples-ar.py"
    )
    examples_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(examples_module)
    examples = examples_module.examples
    logger = logging.getLogger(__name__)
    logger.info(f"✓ Loaded {len(examples)} example sentences")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load examples-ar.py: {e}")
    # Fallback examples
    examples = {
        'ضابط': 'ضباط كبار.',
        'ضباط': 'ضباط كبار.',
        'قناص': 'قناصة إسرائيليون.',
        'قناصة': 'قناصة إسرائيليون.',
        'مغوار': 'مغاوير الصاعقة.',
        'مغاوير': 'مغاوير الصاعقة.',
    }

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ArabicVocabularyEnricher:
    def __init__(self):
        """Initialize Camel Tools components"""
        logger.info("Loading Camel Tools resources...")
        
        # Load morphology database
        try:
            self.db = MorphologyDB.builtin_db()
            self.analyzer = Analyzer(self.db)
            self.disambiguator = MLEDisambiguator.pretrained()
            logger.info("✓ Camel Tools loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Camel Tools: {e}")
            raise
        
        # For transliteration
        self.bw2ar = CharMapper.builtin_mapper('bw2ar')
        self.ar2bw = CharMapper.builtin_mapper('ar2bw')
    
    def normalize_arabic(self, text):
        """Normalize Arabic text for better analysis"""
        if not isinstance(text, str) or not text.strip():
            return ""
        
        # Remove parentheses and content
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'（[^）]*）', '', text)
        
        # Remove plural indicators
        text = text.replace(' (ج)', '').replace('(ج)', '')
        text = text.replace(' (pl.)', '').replace('(pl.)', '')
        
        # Clean and normalize
        text = dediac_ar(text)
        text = normalize_alef_ar(text)
        text = normalize_alef_maksura_ar(text)
        text = normalize_teh_marbuta_ar(text)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
    
    def is_valid_arabic_word(self, word):
        """Check if the input is a valid Arabic word"""
        if not isinstance(word, str) or not word.strip():
            return False
        
        # Remove parentheses and indicators first
        clean_word = re.sub(r'\([^)]*\)', '', word)
        clean_word = re.sub(r'（[^）]*）', '', clean_word)
        clean_word = clean_word.replace(' (ج)', '').replace('(ج)', '')
        clean_word = clean_word.replace(' (pl.)', '').replace('(pl.)', '')
        clean_word = clean_word.strip()
        
        # Arabic Unicode range check
        arabic_pattern = re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s]+$')
        
        return bool(arabic_pattern.match(clean_word)) and len(clean_word) > 0
    
    def get_pos_tag(self, word):
        """Get POS tag for Arabic word - FIXED VERSION"""
        try:
            if not self.is_valid_arabic_word(word):
                return "NOT_ARABIC"
            
            # Clean the word
            clean_word = self.normalize_arabic(word)
            if not clean_word:
                return "EMPTY"
            
            # For multi-word phrases, process each word separately
            if ' ' in clean_word:
                words = clean_word.split()
                pos_tags = []
                for w in words:
                    pos = self._get_single_word_pos(w)
                    pos_tags.append(pos)
                return '/'.join(pos_tags)
            else:
                return self._get_single_word_pos(clean_word)
            
        except Exception as e:
            logger.warning(f"POS error for '{word}': {e}")
            return "ERROR"
    
    def _get_single_word_pos(self, word):
        """Get POS tag for a single Arabic word"""
        try:
            # Tokenize
            tokens = simple_word_tokenize(word)
            if not tokens:
                return "NO_TOKENS"
            
            # Disambiguate
            disambig = self.disambiguator.disambiguate(tokens)
            
            pos_tags = []
            for analysis_list in disambig:
                if analysis_list.analyses:
                    # Get the most probable analysis
                    top_analysis = analysis_list.analyses[0]
                    
                    # FIX: Different ways to access POS in Camel Tools
                    # Try different possible attribute names
                    if hasattr(top_analysis, 'pos'):
                        pos = top_analysis.pos
                    elif hasattr(top_analysis, '_pos'):
                        pos = top_analysis._pos
                    elif hasattr(top_analysis, 'get_pos'):
                        pos = top_analysis.get_pos()
                    elif hasattr(top_analysis, 'analysis'):
                        # Some versions store in analysis dict
                        analysis_dict = top_analysis.analysis if hasattr(top_analysis, 'analysis') else {}
                        pos = analysis_dict.get('pos', 'UNKNOWN')
                    else:
                        # Try to access as dictionary
                        try:
                            pos = top_analysis.get('pos', 'UNKNOWN')
                        except:
                            pos = str(type(top_analysis))  # Debug info
                    
                    pos_tags.append(str(pos))
                else:
                    pos_tags.append("UNKNOWN")
            
            return '/'.join(pos_tags) if pos_tags else "UNKNOWN"
            
        except Exception as e:
            logger.debug(f"Single word POS error for '{word}': {e}")
            return "UNKNOWN"
    
    def get_gloss(self, word):
        """Get gloss/meaning for Arabic word - FIXED VERSION"""
        try:
            if not self.is_valid_arabic_word(word):
                return "NOT_ARABIC"
            
            clean_word = self.normalize_arabic(word)
            if not clean_word:
                return "EMPTY"
            
            # For multi-word phrases, process each word separately
            if ' ' in clean_word:
                words = clean_word.split()
                glosses = []
                for w in words:
                    gloss = self._get_single_word_gloss(w)
                    glosses.append(gloss)
                return '; '.join(glosses)
            else:
                return self._get_single_word_gloss(clean_word)
            
        except Exception as e:
            logger.warning(f"Gloss error for '{word}': {e}")
            return "ERROR"
    
    def _get_single_word_gloss(self, word):
        """Get gloss for a single Arabic word"""
        try:
            tokens = simple_word_tokenize(word)
            disambig = self.disambiguator.disambiguate(tokens)
            
            glosses = []
            for analysis_list in disambig:
                if analysis_list.analyses:
                    top_analysis = analysis_list.analyses[0]
                    
                    # FIX: Different ways to access gloss in Camel Tools
                    if hasattr(top_analysis, 'gloss'):
                        gloss = top_analysis.gloss
                    elif hasattr(top_analysis, '_gloss'):
                        gloss = top_analysis._gloss
                    elif hasattr(top_analysis, 'get_gloss'):
                        gloss = top_analysis.get_gloss()
                    elif hasattr(top_analysis, 'analysis'):
                        analysis_dict = top_analysis.analysis if hasattr(top_analysis, 'analysis') else {}
                        gloss = analysis_dict.get('gloss', 'NO_GLOSS')
                    else:
                        # Try to access as dictionary
                        try:
                            gloss = top_analysis.get('gloss', 'NO_GLOSS')
                        except:
                            gloss = 'NO_GLOSS'
                    
                    if gloss and gloss != 'NO_GLOSS':
                        glosses.append(str(gloss))
                    else:
                        glosses.append("NO_GLOSS")
                else:
                    glosses.append("UNKNOWN")
            
            return '; '.join(glosses) if glosses else "NO_GLOSS_FOUND"
            
        except Exception as e:
            logger.debug(f"Single word gloss error for '{word}': {e}")
            return "NO_GLOSS"
    
    def get_example_sentence(self, word):
        """Generate example sentence using the word with partial matching"""
        
        if not isinstance(word, str):
            return "NO_EXAMPLE_AVAILABLE"
        
        # Store original and clean versions
        raw_word = word
        clean_word = self.normalize_arabic(word)
        
        if not clean_word:
            return "NO_EXAMPLE_AVAILABLE"
        
        # --- STEP 1: EXACT MATCH ---
        if clean_word in examples:
            return examples[clean_word]
        if raw_word in examples:
            return examples[raw_word]
        
        # --- STEP 2: WITHOUT DEFINITE ARTICLE ---
        if clean_word.startswith('ال'):
            without_al = clean_word[2:]
            if without_al in examples:
                return examples[without_al]
        
        # --- STEP 3: EXTRACT BASE WORD (before parentheses) ---
        base_word_match = re.match(r'^([^\(（]+)', raw_word)
        if base_word_match:
            base_word = base_word_match.group(1).strip()
            base_word_norm = self.normalize_arabic(base_word)
            
            if base_word_norm in examples:
                return examples[base_word_norm]
            if base_word in examples:
                return examples[base_word]
        
        # --- STEP 4: WITHOUT PLURAL INDICATORS ---
        without_plural = re.sub(r'\([^)]*\)', '', raw_word).strip()
        without_plural = re.sub(r'[（][^）]*[）]', '', without_plural).strip()
        without_plural_norm = self.normalize_arabic(without_plural)
        
        if without_plural_norm in examples:
            return examples[without_plural_norm]
        if without_plural in examples:
            return examples[without_plural]
        
        # --- STEP 5: PARTIAL MATCH for singular/plural patterns ---
        singular_match = re.match(r'^([^\(（]+)\s*\([^)]*[جpl.]*[^)]*\)\s*[^\(（]+$', raw_word)
        if singular_match:
            singular = singular_match.group(1).strip()
            singular_norm = self.normalize_arabic(singular)
            if singular_norm in examples:
                return examples[singular_norm]
        
        plural_match = re.search(r'\)\s*([^\(（]+)$', raw_word)
        if plural_match:
            plural = plural_match.group(1).strip()
            plural_norm = self.normalize_arabic(plural)
            if plural_norm in examples:
                return examples[plural_norm]
        
        # --- STEP 6: LOOSE PARTIAL MATCHING ---
        best_match = None
        best_match_score = 0
        
        for key, example in examples.items():
            key_norm = self.normalize_arabic(key)
            
            if not key_norm or not clean_word:
                continue
            
            score = 0
            
            if key_norm in clean_word:
                score = len(key_norm) * 2
            elif clean_word in key_norm:
                score = len(clean_word) * 2
            
            if score == 0:
                # Check for common substring
                for i in range(min(len(key_norm), len(clean_word)), 2, -1):
                    for j in range(len(key_norm) - i + 1):
                        substring = key_norm[j:j+i]
                        if substring in clean_word:
                            score = i
                            break
                    if score > 0:
                        break
            
            if score == 0:
                common_letters = set(key_norm) & set(clean_word)
                if len(common_letters) >= 3:
                    score = len(common_letters)
            
            if score > best_match_score:
                best_match = example
                best_match_score = score
        
        if best_match and best_match_score >= 3:
            return best_match
        
        # --- STEP 7: SMART DEFAULT EXAMPLES ---
        base_form = re.sub(r'\([^)]*\)', '', raw_word).strip()
        base_form = re.sub(r'[（][^）]*[）]', '', base_form).strip()
        base_form = base_form.split()[0] if base_form else clean_word
        
        # Specialized examples for different word types
        if any(term in raw_word for term in ['وقف', 'نيران', 'هدنات', 'حلول', 'مفاوضات', 'محادثات', 'مباحثات', 'حوار', 'وسطاء']):
            if 'وقف' in raw_word or 'نيران' in raw_word:
                return 'تم الاتفاق على وقف إطلاق النار بين الطرفين.'
            elif 'هدنات' in raw_word or 'هدنة' in raw_word:
                return 'تم تمديد الهدنة الإنسانية لمدة أسبوع.'
            elif 'حلول' in raw_word or 'حل' in raw_word:
                return 'يبحث المجتمع الدولي عن حلول سلمية للصراع.'
            elif 'مفاوضات' in raw_word or 'محادثات' in raw_word or 'مباحثات' in raw_word:
                return 'استؤنفت المفاوضات بين الوفود في جنيف.'
            elif 'حوار' in raw_word:
                return 'الحوار هو السبيل الوحيد لحل الخلافات.'
            elif 'وسطاء' in raw_word:
                return 'يبذل الوسطاء جهوداً مكثفة للتقريب بين وجهات النظر.'
        
        # Check if it's a plural form
        if 'ج' in raw_word or 'pl.' in raw_word or raw_word.endswith('ات') or raw_word.endswith('ون') or raw_word.endswith('ين'):
            return f'هؤلاء {base_form} متميزون في عملهم.'
        
        # Check if it's a feminine form
        if base_form.endswith('ة'):
            return f'هذه {base_form} جميلة.'
        
        # Default masculine singular
        return f'هذا {base_form} رائع.'
    
    def process_vocabulary(self, df, arabic_column='Standard Arabic'):
        """Process entire vocabulary dataframe"""
        logger.info(f"Processing vocabulary from column: {arabic_column}")
        
        # Initialize new columns
        df['POS_Tags'] = ''
        df['Gloss'] = ''
        df['Example_Usage'] = ''
        
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            arabic_word = row.get(arabic_column, '')
            
            # Progress logging - only every 100 rows to reduce noise
            if idx % 100 == 0:
                logger.info(f"Processing [{idx}/{total_rows}]: {arabic_word}")
            
            # Handle empty cells
            if pd.isna(arabic_word) or not str(arabic_word).strip():
                df.at[idx, 'POS_Tags'] = "EMPTY_CELL"
                df.at[idx, 'Gloss'] = "EMPTY_CELL"
                df.at[idx, 'Example_Usage'] = "NO_EXAMPLE"
                continue
            
            # Convert to string
            arabic_word = str(arabic_word)
            
            # Check if it's valid Arabic
            if not self.is_valid_arabic_word(arabic_word):
                df.at[idx, 'POS_Tags'] = "NOT_ARABIC"
                df.at[idx, 'Gloss'] = "NOT_ARABIC"
                df.at[idx, 'Example_Usage'] = self.get_example_sentence(arabic_word)
                continue
            
            # Get POS, Gloss, and Example
            pos = self.get_pos_tag(arabic_word)
            gloss = self.get_gloss(arabic_word)
            example = self.get_example_sentence(arabic_word)
            
            df.at[idx, 'POS_Tags'] = pos
            df.at[idx, 'Gloss'] = gloss
            df.at[idx, 'Example_Usage'] = example
        
        logger.info("✓ Processing complete!")
        return df


def main():
    """Main execution function"""
    input_file = '/home/zaya/Downloads/Zayas/ZayasTransliteration/web/arabic-vocab.csv'
    output_file = '/home/zaya/Downloads/Zayas/ZayasTransliteration/web/arabic-vocab-enhanced.csv'
    
    try:
        # Read CSV
        logger.info(f"Reading CSV file: {input_file}")
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} rows")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Initialize enricher
        enricher = ArabicVocabularyEnricher()
        
        # Find Arabic column
        arabic_column = None
        possible_names = ['Standard Arabic', 'Arabic', 'Standard_Arabic', 'standard_arabic', 'عربي']
        
        for col in possible_names:
            if col in df.columns:
                arabic_column = col
                logger.info(f"Found Arabic column: {arabic_column}")
                break
        
        if not arabic_column:
            # Auto-detect first column with Arabic text
            for col in df.columns:
                sample = df[col].iloc[0] if len(df) > 0 else ''
                if isinstance(sample, str) and re.search(r'[\u0600-\u06FF]', sample):
                    arabic_column = col
                    logger.info(f"Auto-detected Arabic column: {arabic_column}")
                    break
        
        if not arabic_column:
            raise ValueError("No Arabic column found in CSV")
        
        # Process the data
        enhanced_df = enricher.process_vocabulary(df, arabic_column=arabic_column)
        
        # Save to new CSV
        enhanced_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"✓ Enhanced vocabulary saved to: {output_file}")
        
        # Display sample
        logger.info("\nSample of enhanced data:")
        print("\n" + "="*80)
        display_cols = [arabic_column, 'POS_Tags', 'Gloss', 'Example_Usage']
        print(enhanced_df[display_cols].head(20).to_string())
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()