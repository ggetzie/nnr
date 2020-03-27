import json
import pathlib
import re


CI_PATH = pathlib.Path("/usr/local/src/nnr/recipes/collect/data/cibook.txt")

weird_nums = {chr(178): "2",
              chr(179): "3",
              chr(185): "1"}

# re used to put ingredient amount and description on same line
# fixed = re.sub(r'(?<=\n)([0-9⁄-]+)\n', r'\1 ', book_txt)

def start_deleting(line):
    to_delete = {'WHY THIS RECIPE WORKS', 
                 'TEST KITCHEN TIP'}
    return any([td in line for td in to_delete])

def stop_deleting(line):
    return (not start_deleting(line)) and line.isupper()

def delete_extra(booklines):
    keep = True
    outlines = []
    for line in booklines:
        if keep:
            if start_deleting(line):
                keep = False
                continue
            else:
                outlines.append(line)
        else:
            if stop_deleting(line):
                keep = True
                outlines.append(line)
            else:
                continue
    return outlines

def remove_dupes(booklines):
    last_line = ""
    outlines = []
    for line in booklines:
        if line == last_line:
            continue
        else:
            outlines.append(line)
            last_line = line
    return outlines

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