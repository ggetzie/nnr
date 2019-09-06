from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        profile = Profile(user=user)
        profile.save()
