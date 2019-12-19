from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.models import Profile

import datetime

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        if user.is_staff:
            sub_end = datetime.date.today() + relativedelta(years=1000)
        else:
            sub_end = datetime.date.today() + relativedelta(days=30)
        profile = Profile(user=user, subscription_end=sub_end)
        profile.save()
