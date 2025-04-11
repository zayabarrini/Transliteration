from setuptools import setup, find_packages

setup(
    name="transliteration-tools",  # Unique name for PyPI
    version="0.1",
    packages=find_packages(),  # Automatically discover packages
    install_requires=[],       # Add dependencies if needed
    python_requires=">=3.6",
)

install_requires=[
    'pypinyin',
    'hangul-romanize',
    'indic-transliteration',
    'pykakasi',
    'pyarabic',
    'jieba',
    'transliterate'
]