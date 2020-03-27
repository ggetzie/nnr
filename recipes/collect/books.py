import json
import pathlib
import re


CI_PATH = pathlib.Path("/usr/local/src/nnr/recipes/collect/data/cibook.txt")

weird_nums = {chr(178): "2",
              chr(179): "3",
              chr(185): "1"}

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


def ci_book(filepath):
    with open(filepath) as book:
        for line in book:
            pass