# Products

## Web/Python

- 5008: Translator by word - Japanese (webJapaneseColor-coded)
  - Transliteration
    Color Coding Legend:
    Subject, Topic, Object, Location, Verb, Description, Noun, Verb, Adjective, Particle, Polite, Humble
    Show Romanji, Show Translation, Show Syntax Role

- 5010: Translator by word - Japanese (webJapaneseColor-coded-MeCab)
  - Nouns, Verbs, い-Adjectives, な-Adjectives, Particles, Adverbs, Other
  - POS, Role, Category, Particle, Verb form

## Transliteration

- Web: py, template, styles
- Epub2json.py

## Svelte

- JapaneseReader

that reads a json file
Can we implement a JapaneseReader.svelte

ZayasLanguage + backend py -> migration
Payments and login

# JapaneseReader.svelte

Can we build a JapaneseReader.svelte that reads a json file containing the sections, in each section a list of paragraphs with the english version and the japanese version
export let jsonPath: string =
"/json/ja/epub_content_web-Downton-abbey.json";
Can we use pykakasi or MeCab to get data about syntax, etc?

# epub2jsonJa.py

Let's create a epub2jsonJa.py containing the sections, in each section a list of paragraphs with the english version and the japanese version
In the end we'd produce the epub transliteration and the .json for use in the web

This is the epub structure:
Each split file contains only one section, then we nest the paragraphs contents into each section:

/home/zaya/Downloads/Zayas/ZayasBooks/t/Downton-Abbey_Cinema-Screenplays-db-ja
❯ tree -L 3
.
├── content.opf
├── EPUB
│   ├── media
│   │   └── bing23.png
│   ├── nav_split_000.xhtml
│   ├── nav_split_001.xhtml
│   └── text
│   ├── ch001_split_000.xhtml
│   ├── ch001_split_001.xhtml
│   ├── ch002_split_000.xhtml
│   ├── ch002_split_001.xhtml
│   ├── ch003_split_000.xhtml
│   ├── ch003_split_001.xhtml
│   ├── ch004_split_000.xhtml
...
│   ├── ch057_split_000.xhtml
│   ├── ch057_split_001.xhtml
│   ├── ch057_split_002.xhtml
│   ├── cover.xhtml
│   ├── title_page_split_000.xhtml
│   ├── title_page_split_001.xhtml
│   ├── title_page_split_002.xhtml
│   └── title_page_split_003.xhtml
├── META-INF
│   └── container.xml
├── mimetype
├── page_styles.css
├── stylesheet.css
└── toc.ncx

5 directories, 133 files

<section id="downton-abbey-s01e02-river-xvid----" class="titlepage">
<h1 class="main" id="calibre_pb_1">Downton Abbey S01E02 River-Xvid - -</h1>
<p class="author" dir="ltr" lang="ja" style="color:#00557f">WWW.MY-SUBS.COAdriano_CSI によって可能になった字幕</p><p class="author">WWW.MY-SUBS.COSubtitle made possible by Adriano_CSI</p>
<p class="author" dir="ltr" lang="ja" style="color:#00557f">さあ、奥様。</p><p class="author">Here we are, ma’am.</p>
<p class="author" dir="ltr" lang="ja" style="color:#00557f">クローリーハウス。</p><p class="author">Crawley House.</p>
<p class="author" dir="ltr" lang="ja" style="color:#00557f">良くも悪くも。</p><p class="author">For good or ill.</p>
<p class="author" dir="ltr" lang="ja" style="color:#00557f">理由はまだわかりません</p><p class="author">I still don’t see why</p>

Of course! This is an excellent approach for creating a visual learning tool. Here's a comprehensive composite marker system designed specifically for Japanese analysis, perfect for color-coding.

# Grammar

## Comprehensive Japanese Marker System

```python
# Composite Marker Structure for Japanese
result.append({
    "word": word,
    "transliteration": romaji_word,
    "translation": translation,
    "syntax_role": "X",           # Primary grammatical function
    "part_of_speech": "Unknown",   # Word category
    "particle_type": "None",       # Specific particle classification
    "verb_form": "None",           # Verb conjugation details
    "honorific_level": "Neutral",  # Politeness level
    "is_punctuation": is_punctuation(word),
    "semantic_category": "General", # Meaning-based category
})
```

## Detailed Category Breakdown

### 1. **Syntax Roles** (Sentence Function)

```python
syntax_roles = {
    "SUBJECT": "Subject (marked by が, は)",
    "TOPIC": "Topic (marked by は)",
    "DIRECT_OBJECT": "Direct object (marked by を)",
    "INDIRECT_OBJECT": "Indirect object (marked by に)",
    "LOCATION": "Location (marked by で, に)",
    "TIME": "Time expression",
    "DIRECTION": "Direction (marked by に, へ)",
    "POSSESSOR": "Possessor (marked by の)",
    "VERB": "Main predicate",
    "ADVERBIAL": "Adverbial modifier",
    "SENTENCE_ENDER": "Final particle",
    "CONJUNCTION": "Connector between clauses"
}
```

