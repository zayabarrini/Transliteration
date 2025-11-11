/home/zaya/Downloads/Zayas/ZayasTransliteration/start-chinese-session.sh
./start-chinese-session.sh

1 terminal window with 4 splits:

1,2 and 3:
pwd: /home/zaya/Downloads/Zayas/ZayasTransliteration
Start: Chinese Syntax Analyzer
cd transliteration, pipenv shell, python3 -m web.webChineseColor-coded

4:
pwd: /home/zaya/Downloads/Zayas/zayas-grammar-db
Start: grammar-db
cd grammar-db
./start.sh

start Google Translate on chrome with chinese source select
open Calibre: Chinese-trans-css.epub

- Since for chinese there's data to include the syntax and pos along with the transliteration and translation,
  maybe use spans with rt to compose for chinese:

```
  "word": word,
  "transliteration": pinyin_word,
  "translation": translation,
  "syntax": syntax,
  "pos": pos,
```
