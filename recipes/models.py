from django.db import models
from django.conf import settings
from django.contrib.postgres.search import SearchVectorField
from django.core.cache import cache
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from .utils import sortify

import datetime
import markdown
import string

import logging
logger = logging.getLogger(__name__)

def setup_lettercounts():            
    nums = LetterCount.objects.get_or_create(letter="0-9", 
                                            defaults={"quantity":0})[0]
    nums.save()
    for letter in string.ascii_uppercase:
        lc = LetterCount.objects.get_or_create(letter=letter, 
                                               defaults={"quantity":0})[0]
        lc.save()
    for r in Recipe.objects.all():
        r.save()    


def make_detail_key(slug):
    return f"{slug}-detail"

class LetterCount(models.Model):
    letter = models.CharField(_("Letter"), default="", max_length=3, 
                              unique=True)
    quantity = models.IntegerField(_("Quantity"), default=0)

    class Meta:
        ordering = ["letter"]

    def __str__(self):
        return f"{self.quantity} of {self.letter}"    


INGREDIENTS_HELP = _("Tip: list ingredients in the order they are used")
class Recipe(models.Model):
    title = models.CharField(_("Title"), max_length=150)
    title_slug = models.SlugField(_("Title Slug"), max_length=150, 
                                  unique=True)
    ingredients_text = models.TextField(_("Ingredients"), 
                                        help_text=INGREDIENTS_HELP)
    ingredients_html = models.TextField(_("Ingredients HTML"))
    instructions_text = models.TextField(_("Instructions"))
    instructions_html = models.TextField(_("Instructions HTML"))
    quantity_text = models.CharField(_("Yield"), 
                                     max_length=200, 
                                     default="")
    quantity_html = models.CharField(_("Quantity HTML"), 
                                     max_length=400, 
                                     default="")
    tags = models.ManyToManyField("Tag", through="UserTag")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.SET_NULL,
                             null=True,
                             related_name="author")
    first_letter = models.CharField(_("First Letter"), max_length=3, 
                                    default="")
    sort_title = models.CharField(_("Sort Title"), max_length=150, 
                                  default="")
    created = models.DateField(_("Date Created"), auto_now_add=True)
    created_dt = models.DateTimeField(_("Datetime Created"), auto_now_add=True, 
                                      blank=True, null=True)
    featured = models.BooleanField(_("Recipe of the Day"), default=False)
    last_featured = models.DateField(_("Last Featured"), 
                                     default=datetime.date(year=1970, 
                                                           month=1, 
                                                           day=1))
    see_also = models.ManyToManyField("self")
    search_vector = SearchVectorField(null=True)

    class Meta:
        ordering = ["sort_title"]

    def save(self, *args, **kwargs):
        self.ingredients_html = markdown.markdown(self.ingredients_text)
        self.instructions_html = markdown.markdown(self.instructions_text)
        self.quantity_html = markdown.markdown(self.quantity_text)
        self.title_slug = slugify(self.title)
        if self.title.isupper():
            self.title = self.title.title()
            self.title = self.title.replace("’S", "’s")
            self.title = self.title.replace("'S", "'s")
        self.first_letter, self.sort_title = sortify(self.title_slug)
        lc, created = LetterCount.objects.get_or_create(letter=self.first_letter,
                                                        defaults={"quantity": 1})
        if not created:
            lc.quantity += 1
            logger.info(f"Deleting key {self.detail_key}")
            cache.delete(self.detail_key)
        lc.save()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("recipes:recipe_detail", kwargs={"slug": self.title_slug})

    @property
    def detail_key(self):
        # key for caching the detail of this recipe
        return f"{self.title_slug}-detail"

    def delete(self, *args, **kwargs):
        cache.delete(self.detail_key)
        return super().delete(*args, **kwargs)

    def text_only(self):
        return f"""{self.title}

Ingredients
{strip_tags(self.ingredients_html)}

Instructions
{strip_tags(self.instructions_html)}"""
    
    def __str__(self):
        if len(self.title) < 15:
            return self.title
        else:
            return f"{self.title[:15]}..."        


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=100)
    name_slug = models.SlugField(_("slug"), max_length=100, unique=True)

    class Meta:
        ordering = ["name_slug"]

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

class UserTag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name="owner")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'tag', 'recipe'],
                                               name="unique_user_tag")]

    def __str__(self):
        return f"{self.recipe} - {self.user} - {self.tag}"            

    # def save(self, *args, **kwargs):
    #     logger.info(f"Deleting tags cache: {self.recipe.tags_key}")
    #     cache.delete(self.recipe.tags_key)
    #     return super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):
    #     logger.info(f"Deleting tags cache: {self.recipe.tags_key}")
    #     cache.delete(self.recipe.tags_key)
    #     return super().delete(*args, **kwargs)

RATING_CHOICES = ((1, "⭐"),
                  (2, "⭐⭐"),
                  (3, "⭐⭐⭐"),
                  (4, "⭐⭐⭐⭐"),
                  (5, "⭐⭐⭐⭐⭐"))

class RecipeRating(models.Model):
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(_("Rating"), choices=RATING_CHOICES)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["recipe", "user"],
                                              name="unique_recipe_rating")]
        ordering = ["user", "recipe__sort_title"]

    def __str__(self):
        return f"{self.user.username} rated {self.recipe} {self.rating} stars"