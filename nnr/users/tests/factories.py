from typing import Any, Sequence

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

# Tests that need to log a user in have to know the password, so it is fixed
# rather than generated. Override by passing password="..." to the factory.
DEFAULT_PASSWORD = "n0nsense-test-pw"


class UserFactory(DjangoModelFactory):

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")

    @factory.post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        self.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            self.save()

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]
