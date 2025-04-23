# -*- coding: utf-8 -*-

try:
    unicode(0)
except NameError:
    # py3
    unicode = str
    unichr = chr


class Syllable(object):
    """Hangul syllable interface"""
    MIN = ord(u'가')
    MAX = ord(u'힣')

    def __init__(self, char=None, code=None):
        if char is None and code is None:
            raise TypeError('__init__ takes char or code as a keyword argument (not given)')
        if char is not None and code is not None:
            raise TypeError('__init__ takes char or code as a keyword argument (both given)')
        if char:
            code = ord(char)
        if not self.MIN <= code <= self.MAX:
            raise TypeError('__init__ expected Hangul syllable but {0} not in [{1}..{2}]'.format(code, self.MIN, self.MAX))
        self.code = code

    @property
    def index(self):
        return self.code - self.MIN

    @property
    def initial(self):
        return self.index // 588

    @property
    def vowel(self):
        return (self.index // 28) % 21

    @property
    def final(self):
        return self.index % 28

    @property
    def char(self):
        return unichr(self.code)

    def __unicode__(self):
        return self.char

    def __repr__(self):
        return u'''<Syllable({}({}),{}({}),{}({}),{}({}))>'''.format(
            self.code, self.char, self.initial, u'', self.vowel, u'', self.final, u'')


class Transliter(object):
    """General transliteration interface with enhanced Korean support"""

    def __init__(self, rule):
        print("USING ENHANCED KOREAN TRANSLITERATION")
        self.rule = rule
        # Define Korean punctuation and symbols that should remain unchanged
        self.korean_punctuation = [' ', '.', ',', '!', '?', '。', '，', '！', '？', '、', 
                                 '「', '」', '『', '』', '（', '）', '《', '》']

    def translit(self, text):
        """Translit Korean text to romanized text and return a list of (char, transliteration) pairs.
        
        Args:
            text: Unicode string containing Korean text
            
        Returns:
            List of tuples where each tuple is (original_char, transliteration)
        """
        result = []
        pre = (None, None)
        now = (None, None)
        
        for c in text:
            # Handle punctuation and spaces
            if c in self.korean_punctuation:
                if now[0] is not None:
                    # Process the current character before handling punctuation
                    out = self.rule(now, pre=pre, post=(c, None))
                    if out is not None:
                        result.append((now[0], out))
                # Add the punctuation as-is
                result.append((c, c))
                pre = (None, None)
                now = (None, None)
                continue
            
            try:
                post = (c, Syllable(c))
            except TypeError:
                # Not a Korean syllable
                post = (c, None)
                out = c  # Keep non-Korean characters as-is
                result.append((c, out))
                pre = now
                now = post
                continue

            if now[0] is not None:
                out = self.rule(now, pre=pre, post=post)
                if out is not None:
                    result.append((now[0], out))

            pre = now
            now = post

        # Process the last character if it exists
        if now[0] is not None:
            out = self.rule(now, pre=pre, post=(None, None))
            if out is not None:
                result.append((now[0], out))

        return result