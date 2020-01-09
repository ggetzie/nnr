from main.models import *
from main.forms import *
from django.conf import settings

from nnr.users.models import *

gabe = User.objects.get(username="gabe")

import stripe

stripe.api_key = settings.STRIPE_SK

