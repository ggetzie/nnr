import pathlib

import subprocess
import time

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from ..models import Recipe, Tag, UserTag

from bs4 import BeautifulSoup
import requests

User = get_user_model()
admin = User.objects.get(username="admin")
ar_tag = Tag.objects.get(name="ar")

last_recipe = "https://www.allrecipes.com/recipe/23788/bacon-quiche-tarts/"

recipe_data = pathlib.Path("/usr/local/src/nnr/recipes/collect/data")
ar_categories = recipe_data / "ar_categories.txt"
ar_recipe_links = recipe_data / "ar_recipe_links.txt"
ar_remaining = recipe_data / "ar_remaining.txt"

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

def get_page(url):
    print(f"getting {url}")
    res = subprocess.check_output(["/opt/google/chrome/chrome",
                                    "--headless", "--disable-gpu",
                                    "--dump-dom", url])
    return res

def parse_recipe_page(page_text):
    print("parsing page")
    soup = BeautifulSoup(page_text, "html.parser")
    ingredient_list = soup.select('[itemprop="recipeIngredient"]')
    instruction_list = soup.select('ol[itemprop="recipeInstructions"]')
    quantity_list = soup.select(".servings-count")
    title_list = soup.select('h1[itemprop="name"]')
    if all([title_list,
            quantity_list,
            ingredient_list,
            instruction_list]):
        ingredients = "\n".join([s.text + "  " for s in ingredient_list])
        quantity = quantity_list[0].text
        instructions = "".join([s.text for s in instruction_list])
        title = title_list[0].text
        return Recipe(quantity_text = quantity,
                    ingredients_text = ingredients,
                    instructions_text = instructions,
                    title = title,
                    user = admin)
    else:
        return None

def get_recipes():
    with open(ar_remaining) as recipe_file:
        urls = [l.strip() for l in recipe_file]
    for i, url in enumerate(urls):
        res = get_page(url)
        recipe = parse_recipe_page(res)
        if not recipe:
            print(f"Could not parse page at {url}")
            continue
        try:
            recipe.save()
            ut = UserTag(recipe=recipe, user=admin, tag=ar_tag)
            ut.save()
            print(f"Saved recipe {recipe.title}")
        except IntegrityError:
            # duplicate recipe
            pass
        with open(ar_remaining, "w") as remaining_file:
            try:
                remaining_file.write("\n".join(urls[i+1:]))
            except IndexError:
                # end of list
                pass
        time.sleep(5)
    