### 2. **Parts of Speech**

```python
parts_of_speech = {
    "NOUN": "名詞",
    "PRONOUN": "代名詞",
    "VERB": "動詞",
    "ADJECTIVE_I": "い-adjective",
    "ADJECTIVE_NA": "な-adjective",
    "ADVERB": "副詞",
    "PARTICLE": "助詞",
    "AUXILIARY_VERB": "助動詞",
    "CONJUNCTION": "接続詞",
    "INTERJECTION": "感動詞",
    "PRENOUN_ADJECTIVE": "連体詞",
    "COUNTER": "助数詞",
    "NUMERAL": "数詞"
}
```

### 3. **Particle Types** (Detailed)

```python
particle_types = {
    "CASE_GA": "Subject marker が",
    "CASE_WA": "Topic marker は",
    "CASE_O": "Object marker を",
    "CASE_NI": "Target/location に",
    "CASE_DE": "Location/means で",
    "CASE_E": "Direction へ",
    "CASE_TO": "With/and と",
    "CASE_KARA": "From から",
    "CASE_MADE": "Until まで",
    "CASE_YORI": "Than/from より",
    "CASE_NO": "Possession の",
    "CONNECTIVE_TE": "て-form connector",
    "CONNECTIVE_BA": "Conditional ば",
    "FINAL_KA": "Question か",
    "FINAL_NE": "Seek agreement ね",
    "FINAL_YO": "Emphasis よ",
    "FINAL_WA": "Feminine emphasis わ"
}
```

### 4. **Verb Forms**

```python
verb_forms = {
    "DICTIONARY": "Plain form (辞書形)",
    "MASU_PRESENT": "Polite non-past ます",
    "MASU_PAST": "Polite past ました",
    "MASU_NEGATIVE": "Polite negative ません",
    "TE_FORM": "て-form",
    "TA_FORM": "Past plain た-form",
    "NAI_FORM": "Negative plain ない",
    "VOLITIONAL": "Let's form よう",
    "IMPERATIVE": "Command form",
    "CONDITIONAL_BA": "Conditional ば-form",
    "CONDITIONAL_TARA": "Conditional たら",
    "POTENTIAL": "Can do られる",
    "PASSIVE": "Passive られる",
    "CAUSATIVE": "Make do させる",
    "CAUSATIVE_PASSIVE": "Causative-passive"
}
```

### 5. **Honorific Levels**

```python
honorific_levels = {
    "PLAIN": "Casual speech",
    "POLITE": "Standard polite (です/ます)",
    "HUMBLE": "Humble (謙譲語)",
    "RESPECTFUL": "Respectful (尊敬語)",
    "HONORIFIC": "Formal honorific"
}
```

### 6. **Semantic Categories**

```python
semantic_categories = {
    "PERSON": "People, names, titles",
    "LOCATION": "Places, directions",
    "TIME": "Time expressions",
    "OBJECT": "Physical objects",
    "ACTION": "Actions, events",
    "DESCRIPTION": "Qualities, states",
    "QUANTITY": "Numbers, amounts",
    "QUESTION": "Question words",
    "NEGATION": "Negative expressions",
    "EMOTION": "Feelings, emotions"
}
```

## Complete Implementation Example

```python
def analyze_japanese_word(word):
    # Your existing analysis logic here
    # Then return comprehensive markers:

    return {
        "word": "食べました",
        "transliteration": "tabemashita",
        "translation": "ate",
        "syntax_role": "VERB",
        "part_of_speech": "VERB",
        "particle_type": "None",
        "verb_form": "MASU_PAST",
        "honorific_level": "POLITE",
        "is_punctuation": False,
        "semantic_category": "ACTION"
    }

def analyze_particle(word):
    return {
        "word": "が",
        "transliteration": "ga",
        "translation": "(subject marker)",
        "syntax_role": "SUBJECT",
        "part_of_speech": "PARTICLE",
        "particle_type": "CASE_GA",
        "verb_form": "None",
        "honorific_level": "Neutral",
        "is_punctuation": False,
        "semantic_category": "General"
    }
```

part_of_speech
particle_type
verb_form
honorific_level

## Suggested Color Scheme

- **Syntax Roles**: Blues (subject=dark blue, object=medium blue, etc.)
- **Particles**: Oranges/Yellows (case particles=orange, conjunctive=yellow)
- **Verbs**: Reds (different forms as red shades)
- **Nouns**: Greens (people=light green, objects=dark green)
- **Adjectives**: Purples (い-adjective=purple, な-adjective=violet)
- **Honorifics**: Golds (polite=light gold, humble=dark gold)

This system gives you granular control for color-coding while maintaining clear linguistic categories specific to Japanese's structure. You can collapse categories if you need simpler coloring, but this provides maximum analytical power.
