import json
import pathlib
import re


CI_PATH = pathlib.Path("/usr/local/src/nnr/recipes/collect/data/cibook.txt")

weird_nums = {chr(178): "2",
              chr(179): "3",
              chr(185): "1"}

# re used to put ingredient amount and description on same line
# fixed = re.sub(r'(?<=\n)([0-9⁄-]+)\n', r'\1 ', booktxt)         

def fix_weird_nums(book):
    out=""
    for i, c in enumerate(book):
        if c in weird_nums:
            if book[i-1].isdigit():
                out += f"-{weird_nums[c]}"
            else:
                out += weird_nums[c]
        else:
            out += c
    return out

def fix_ingredients(bookfile):
    booklines = [l.strip() for l in open("bookfile")]


def ci_book(filepath):
    with open(filepath) as book:
        for line in book:
            pass