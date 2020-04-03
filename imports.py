import pathlib
import datetime
import random
from importlib import reload

from main.models import *
from main.forms import *
from django.conf import settings

from recipes.models import *
from recipes.forms import *
from recipes.utils import *

from comments.models import *
from comments.forms import *

from nnr.users.models import *

gabe = User.objects.get(username="gabe")

recipe_data = pathlib.Path("/usr/local/src/nnr/recipes/collect/data")
from recipes.collect import books, ingest

import stripe

stripe.api_key = settings.STRIPE_SK

