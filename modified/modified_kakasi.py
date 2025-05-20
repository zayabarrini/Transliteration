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
    from .kanji import JConv
    from .properties import Ch
    from .scripts import A2, H2, IConv, K2, Sym2
except ImportError:
    from pykakasi.kanji import JConv
    from pykakasi.properties import Ch
    from pykakasi.scripts import A2, H2, IConv, K2, Sym2


class PyKakasiException(Exception):
    pass


class UnknownCharacterException(PyKakasiException):
    pass


class _TYPE(enum.Enum):
    KANJI = 1
    KANA = 2
    HIRAGANA = 3
    SYMBOL = 4
    ALPHA = 5


class _ACTION(enum.Enum):
    NOBUFOUT_AND_OUTPUT_CURRENT_AND_NEXT = 1
    BUFOUT_AND_SKIP_CURRENT = 2
    BUFOUT_AND_OUTPUT_CURRENT_AND_NEXT = 3
    PUT_AND_NEXT = 4
    BUFOUT_AND_NEXT = 5
    DO_NOTHING = 6


class Kakasi:
    """Simplified Kakasi conversion class with improved non-Japanese handling."""

    def __init__(self):
        self._jconv = JConv()
        self._iconv = IConv()
        self.japanese_punctuation = [' ', '。', '、', '！', '？', '「', '」', '『', '』', '（', '）', '・']
        self.non_japanese_pattern = re.compile(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\s]')

    def is_japanese(self, text: str) -> bool:
        return not self.non_japanese_pattern.search(text)

    @classmethod
    def normalize(cls, text):
        return jaconv.normalize(text)

    def convert(self, text: str) -> List[Dict[str, str]]:
        if not text:
            return [{
                "orig": "", "kana": "", "hira": "",
                "hepburn": "", "passport": "", "kunrei": ""
            }]

        result = []
        original_text = ""
        kana_text = ""
        i = 0
        prev_type = _TYPE.KANJI
        action_flag: _ACTION

        while i < len(text):
            char = text[i]
            
            # Skip non-Japanese characters (except whitespace and punctuation)
            if (self.non_japanese_pattern.match(char) and 
                char not in self.japanese_punctuation):
                i += 1
                continue
            
            # Handle punctuation first
            if char in self.japanese_punctuation:
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                    original_text = ""
                    kana_text = ""
                result.append({
                    "orig": char, "kana": char, "hira": char,
                    "hepburn": char, "passport": char, "kunrei": char
                })
                prev_type = _TYPE.SYMBOL
                i += 1
                continue
            
            # Main processing logic
            if char in Ch.endmark:
                prev_type = _TYPE.SYMBOL
                action_flag = _ACTION.BUFOUT_AND_NEXT
            elif char in Ch.long_symbols:
                action_flag = _ACTION.PUT_AND_NEXT
            elif K2.isRegion(char):
                if prev_type == _TYPE.KANA:
                    action_flag = _ACTION.PUT_AND_NEXT
                else:
                    action_flag = _ACTION.BUFOUT_AND_NEXT
                prev_type = _TYPE.KANA
            elif H2.isRegion(char):
                if prev_type == _TYPE.HIRAGANA:
                    action_flag = _ACTION.PUT_AND_NEXT
                else:
                    action_flag = _ACTION.BUFOUT_AND_NEXT
                prev_type = _TYPE.HIRAGANA
            elif A2.isRegion(char):
                if prev_type == _TYPE.ALPHA:
                    action_flag = _ACTION.PUT_AND_NEXT
                else:
                    action_flag = _ACTION.BUFOUT_AND_NEXT
                prev_type = _TYPE.ALPHA
            elif Sym2.isRegion(char):
                if prev_type != _TYPE.SYMBOL:
                    action_flag = _ACTION.BUFOUT_AND_NEXT
                else:
                    action_flag = _ACTION.NOBUFOUT_AND_OUTPUT_CURRENT_AND_NEXT
                prev_type = _TYPE.SYMBOL
            elif self._jconv.isRegion(char):
                # Process single kanji character (no compound matching)
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                reading, matched_len = self._jconv.convert(char, char)
                if matched_len > 0:
                    original_text = char
                    kana_text = reading
                else:
                    original_text = char
                    kana_text = ""
                i += 1
                action_flag = _ACTION.DO_NOTHING
                prev_type = _TYPE.KANJI
                continue
            elif 0xF000 <= ord(char) <= 0xFFFD or 0x10000 <= ord(char) <= 0x10FFFD:
                # PUA: ignore and drop
                prev_type = _TYPE.SYMBOL
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                    original_text = ""
                    kana_text = ""
                i += 1
                action_flag = _ACTION.DO_NOTHING
            else:
                # Non-Japanese characters we didn't skip earlier
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                result.append(self._iconv.convert(char, ""))
                i += 1
                action_flag = _ACTION.DO_NOTHING

            # Action handling
            if action_flag == _ACTION.BUFOUT_AND_OUTPUT_CURRENT_AND_NEXT:
                original_text += char
                kana_text += char
                result.append(self._iconv.convert(original_text, kana_text))
                original_text = ""
                kana_text = ""
                i += 1
            elif action_flag == _ACTION.BUFOUT_AND_NEXT:
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                original_text = char
                kana_text = char
                i += 1
            elif action_flag == _ACTION.PUT_AND_NEXT:
                original_text += char
                kana_text += char
                i += 1
            elif action_flag == _ACTION.NOBUFOUT_AND_OUTPUT_CURRENT_AND_NEXT:
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                result.append(self._iconv.convert(char, char))
                original_text = ""
                kana_text = ""
                i += 1
            elif action_flag == _ACTION.BUFOUT_AND_SKIP_CURRENT:
                if len(original_text) > 0:
                    result.append(self._iconv.convert(original_text, kana_text))
                original_text = ""
                kana_text = ""
                i += 1
            elif action_flag == _ACTION.DO_NOTHING:
                pass

        # Add any remaining buffered text
        if len(original_text) > 0:
            result.append(self._iconv.convert(original_text, kana_text))

        return result