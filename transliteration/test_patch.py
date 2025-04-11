import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path modification
from modified.modified_kakasi import Kakasi as CustomKakasi
from modified.modified_hangul import Transliter as CustomTransliter
from modified.modified_pyarabic import custom_utf82latin as custom_arabic

# Original imports
import pykakasi as original_pykakasi
from hangul_romanize import Transliter as OriginalTransliter
from pyarabic import trans as original_pyarabic
from hangul_romanize.rule import academic 

# Monkey-patching
original_pykakasi.kakasi = lambda: CustomKakasi()
OriginalTransliter.__init__ = CustomTransliter.__init__

if not hasattr(original_pyarabic, 'custom_utf82latin'):
    original_pyarabic.custom_utf82latin = custom_arabic

# Test cases
def test_transliterations():
    print("Japanese:", original_pykakasi.kakasi().convert("日本語"))
    print("Korean:", OriginalTransliter(academic).translit("한글"))  # Pass the rule explicitly
    print("Arabic:", original_pyarabic.custom_utf82latin("عربي"))

if __name__ == "__main__":
    test_transliterations()