from pypinyin import pinyin, Style
import re


def add_pinyin_to_text(text):
    # Regular expression to match Chinese sentences
    chinese_pattern = re.compile(r"[\u4e00-\u9fff，。？！：；、“”‘’（）《》〈〉]+")

    def convert(match):
        sentence = match.group()
        pinyin_text = pinyin(sentence, style=Style.TONE3)
        pinyin_with_spaces = " ".join(word[0] for word in pinyin_text)
        return f"{pinyin_with_spaces}\n{sentence}\n"

        # pinyin_with_spaces = ' '.join(word[0] for word in pinyin_text)
        # return f'[{pinyin_with_spaces}] {chars}'

    return chinese_pattern.sub(convert, text)


def process_markdown_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    content_with_pinyin = add_pinyin_to_text(content)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content_with_pinyin)


if __name__ == "__main__":
    process_markdown_file(
        "/home/zaya/Downloads/input.md", "/home/zaya/Downloads/output_with_pinyin.md"
    )
