# -*- coding: utf-8 -*-
#  kakasi.py
#
# Copyright 2011-2021 Hiroshi Miura <miurahr@linux.com>
#
import enum
from typing import Dict, List, Tuple, Optional
import re

import jaconv

try:
    # First try relative import (if this module is part of a package)
    from .kanji import JConv
    from .properties import Ch
    from .scripts import A2, H2, IConv, K2, Sym2
except ImportError:
    # Fallback to direct import from pykakasi
    from pykakasi.kanji import JConv
    from pykakasi.properties import Ch
    from pykakasi.scripts import A2, H2, IConv, K2, Sym2


class PyKakasiException(Exception):
    pass


class UnknownCharacterException(PyKakasiException):
    pass


class Kakasi:
    """Enhanced Kakasi conversion class for Japanese text with better furigana support."""

    def __init__(self):
        self._jconv = JConv()
        self._iconv = IConv()
        # Define Japanese punctuation that should be handled specially
        self.japanese_punctuation = [' ', '。', '、', '！', '？', '「', '」', '『', '』', '（', '）', '・']

    @classmethod
    def normalize(cls, text):
        """Normalize Japanese text."""
        return jaconv.normalize(text)
        
    def is_latin(self, token):  # as instance method
        """Check if a token contains only Latin characters, numbers, or basic punctuation."""
        return bool(re.fullmatch(r'^[\w\s.,;:!?\'"()\-–—\[\]{}@#$%^&*+=/\\|~<>]+$', token, re.UNICODE))

    def convert(self, text: str) -> List[Dict[str, str]]:
        """Convert Japanese text to dictionary with detailed information for furigana.
        
        Returns:
            List of dictionaries containing:
            - orig: original character(s)
            - kana: katakana representation
            - hira: hiragana representation
            - hepburn: Hepburn romanization
            - passport: Passport romanization
            - kunrei: Kunrei-shiki romanization
        """
        if not text:
            return [{
                "orig": "",
                "kana": "",
                "hira": "",
                "hepburn": "",
                "passport": "",
                "kunrei": "",
            }]

        result = []
        i = 0
        length = len(text)

        while i < length:
            char = text[i]
            
            # if self.is_latin(char):
            #     # Skip Latin characters
            #     # result.append({})
            #     i += 1
            #     continue
            
            # Check for punctuation first
            if char in self.japanese_punctuation:
                result.append({
                    "orig": char,
                    "kana": char,
                    "hira": char,
                    "hepburn": char,
                    "passport": char,
                    "kunrei": char,
                })
                i += 1
                continue
            
            # Handle kanji (may be multi-character compounds)
            if self._jconv.isRegion(char):
                # Try to find the longest matching kanji compound
                max_len = min(4, length - i)  # Max 4-character kanji compounds
                for l in range(max_len, 0, -1):
                    substring = text[i:i+l]
                    reading, matched_len = self._jconv.convert(substring, substring)
                    if matched_len > 0:
                        converted = self._iconv.convert(substring, reading)
                        result.append(converted)
                        i += matched_len
                        break
                else:
                    # No match found, treat as unknown kanji
                    result.append(self._iconv.convert(char, ""))
                    i += 1
                continue
            
            # Handle kana and other characters
            if K2.isRegion(char):  # Katakana
                converted = self._iconv.convert(char, char)
            elif H2.isRegion(char):  # Hiragana
                converted = self._iconv.convert(char, char)
            elif A2.isRegion(char):  # Alphanumeric
                converted = self._iconv.convert(char, char)
            elif Sym2.isRegion(char):  # Symbols
                converted = self._iconv.convert(char, char)
            else:  # Non-Japanese characters
                result.append({})
                i += 1
                continue

            result.append(converted)
            i += 1

        return result