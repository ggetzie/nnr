
import logging

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        The functionality to set the new recipe of the day has been moved to
        a go module in the nnr/awslambda folder to be run by a lambda function.
        This command is kept to be run at the same time (or shortly after) only to
        delete the cache entry
        """
        
        cache_key = make_template_fragment_key("rotd")
        cache.delete(cache_key)