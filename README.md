# For What

Multilingual Products, Tools for Reading/Listening

# How to Use, Download and Install

Menu.md

## Requeriments

python_version = "3.12"

# Transliteration issues

## Arabic

difference of one word, the first word does not have transliteration
second transliteration aligned with first word, and so on

## Japanese, Korean

Transliteration not being separated into chars

## Hindi

Words are being separated incorrectly and Transliteration is weird

## Chinese

There's punctuation in Transliteration
There should be punctuation only in the original text

## Russian

Weird with latin words in the middle

# Python Issues

Live serve not working
Relying on libraries for transliteration

import pypinyin
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as indic_transliterate
import pykakasi
from pyarabic.trans import custom_utf82latin
import jieba

# @ReadAloud Issues

Having to use ignore latin regex, which causes the detection language to be off, and manually select the language
which is annoying when you're reading 6 different languages in a day

# MoonReader Issues

Css for Arabic is not being properly applied - word and transliteration aligned
Same for Chinese - no unnecessary spaces between chinese characters

# ZayaLanguage

## Flashcards Issues

MD files into the static folder, weird handling, not being deployed by vercel

## Implement Transliteration page

npm libraries for handling transliteration?

lsof -i :8000

# 24/03/25

On Calibre/Ubuntu all the styles are fine, but on MoonReader, Android App, there are some errors:
Japanese, Korean: ok
Russian, Hindi: no margin-right applied to ruby tags
Arabic: Superposing words in rt tags, no margin-left on ruby
Chinese: justify: left, there's unnecessary space between ruby

What could MoonReader be possible ignoring for the rt tags to be intersecting with each other in arabic and hindi text where the font-size used for the epub to display the text are relatively small
transliteration text is bigger than the original text
Instead of
It prioritize ruby tags, doesn't respect rt tags

## On @voiceReadAloud they're better

Arabic, Chinese, Hindi: voiceReadAloud
Russian, Japanese, Korean: MoonReader

Other ebooks:
ReadEra: doesn't show rt tags
Prestigio: display rt tags inline
Google Ebooks: doesn't open the ebook

Issue: Harry Potter Chinese - Doesn't open the transliterated version on @voiceReadAloud, MoonReader version is weird

# 26/03/25

Versions: nl, db, trans, orig
no latin, dub: both translation and original, trans: original, translation, transliteration

Ebook Operations:
I have an ebook translated from calibre with content above original
I want to produce 2 additional versions
Transliteration: \_transliterated
no_original: remove the original content from the calibre translation

Since I'm updating metadata

[de, it, fr, ru, zh-ch, jp, hi, ar, ko, en, es ]

Я сказал ему, что он не умрет.
Но он продолжал идти.
Он сказал: «Вы должны знать об этом.
Это когда -нибудь случится ».
«И неудивительно, что Снуп устает».
«Он не так молод в собачьих годах».
«Вы можете представить его жизнь?»
«Он не просто собака».
«Он отличная собака».
«Выдающаяся собака».
«Подумай об этом.
Он ожидает ваших потребностей »,
«Предвидит ваши движения»,
«Держит вас в безопасности от опасности».
«Он тратит свою жизнь, представляя ваши потребности»
«Думая о том, что ты не видит».
«Может, он устал».
«Всегда заботиться о других».
«Может быть, однажды он закончится».
«Это может случиться».
И я помню в конце, он сказал: «Однажды»,
«Когда пришло время уйти, он пойдет».
«Вы не сможете помочь.
Подготовьтесь, это будет сложно ».
«Но это не будет конец вашей жизни».
Он имел в виду себя.
Сейчас…
Теперь я знаю, что он имел в виду себя.
Я умоляю присяжных иметь в виду, что эта история чрезвычайно субъективна.
Ни в коем случае не считается любой формой доказательства.
