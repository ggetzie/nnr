"""django-allauth flow tests.

allauth is the riskiest dependency in the upgrade: the settings that drive it get
renamed between major versions, and this project overrides sixteen of its
templates under nnr/templates/account/. Rendering each override and walking a
full signup here means a broken template or a silently-ignored setting fails the
suite instead of reaching production.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from nnr.users.tests.factories import DEFAULT_PASSWORD

User = get_user_model()

pytestmark = pytest.mark.django_db


# --------------------------------------------------------------------------
# Every overridden template must still render
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "route",
    [
        "account_login",
        "account_signup",
        "account_reset_password",
    ],
)
def test_anonymous_account_pages_render(anon_client, route):
    assert anon_client.get(reverse(route)).status_code == 200


@pytest.mark.parametrize(
    "route",
    [
        "account_email",
        "account_change_password",
        "account_logout",
    ],
)
def test_authenticated_account_pages_render(subscribed_client, route):
    assert subscribed_client.get(reverse(route)).status_code == 200


# --------------------------------------------------------------------------
# Login is by email address, not username (ACCOUNT_AUTHENTICATION_METHOD)
# --------------------------------------------------------------------------


def test_login_with_email_succeeds(anon_client, subscribed_user):
    response = anon_client.post(
        reverse("account_login"),
        {"login": subscribed_user.email, "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 302
    assert response.wsgi_request.user.is_authenticated


def test_login_with_wrong_password_fails(anon_client, subscribed_user):
    response = anon_client.post(
        reverse("account_login"),
        {"login": subscribed_user.email, "password": "not-the-password"},
    )
    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


def test_unverified_account_is_sent_to_confirm_email(anon_client, unverified_user):
    """ACCOUNT_EMAIL_VERIFICATION = "mandatory" blocks login until confirmed."""
    response = anon_client.post(
        reverse("account_login"),
        {"login": unverified_user.email, "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 302
    assert response.url == "/accounts/confirm-email/"
    assert not response.wsgi_request.user.is_authenticated


# --------------------------------------------------------------------------
# Signup goes through main.forms.NNRSignupForm (ACCOUNT_FORMS)
# --------------------------------------------------------------------------


SIGNUP_DATA = {
    "email": "newcook@example.com",
    "username": "newcook",
    "password1": "a-perfectly-fine-pw-42",
    "password2": "a-perfectly-fine-pw-42",
    "tos": "on",
}


def test_signup_form_renders_every_field(anon_client):
    """A 200 is not enough: crispy-forms failing over would still return one.

    NNRSignupForm builds an explicit crispy Layout, so if the template pack is
    misconfigured the fields silently stop appearing.
    """
    html = anon_client.get(reverse("account_signup")).content.decode()

    assert 'id="signup_form"' in html
    for field in ("email", "username", "password1", "password2", "tos"):
        assert f'name="{field}"' in html, f"{field} missing from signup form"
    # bootstrap4 pack markup, i.e. crispy resolved a real template pack
    assert "form-group" in html


def test_login_form_renders_fields(anon_client):
    html = anon_client.get(reverse("account_login")).content.decode()
    assert 'name="login"' in html
    assert 'name="password"' in html


def test_signup_creates_user_and_sends_confirmation(anon_client):
    response = anon_client.post(reverse("account_signup"), SIGNUP_DATA)
    assert response.status_code == 302

    user = User.objects.get(username="newcook")
    assert user.email == "newcook@example.com"
    # ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    assert len(mail.outbox) == 1
    assert "confirm" in mail.outbox[0].body.lower()


def test_signup_requires_terms_of_service(anon_client):
    data = dict(SIGNUP_DATA)
    del data["tos"]

    response = anon_client.post(reverse("account_signup"), data)
    assert response.status_code == 200
    assert not User.objects.filter(username="newcook").exists()


def test_signup_creates_profile_with_thirty_day_trial(anon_client):
    """main.signals.create_profile is what makes a new account usable."""
    anon_client.post(reverse("account_signup"), SIGNUP_DATA)

    profile = User.objects.get(username="newcook").profile
    import datetime

    from dateutil.relativedelta import relativedelta

    assert profile.subscription_end == datetime.date.today() + relativedelta(days=30)


def test_signup_with_duplicate_email_creates_no_account(anon_client, subscribed_user):
    """allauth prevents account enumeration: the response looks like a success,
    but no second account is created for an address already in use."""
    data = dict(SIGNUP_DATA, email=subscribed_user.email)
    response = anon_client.post(reverse("account_signup"), data)

    assert response.status_code == 302
    assert not User.objects.filter(username="newcook").exists()
    assert User.objects.filter(email=subscribed_user.email).count() == 1


# --------------------------------------------------------------------------
# Password reset
# --------------------------------------------------------------------------


def test_password_reset_emails_a_known_address(anon_client, subscribed_user):
    response = anon_client.post(
        reverse("account_reset_password"), {"email": subscribed_user.email}
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 1


def test_password_reset_stays_silent_for_unknown_address(anon_client):
    """ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False -- do not confirm the address exists."""
    response = anon_client.post(
        reverse("account_reset_password"), {"email": "nobody@example.com"}
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 0
