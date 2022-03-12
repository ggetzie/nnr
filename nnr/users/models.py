from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, BooleanField
from django.urls import reverse


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = CharField("Name of User", blank=True, max_length=255)
    is_ff = BooleanField("Friends & Family", default=False)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})
