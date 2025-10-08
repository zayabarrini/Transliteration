pipenv run python pdf2latex.py ../documentation/sample.pdf -o output.tex

pipenv run python pdf2latex.py /home/zaya/Downloads/EQED_20201.pdf -o /home/zaya/Downloads/output.tex

pipenv run python pdf2latex.py ../documentation/sample.pdf -o simple.tex --simple-layout

# Mathpix $
pipenv run python pdf2latex.py ../documentation/math_paper.pdf -o paper.tex \
    --mathpix-id YOUR_APP_ID --mathpix-key YOUR_APP_KEY

