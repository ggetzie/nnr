import datetime
import random

from django.core.management.base import BaseCommand, CommandError
from main.models import Recipe

class Command(BaseCommand):

    def handle(self, *args, **options):
        # reset previous rotd
        try:
            old_rotd = Recipe.objects.get(featured=True)
            old_rotd.featured = False
            old_rotd.save()
        except Recipe.DoesNotExist:
            pass

        thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)
        recipes = Recipe.objects.filter(last_featured__lt=thirty_days_ago)

        new_rotd = random.choice(recipes)
        new_rotd.featured = True
        new_rotd.last_featured = datetime.date.today()
        new_rotd.save()
