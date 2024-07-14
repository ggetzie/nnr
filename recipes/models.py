from django.db import models
from django.conf import settings
from django.contrib.postgres.search import SearchVectorField
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify

from nnr.custom_storages import RawMediaStorage
from .utils import sortify, utc_now

import datetime
import markdown
import re
import string
import uuid
from textwrap import dedent

import logging

logger = logging.getLogger(__name__)


def setup_lettercounts():
    nums = LetterCount.objects.get_or_create(letter="0-9", defaults={"quantity": 0})[0]
    nums.save()
    for letter in string.ascii_uppercase:
        lc = LetterCount.objects.get_or_create(letter=letter, defaults={"quantity": 0})[
            0
        ]
        lc.save()
    for r in Recipe.objects.all():
        r.save()


def make_detail_key(slug):
    return f"{slug}-detail"


IMAGE_STORAGE = default_storage if settings.DEBUG else RawMediaStorage


def replace_filename(url, size, ext):
    """Replace filenames with different sizes for photo tag"""
    prefix = url.rsplit("/", maxsplit=1)[0]
    return "/".join([prefix, f"{size}.{ext}"])


class LetterCount(models.Model):
    letter = models.CharField("Letter", default="", max_length=3, unique=True)
    quantity = models.IntegerField("Quantity", default=0)

    class Meta:
        ordering = ["letter"]

    def __str__(self):
        return f"{self.quantity} of {self.letter}"


INGREDIENTS_HELP = "Tip: list ingredients in the order they are used"


class Recipe(models.Model):
    title = models.CharField("Title", max_length=150)
    title_slug = models.SlugField("Title Slug", max_length=150, unique=True)
    ingredients_text = models.TextField("Ingredients", help_text=INGREDIENTS_HELP)
    ingredients_html = models.TextField("Ingredients HTML")
    instructions_text = models.TextField("Instructions")
    instructions_html = models.TextField("Instructions HTML")
    quantity_text = models.CharField("Yield", max_length=200, default="")
    quantity_html = models.CharField("Quantity HTML", max_length=400, default="")
    tags = models.ManyToManyField("Tag", through="UserTag")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="author",
    )
    first_letter = models.CharField("First Letter", max_length=3, default="")
    sort_title = models.CharField("Sort Title", max_length=150, default="")
    created = models.DateField("Date Created", auto_now_add=True)
    created_dt = models.DateTimeField(
        "Datetime Created", auto_now_add=True, blank=True, null=True
    )
    featured = models.BooleanField("Recipe of the Day", default=False)
    last_featured = models.DateField(
        "Last Featured", default=datetime.date(year=1970, month=1, day=1)
    )
    see_also = models.ManyToManyField("self", blank=True)
    search_vector = SearchVectorField(null=True)
    approved = models.BooleanField("Approved", default=False)

    class Meta:
        ordering = ["sort_title"]

    def __str__(self):
        if len(self.title) < 15:
            return self.title
        else:
            return f"{self.title[:15]}..."

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
        lc, created = LetterCount.objects.get_or_create(
            letter=self.first_letter, defaults={"quantity": 1}
        )
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
        return f"""{self.title}\n\nIngredients:\n{self.get_ingredients_text()}\n\nInstructions:\n{self.get_instructions_text()}"""

    def ingredients_list(self):
        return (
            line.strip()
            for line in strip_tags(self.ingredients_html).split("\n")
            if line
        )

    def get_ingredients_text(self):
        return strip_tags(self.ingredients_html).strip()

    def get_instructions_text(self):
        return strip_tags(self.instructions_html).strip()

    def as_tweet(self) -> str:
        max_length = 280
        length_remaining = max_length
        title = self.title
        url = "https://nononsense.recipes" + self.get_absolute_url()
        intro = f"Recipe of the Day\n"
        message = f"{intro}{self.title}\n{url}"
        length_remaining -= len(message)
        tags = sorted([re.sub(r"\W", "", tag.name) for tag in self.tags.all()], key=len)
        if length_remaining > len(tags[0]) + 3:
            message += "\n"
            length_remaining -= 1
            for i, tag in enumerate(tags):
                hashtag = f" #{tag}" if i > 0 else f"#{tag}"
                if length_remaining - len(hashtag) > 0:
                    message += hashtag
                    length_remaining -= len(hashtag)
                else:
                    break
            return message
        elif length_remaining > 0:
            return message
        else:
            truncated = f"{title}\n{url}"
            return truncated if len(truncated) < max_length else url


