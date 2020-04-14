import json
import pickle
import random
import re
import string

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.text import slugify

from ..models import Recipe, Tag, UserTag
from .scrape import recipe_data

User = get_user_model()


def add_recipes(jsonfile):
    recipe_list = json.loads(open(jsonfile).read())
    user = User.objects.get(username="admin")
    for rd in recipe_list:
        tag = Tag.objects.get_or_create(name_slug=slugify(rd["tag"]),
                                        defaults={"name": rd["tag"]})[0]
        recipe = Recipe(user=user,
                        title=rd["title"],
                        quantity_text=rd["quantity"],
                        ingredients_text=rd["ingredients"],
                        instructions_text=rd["instructions"])
        try:
            recipe.save()
        except IntegrityError:
            print(f"Duplicate title {recipe.title}")
            suffix = "".join(random.sample(string.ascii_letters, 3))
            recipe.title += f" {suffix}"
            print(f"Replaced title with {recipe.title}")
            recipe.save()
        ut = UserTag(tag=tag, user=user, recipe=recipe)
        ut.save()

recipe_title = re.compile(r'(?<=RECIPE )([A-ZÂÀÉÛ -]+)([,\(\n\r])')
def find_related():
    count = 0
    for recipe in Recipe.objects.all():
        q_results = recipe_title.findall(recipe.quantity_text.upper())
        ing_results = recipe_title.findall(recipe.ingredients_text.upper())
        slugs = ([slugify(t[0]) for t in q_results] + 
                 [slugify(t[0]) for t in ing_results])
        related = Recipe.objects.filter(title_slug__in=slugs)
        if related:
            recipe.see_also.add(*related)
            count += 1
    print(f"Found related recipes for {count} recipes")

def tag_ar(tagpath):
    admin = User.objects.get(username="admin")
    with open(tagpath, "rb") as tagfile:
        tag_dict = pickle.loads(tagfile.read())
    
    for tag_name, slugs in tag_dict.items():
        tag = Tag.objects.get_or_create(name_slug=slugify(tag_name), 
                                        defaults={"name": tag_name})[0]
        recipes = Recipe.objects.filter(title_slug__in=slugs)
        usertags = [UserTag(tag=tag, 
                            recipe=recipe,
                            user=admin) for recipe in recipes]
        UserTag.objects.bulk_create(usertags, ignore_conflicts=True)

def fix_romans():
    roman_re = r' (Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii)$' 
    romans = Recipe.objects.filter(title__regex=roman_re)
    for recipe in romans:
        recipe.title = re.sub(roman_re, lambda m: m[0].upper(), recipe.title)
        recipe.save()