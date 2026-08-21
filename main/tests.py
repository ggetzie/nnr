"""Stripe webhook and subscription-state tests.

``main/views.py:webhook`` dispatches eight event types into handlers in
``main/payments.py`` that read deeply nested attributes off the parsed event
(``event.data.object.customer``). That attribute chain is built by the stripe
library, so a stripe major upgrade can change its shape without any import
breaking. These tests pin the resulting Profile state for every branch.

The stripe network calls made by ``Profile.sync_subscription`` are stubbed. The
stub signatures are deliberately the same ones the application calls, so if the
library renames or removes them the stub setup fails loudly.
"""

import datetime
import json

import pytest
import stripe
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from main.models import Profile

pytestmark = pytest.mark.django_db


class Obj:
    """Minimal stand-in for a stripe response object (attribute access)."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def stripe_stub(monkeypatch):
    """Stub the stripe calls reachable from the webhook handlers.

    Returns a dict the test can mutate to steer what the fake API returns.
    """
    state = {"subscription_status": "active", "email": None, "subscriptions": None}

    def fake_subscription_list(**kwargs):
        if state["subscriptions"] is not None:
            return Obj(data=state["subscriptions"])
        return Obj(data=[Obj(status=state["subscription_status"])])

    def fake_customer_retrieve(customer_id, **kwargs):
        return Obj(id=customer_id, email=state["email"])

    def fake_customer_list(**kwargs):
        return Obj(data=[])

    monkeypatch.setattr(stripe.Subscription, "list", fake_subscription_list)
    monkeypatch.setattr(stripe.Customer, "retrieve", fake_customer_retrieve)
    monkeypatch.setattr(stripe.Customer, "list", fake_customer_list)
    return state


def post_event(client, event_type, obj):
    """POST a Stripe-shaped event at the webhook."""
    payload = {
        "id": "evt_test_1",
        "object": "event",
        "type": event_type,
        "data": {"object": obj},
    }
    return client.post(
        reverse("main:webhook"),
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.fixture
def customer(subscribed_user):
    """A user already linked to a Stripe customer."""
    profile = subscribed_user.profile
    profile.stripe_id = "cus_test_123"
    profile.save()
    return profile


# --------------------------------------------------------------------------
# invoice.*
# --------------------------------------------------------------------------


def test_payment_succeeded_marks_paid_and_extends_a_year(
    anon_client, customer, stripe_stub
):
    response = post_event(
        anon_client,
        "invoice.payment_succeeded",
        {"customer": customer.stripe_id, "customer_email": None, "amount_paid": 1900},
    )
    assert response.status_code == 200

    customer.refresh_from_db()
    assert customer.payment_status == 3
    expected = datetime.date.today() + relativedelta(years=1)
    assert customer.subscription_end == expected


def test_zero_amount_invoice_marks_trial(anon_client, customer, stripe_stub):
    post_event(
        anon_client,
        "invoice.payment_succeeded",
        {"customer": customer.stripe_id, "customer_email": None, "amount_paid": 0},
    )
    customer.refresh_from_db()
    assert customer.payment_status == 2


def test_payment_action_required_marks_needs_confirmation(
    anon_client, customer, stripe_stub
):
    post_event(
        anon_client,
        "invoice.payment_action_required",
        {"customer": customer.stripe_id, "customer_email": None},
    )
    customer.refresh_from_db()
    assert customer.payment_status == 1


def test_payment_failed_marks_failed(anon_client, customer, stripe_stub):
    post_event(
        anon_client,
        "invoice.payment_failed",
        {"customer": customer.stripe_id, "customer_email": None},
    )
    customer.refresh_from_db()
    assert customer.payment_status == 0


def test_profile_is_found_by_email_when_stripe_id_is_unknown(
    anon_client, customer, stripe_stub
):
    """The handlers fall back to customer_email if no Profile has that stripe_id."""
    post_event(
        anon_client,
        "invoice.payment_failed",
        {"customer": "cus_not_in_db", "customer_email": customer.user.email},
    )
    customer.refresh_from_db()
    assert customer.payment_status == 0


# --------------------------------------------------------------------------
# checkout.session.completed
# --------------------------------------------------------------------------


def test_session_complete_links_stripe_customer(anon_client, subscribed_user, stripe_stub):
    profile = subscribed_user.profile
    profile.checkout_session = "cs_test_abc"
    profile.stripe_id = ""
    profile.save()

    post_event(
        anon_client,
        "checkout.session.completed",
        {
            "id": "cs_test_abc",
            "customer": "cus_new_456",
            "customer_email": subscribed_user.email,
        },
    )

    profile.refresh_from_db()
    assert profile.stripe_id == "cus_new_456"
    assert profile.checkout_session == ""
    assert profile.payment_status == 2


# --------------------------------------------------------------------------
# customer.subscription.*
# --------------------------------------------------------------------------


def test_subscription_updated_syncs_status(anon_client, customer, stripe_stub):
    stripe_stub["subscription_status"] = "past_due"
    post_event(
        anon_client, "customer.subscription.updated", {"customer": customer.stripe_id}
    )
    customer.refresh_from_db()
    assert customer.subscription_status == "past_due"


def test_subscription_created_adopts_existing_customer_by_email(
    anon_client, subscribed_user, stripe_stub
):
    profile = subscribed_user.profile
    profile.stripe_id = ""
    profile.save()
    stripe_stub["email"] = subscribed_user.email

    post_event(
        anon_client, "customer.subscription.created", {"customer": "cus_from_stripe"}
    )

    profile.refresh_from_db()
    assert profile.stripe_id == "cus_from_stripe"


def test_subscription_deleted_ends_subscription(anon_client, customer, stripe_stub):
    stripe_stub["subscriptions"] = []  # no subscriptions left at Stripe
    post_event(
        anon_client, "customer.subscription.deleted", {"customer": customer.stripe_id}
    )
    customer.refresh_from_db()
    assert customer.subscription_status == "canceled"


def test_subscription_deleted_for_unknown_customer_is_not_an_error(
    anon_client, stripe_stub
):
    response = post_event(
        anon_client, "customer.subscription.deleted", {"customer": "cus_ghost"}
    )
    assert response.status_code == 200


# --------------------------------------------------------------------------
# Dispatch itself
# --------------------------------------------------------------------------


def test_payment_method_updated_is_accepted(anon_client, customer, stripe_stub):
    response = post_event(anon_client, "payment_method.updated", {})
    assert response.status_code == 200


def test_unhandled_event_type_is_accepted(anon_client, stripe_stub):
    response = post_event(anon_client, "customer.created", {"customer": "cus_x"})
    assert response.status_code == 200


def test_malformed_payload_is_rejected(anon_client):
    response = anon_client.post(
        reverse("main:webhook"), data="not json", content_type="application/json"
    )
    assert response.status_code == 400


# --------------------------------------------------------------------------
# Profile helpers the gating depends on
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,valid,paid",
    [
        ("admin", True, True),
        ("free", True, True),
        ("active", True, True),
        ("trialing", True, False),
        ("past_due", False, False),
        ("canceled", False, False),
        ("incomplete", False, False),
        ("unpaid", False, False),
        ("", False, False),
    ],
)
def test_is_valid_and_paid(subscribed_user, status, valid, paid):
    profile = subscribed_user.profile
    profile.subscription_status = status
    profile.save()
    assert profile.is_valid() is valid
    assert profile.paid() is paid


def test_profile_created_for_new_user_with_trial(subscribed_user):
    assert Profile.objects.filter(user=subscribed_user).exists()


def test_rate_limit_blocks_rapid_submissions(subscribed_user):
    profile = subscribed_user.profile
    exceeded, _ = profile.rate_limit_exceeded()
    assert exceeded is False  # last_sub is 1970

    exceeded, msg = profile.rate_limit_exceeded()
    assert exceeded is True
    assert "Posting too fast" in msg
