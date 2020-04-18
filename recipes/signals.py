from django.core.cache import cache
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Recipe


@receiver(pre_delete, sender=Recipe)
def clear_cache_recipe_detail(sender, **kwargs):
    recipe = kwargs["instance"]
    recipe_key = f"{recipe.title_slug}-detail"
    cache.delete(recipe_key)
