import json
import pathlib
import queue
import re

CI_PATH = pathlib.Path("/usr/local/src/nnr/recipes/collect/data/cibook.txt")

weird_nums = {chr(178): "2",
              chr(179): "3",
              chr(185): "1"}

# re used to put ingredient amount and description on same line
# fixed = re.sub(r'(?<=\n)([0-9⁄–-]+)\n', r'\1 ', book_txt)

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

def tag_quantities(bookpath):
    booklines = [l.strip() for l in open(bookpath)]
    outlines = []
    last_line = ""
    for line in booklines:
        if ((line.startswith("SERVES") or 
             line.startswith("MAKES")) and not
            last_line.startswith("#quantity")):
            outlines.append("#quantity")
            outlines.append(line)
        else:
            outlines.append(line)
        last_line = line
    out_txt = "\n".join([l+"  " for l in outlines])
    with open("data/cibook_out.txt", "w") as outfile:
        outfile.write(out_txt)
    return outlines

def tag_title_end(booklines, start_line):
    outlines = []
    last_line = booklines[start_line]
    for line in booklines[start_line+1:]:
        if line == "#quantity":
            outlines.append("#end")
            outlines.append("#title")
            outlines.append(last_line)
        else:
            outlines.append(last_line)
        last_line = line
    outlines.append(last_line)
    return booklines[:start_line] + outlines

def tag_ingredients(booklines, start_line):
    outlines = []
    after_q = 0
    for line in booklines[start_line:]:
        if line == "#quantity":
            after_q += 1
            outlines.append(line)
        elif after_q == 1:
            after_q += 1
            outlines.append(line)
        elif after_q == 2:
            outlines.append("#ingredients")
            outlines.append(line)
            after_q = 0
        else:
            outlines.append(line)
    return booklines[:start_line] + outlines

def tag_instructions(booklines, start_line):
    outlines = []
    for line in booklines[start_line:]:
        if line.startswith("1."):
            outlines.append("#instructions")
        outlines.append(line)
    return booklines[:start_line] + outlines

def write_book(outlines):
    out_txt = "\n".join([l + "  " for l in outlines])
    with open("data/cibook_out.txt", "w") as outfile:
        outfile.write(out_txt)

def read_book():
    return [l.strip() for l in open("data/cibook.txt")]

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


def parse_ci(filepath):
    with open(filepath) as book:
        booklines = [l.strip() for l in book]
    recipes = []
    state = ""
    title = ""
    quantity = ""
    ingredients = []
    instructions = []
    tag = ""
    print(len(booklines))
    for i, line in enumerate(booklines):
        if line and line[0] == "#":
            state = line[1:]
            if not state == "end":
                continue
        if state == "title":
            title = line
        elif state == "section":
            tag = line
        elif state == "quantity":
            quantity = line
        elif state == "ingredients":
            ingredients.append(line + "  ")
        elif state == "instructions":
            instructions.append(line + "  ")
        elif state == "end":
            if title and ingredients and instructions:
                recipes.append({
                    "title": title,
                    "quantity": quantity,
                    "ingredients": "\n".join(ingredients),
                    "instructions": "\n".join(instructions),
                    "tag": tag
                })
            title = ""
            quantity = ""
            ingredients = []
            instructions = []
        else:
            print(f"Undefined state {state} @ line {i}")
    with open("data/cibook.json", "w") as outfile:
        outfile.write(json.dumps(recipes))
        print("recipes saved")
    return recipes
