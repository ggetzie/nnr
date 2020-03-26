import json
import pathlib

CI_PATH = "/home/gabe/Dropbox/books/The Editors at America's Test Kitchen/The Cook's Illustrated Cookbook (657)"

def ci_book(filepath):
    with open(filepath)as book:
        for line in book:
            pass