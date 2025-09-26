# Using the CLI tool
pipenv run clean-spelling /home/zaya/Downloads/ITA2025.md -o /home/zaya/Downloads/ITA2025_cleaned.md

# Or directly with Python
pipenv run python3 -m spelling.cli /home/zaya/Downloads/ITA2025.md

Process: 
Download Provas.pdf from Poliedro Resolve
Online converter to docx: https://www.ilovepdf.com/pt
pandoc: convert docx to .md
run spelling checker
pandoc: convert to epub
split Processor
open in calibre: translation to de, ru, fr, etc
remove original


Combined Operation (One Step)
If you want to do both in one operation:

Find: \s*([.,!?;:])\s*
Replace: $1

Fix punctuation on VSCode:
Remove Spaces Before Punctuation
Find: \s+([.,!?;:])
Replace: $1

Add Spaces After Punctuation
Find: ([.,!?;:])(?!\s)(?=[^\s])
Replace: $1

This will add a single space after punctuation marks that are not already followed by a space.



pipenv run python3 -m spelling.cli /home/zaya/Downloads/ime-2025-provas/IME-2025.md
