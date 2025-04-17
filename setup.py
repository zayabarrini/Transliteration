from setuptools import setup, find_packages

setup(
    name="transliteration-tools",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pypinyin',
        'hangul-romanize',
        'indic-transliteration',
        'pykakasi',
        'pyarabic',
        'jieba',
        'transliterate'
    ],
    python_requires=">=3.6",
)