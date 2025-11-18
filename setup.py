from setuptools import find_packages, setup

setup(
    name="transliteration-tools",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pypinyin",
        "hangul-romanize",
        "indic-transliteration",
        "pykakasi",
        "pyarabic",
        "jieba",
        "transliterate",
        "ebooklib",
        "beautifulsoup4",
        "chardet",
        # Add other essential dependencies here
    ],
    entry_points={
        'console_scripts': [
            'epubManager=transliteration.epubManager:main',
        ],
    },
    python_requires=">=3.6",
)