from setuptools import setup, find_packages

setup(
    name="spelling",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyspellchecker>=0.7.0",
        "spacy>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "clean-spelling=spelling.cli:main",
        ],
    },
    python_requires=">=3.8",
)