SCREEN_SIZES = ["1200", "992", "768", "576", "408", "320"]
PHOTO_EXTENSIONS = ["webp", "jpeg"]


def tag_photo_path(instance, filename):
    stem, ext = filename.rsplit(".", maxsplit=1)
    ext = ext.lower()
    # standardize on "jpeg" extension for jpegs
    if ext == "jpg":
        ext = "jpeg"
    path = f"images/tags/{instance.name_slug}/{stem.lower()}.{ext}"
    return path


class Tag(models.Model):
    name = models.CharField("name", max_length=100)
    name_slug = models.SlugField("slug", max_length=100, unique=True)
    hashtag = models.BooleanField("Use as hashtag", default=False)
    photo = models.ImageField(
        "Photo", blank=True, null=True, upload_to=tag_photo_path, storage=IMAGE_STORAGE
    )

    class Meta:
        ordering = ["name_slug"]

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("recipes:tag_detail", kwargs={"slug": self.name_slug})

    @property
    def caption(self):
        return f"Tagged: {self.name}"

    @property
    def thumbnail_url(self):
        return replace_filename(self.photo.url, "thumbnail", "jpeg")

    def picture_tag(self):
        sources = "\n".join(
            [
                f"""<source media="(min-width:{size}px)" srcset="{replace_filename(self.photo.url, size, ext)}">"""
                for size in SCREEN_SIZES
                for ext in PHOTO_EXTENSIONS
            ]
        )
        return dedent(
            f"""
        <picture class="d-block w-100">
            {sources}
            <img src="{self.photo.url}">
        </picture>
        """
        )


class UserTag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owner"
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tag", "recipe"], name="unique_user_tag"
            )
        ]

    def __str__(self):
        return f"{self.recipe} - {self.user} - {self.tag}"


RATING_CHOICES = (
    (1, "⭐"),
    (2, "⭐⭐"),
    (3, "⭐⭐⭐"),
    (4, "⭐⭐⭐⭐"),
    (5, "⭐⭐⭐⭐⭐"),
)


class RecipeRating(models.Model):
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField("Rating", choices=RATING_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"], name="unique_recipe_rating"
            )
        ]
        ordering = ["user", "recipe__sort_title"]

    def __str__(self):
        return f"{self.user.username} rated {self.recipe} {self.rating} stars"


def recipe_photo_path(instance, filename):
    stem, ext = filename.rsplit(".", maxsplit=1)
    ext = ext.lower()
    # standardize on "jpeg" extension for jpegs
    if ext == "jpg":
        ext = "jpeg"
    path = f"images/recipes/{instance.recipe.title_slug}/{instance.id}/{stem.lower()}.{ext}"
    return path


class RecipePhoto(models.Model):
    id = models.UUIDField("id", primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    photo = models.ImageField(
        "Photo", max_length=200, upload_to=recipe_photo_path, storage=IMAGE_STORAGE
    )
    reviewed = models.BooleanField("Reviewed", default=False)
    approved = models.BooleanField("Approved", default=False)
    resized = models.BooleanField("Resized options created", default=False)
    timestamp = models.DateTimeField("Timestamp", default=utc_now, editable=False)
    caption = models.CharField("Caption", max_length=200, default="", blank=True)
    order = models.PositiveSmallIntegerField("Order", default=1)

    class Meta:
        ordering = ["recipe__sort_title", "-timestamp"]

    def picture_tag(self):

        sources = "\n".join(
            [
                f"""<source media="(min-width:{size}px)" srcset="{replace_filename(self.photo.url, size, ext)}">"""
                for size in SCREEN_SIZES
                for ext in PHOTO_EXTENSIONS
            ]
        )
        return dedent(
            f"""
        <picture>
            {sources}
            <img src="{self.photo.url}">
        </picture>
        """
        )

    @property
    def thumbnail_url(self):
        return replace_filename(self.photo.url, "thumbnail", "jpeg")
