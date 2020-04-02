import json
import random
import string

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.text import slugify

from ..models import Recipe, Tag, UserTag

User = get_user_model()

def add_recipes(jsonfile):
    recipe_list = json.loads(open(jsonfile).read())
    user = User.objects.get(username="gabe")
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