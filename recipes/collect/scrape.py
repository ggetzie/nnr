import requests
import time
from bs4 import BeautifulSoup

import pathlib
recipe_data = pathlib.Path("/usr/local/src/nnr/recipes/collect/data")
ar_categories = recipe_data / "ar_categories.txt"
ar_recipe_links = recipe_data / "ar_recipe_links.txt"
def get_recipe_links():
    categories = [l.strip() for l in open(ar_categories).readlines()]
    recipe_links = set()
    for category in categories:
        for page in range(1, 21):
            url = f"{category}?page={page}"
            response = requests.get(url)
            if response.status_code != 200: break
            soup = BeautifulSoup(response.text, "html.parser")
            links = {l.get("href") for l in soup.select('a[href^="https://www.allrecipes.com/recipe/"]')}
            # write only the recipes we haven't seen before
            with open(ar_recipe_links, "a") as outfile:
                out_links = links - recipe_links
                outfile.write("\n".join(out_links))
                outfile.write("\n")
            # add new links to list of ones we've seen
            recipe_links = recipe_links.union(links)
            print(f"Found {len(links)} at {url}")
            time.sleep(5)

def parse_recipe_page(page_text):
    soup = BeautifulSoup(page_text)
    ingredients = "\n".join([s.text for s in soup.select('[itemprop="recipeIngredient"]')])