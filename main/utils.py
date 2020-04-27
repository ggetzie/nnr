import datetime
import hashlib

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlquote

import logging

logger = logging.getLogger(__name__)

def get_trial_end():
    if settings.DEBUG:
        trial_period = relativedelta(minutes=1)
    else:
        trial_period = relativedelta(days=30)
    trial_end = datetime.datetime.now() + trial_period
    return int(trial_end.timestamp())

def get_subscription_plan():
    if settings.DEBUG:
        # test plan
        plan = "plan_GE5qJjPJHeV0Hn"
    else:
        # production plan
        plan = "plan_G9ZcHdJbqG4WBs"
    return plan