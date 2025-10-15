#!/usr/bin/env python3
import argparse
from pathlib import Path
from .spell_cleaner import MDSpellCleaner


def main():
    parser = argparse.ArgumentParser(description="Clean spelling mistakes in markdown files")
    parser.add_argument("input_file", help="Input markdown file to clean")
    parser.add_argument("-o", "--output", help="Output file (optional)")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")

    args = parser.parse_args()

    cleaner = MDSpellCleaner()
    cleaner.clean_markdown_file(args.input_file, args.output)


if __name__ == "__main__":
    main()
