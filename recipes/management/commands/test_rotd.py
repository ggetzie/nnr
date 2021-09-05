import datetime
import random

from recipes.models import Recipe
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **options):
        omago = datetime.date.today() - datetime.timedelta(days=30)
        old_rotd = Recipe.objects.get(featured=True)
        candidates = Recipe.objects.filter(last_featured__lt=omago)
        offset = random.randint(0, candidates.count()-1)
        new_rotd = candidates[offset]
        old_rotd.featured = False
        new_rotd.featured = True
        old_rotd.save()
        new_rotd.save()
