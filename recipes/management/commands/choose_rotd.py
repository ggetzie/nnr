import datetime
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.management.base import BaseCommand

from recipes.models import Recipe
from recipes.twitter import create_tweet

logger = logging.getLogger(__name__)


def set_new_rotd() -> Recipe:
    today = datetime.date.today()
    omago = today - datetime.timedelta(days=30)
    old_rotd = Recipe.objects.get(featured=True)
    new_rotd = Recipe.objects.filter(last_featured__lt=omago).order_by("?").first()
    old_rotd.featured = False
    new_rotd.featured = True
    new_rotd.last_featured = today
    old_rotd.save()
    new_rotd.save()
    return new_rotd


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        Pick the next recipe of the day, bust the cached homepage fragment and
        announce it.

        This is the only thing that selects the recipe of the day. It runs from
        cron via recipes/management/rotd.sh. A Go lambda under awslambda/rotd
        used to do the same job and was removed; if a docstring or comment
        anywhere still says the selection lives in Go, it is out of date.
        """

        cache_key = make_template_fragment_key("rotd")
        cache.delete(cache_key)

        new_rotd = set_new_rotd()

        # post to twitter
        create_tweet(
            settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_SECRET,
            new_rotd.as_tweet(),
        )

        # TODO fix posting to facebook when approved
