from dateutil.relativedelta import relativedelta

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from .utils import sortify

import datetime
import markdown
import string

def next_year():
    today = datetime.date.today()
    return today + relativedelta(years=1)

def get_basic_plan():
    plan, created =  PaymentPlan.objects.get_or_create(name_slug="basic", 
                                                       defaults={"name": "Basic"})
    return plan.id

def setup_lettercounts():            
    nums = LetterCount(letter="0-9", quantity=0)
    nums.save()
    for letter in string.ascii_uppercase:
        lc = LetterCount(letter=letter, quantity=0)
        lc.save()
    for r in Recipe.objects.all():
        r.save()    


class LetterCount(models.Model):
    letter = models.CharField(_("Letter"), default="", max_length=3, 
                              unique=True)
    quantity = models.IntegerField(_("Quantity"), default=0)

    class Meta:
        ordering = ["letter"]

    def __str__(self):
        return f"{self.quantity} of {self.letter}"    
                            

class Recipe(models.Model):
    title = models.CharField(_("Title"), max_length=150)
    title_slug = models.SlugField(_("Title Slug"), max_length=150, 
                                  unique=True)
    ingredients_text = models.TextField(_("Ingredients"))
    ingredients_html = models.TextField(_("Ingredients HTML"))
    instructions_text = models.TextField(_("Instructions"))
    instructions_html = models.TextField(_("Instructions HTML"))
    tags = models.ManyToManyField("Tag", through="UserTag")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.SET_NULL,
                             null=True)
    first_letter = models.CharField(_("First Letter"), max_length=3, 
                                    default="")
    sort_title = models.CharField(_("Sort Title"), max_length=150, 
                                  default="")

    class Meta:
        ordering = ["sort_title"]

    def save(self, *args, **kwargs):
        self.ingredients_html = markdown.markdown(self.ingredients_text)
        self.instructions_html = markdown.markdown(self.instructions_text)
        self.title_slug = slugify(self.title)
        self.first_letter, self.sort_title = sortify(self.title_slug)
        lc, created = LetterCount.objects.get_or_create(letter=self.first_letter,
                                                        defaults={"quantity": 1})
        if not created:
            lc.quantity += 1
        lc.save()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("main:recipe_detail", kwargs={"slug": self.title_slug})
    
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
                            on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.recipe} - {self.user} - {self.tag}"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("PaymentPlan", 
                             on_delete=models.SET_DEFAULT, 
                             default=get_basic_plan)
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    next_payment = models.DateField(_("Next Payment"), default=next_year)
    saved_recipes = models.ManyToManyField(Recipe, 
                                           related_name="saved_by")
    
    
    def __str__(self):
        return f"{self.user.name} ({self.user.id})"


class PaymentPlan(models.Model):
    name = models.CharField(_("Name"), max_length=25)
    name_slug = models.SlugField(_("Name Slug"), max_length=25, unique=True)
    interval = models.PositiveSmallIntegerField(_("Days between payments"), default=365)
    amount = models.PositiveSmallIntegerField(_("Amount"), default=10)

    class Meta:
        ordering = ["name_slug"]

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class RecipeRating(models.Model):
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(_("Rating"))

    class Meta:
        constraints = [models.UniqueConstraint(fields=["recipe", "profile"],
                                              name="unique_rating")]

    def __str__(self):
        return f"{self.profile} rated {self.recipe} {self.rating} stars"