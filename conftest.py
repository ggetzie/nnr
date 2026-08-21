"""Shared pytest fixtures.

This lives at the repo root rather than in nnr/ because the apps are split
between the repo root (recipes, main, comments) and the nnr/ package (users).
A conftest under nnr/ is only visible to tests under nnr/.
"""

import datetime

import pytest
from django.conf import settings
from django.test import Client, RequestFactory

from nnr.users.tests.factories import DEFAULT_PASSWORD, UserFactory

UTC = datetime.timezone.utc


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


def make_user(
    *,
    subscription_status="",
    stripe_id="",
    checkout_session="",
    verified=True,
    **kwargs,
):
    """A user whose Profile is in a specific subscription state.

    main.signals.create_profile already builds the Profile on user creation, so
    this only has to move it into the state under test.

    ACCOUNT_EMAIL_VERIFICATION is "mandatory", so an account with no verified
    EmailAddress cannot log in through the form. Fixtures default to verified;
    pass verified=False to exercise the confirm-email path.
    """
    from allauth.account.models import EmailAddress

    user = UserFactory(**kwargs)
    EmailAddress.objects.create(
        user=user, email=user.email, primary=True, verified=verified
    )
    profile = user.profile
    profile.subscription_status = subscription_status
    profile.stripe_id = stripe_id
    profile.checkout_session = checkout_session
    # Push last_sub back so the rate limiter is not what fails an unrelated test.
    profile.last_sub = datetime.datetime(1970, 1, 1, tzinfo=UTC)
    profile.save()
    return user


def make_client(user):
    client = Client()
    if user is not None:
        client.force_login(user)
    return client


@pytest.fixture
def user():
    return make_user(subscription_status="active")


@pytest.fixture
def trial_user():
    return make_user(subscription_status="trialing")


@pytest.fixture
def subscribed_user():
    return make_user(subscription_status="active")


@pytest.fixture
def lapsed_user():
    """Payment failed. Has a Stripe customer, so should be sent to main:payment."""
    return make_user(subscription_status="past_due", stripe_id="cus_test_lapsed")


@pytest.fixture
def pending_user():
    """Checkout started but never completed -> main:processing."""
    return make_user(subscription_status="incomplete", checkout_session="cs_test_123")


@pytest.fixture
def canceled_user():
    return make_user(subscription_status="canceled")


@pytest.fixture
def staff_user():
    return make_user(subscription_status="", is_staff=True)


@pytest.fixture
def unverified_user():
    return make_user(subscription_status="trialing", verified=False)


@pytest.fixture
def anon_client():
    return Client()


@pytest.fixture
def trial_client(trial_user):
    return make_client(trial_user)


@pytest.fixture
def subscribed_client(subscribed_user):
    return make_client(subscribed_user)


@pytest.fixture
def lapsed_client(lapsed_user):
    return make_client(lapsed_user)


@pytest.fixture
def pending_client(pending_user):
    return make_client(pending_user)


@pytest.fixture
def canceled_client(canceled_user):
    return make_client(canceled_user)


@pytest.fixture
def staff_client(staff_user):
    return make_client(staff_user)


@pytest.fixture
def password():
    return DEFAULT_PASSWORD


@pytest.fixture
def recipe(subscribed_user):
    from recipes.models import Recipe

    return Recipe.objects.create(
        title="Test Pancakes",
        ingredients_text="- flour\n- eggs",
        instructions_text="1. Mix\n2. Cook",
        quantity_text="4 servings",
        user=subscribed_user,
        approved=True,
    )


@pytest.fixture
def tag():
    from recipes.models import Tag

    return Tag.objects.create(name="Breakfast")


@pytest.fixture
def user_tag(subscribed_user, recipe, tag):
    from recipes.models import UserTag

    return UserTag.objects.create(user=subscribed_user, recipe=recipe, tag=tag)
