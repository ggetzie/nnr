from main.models import Profile
from main.forms import *
from django.conf import settings

from recipes.models import *
from recipes.forms import *

from comments.models import *
from comments.forms import *

from nnr.users.models import *

gabe = User.objects.get(username="gabe")

import stripe

stripe.api_key = settings.STRIPE_SK

