from dateutil.relativedelta import relativedelta

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

import datetime
import markdown

def next_year():
    today = datetime.date.today()
    return today + relativedelta(years=1)

def get_basic_plan():
    plan, created =  PaymentPlan.objects.get_or_create(name_slug="basic", 
                                                       defaults={"name": "Basic"})
    return plan.id
                            

class Recipe(models.Model):
    title = models.CharField(_("Title"), max_length=150)
    title_slug = models.SlugField(_("Title Slug"), max_length=150, unique=True)
    ingredients_text = models.TextField(_("Ingredients"))
    ingredients_html = models.TextField(_("Ingredients HTML"))
    instructions_text = models.TextField(_("Instructions"))
    instructions_html = models.TextField(_("Instructions HTML"))
    tags = models.ManyToManyField("Tag")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.SET_NULL,
                             null=True)

    def save(self, *args, **kwargs):
        self.ingredients_html = markdown.markdown(self.ingredients_text)
        self.instructions_html = markdown.markdown(self.instructions_text)
        self.title_slug = slugify(self.title)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title_slug}"


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=100)
    name_slug = models.SlugField(_("slug"), max_length=100, unique=True)

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("PaymentPlan", 
                             on_delete=models.SET_DEFAULT, 
                             default=get_basic_plan)
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    next_payment = models.DateField(_("Next Payment"), default=next_year)

    def __str__(self):
        return f"{self.user.name} {self.user.id}"


class PaymentPlan(models.Model):
    name = models.CharField(_("Name"), max_length=25)
    name_slug = models.SlugField(_("Name Slug"), max_length=25, unique=True)
    interval = models.PositiveSmallIntegerField(_("Days between payments"), default=365)
    amount = models.PositiveSmallIntegerField(_("Amount"), default=10)

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"