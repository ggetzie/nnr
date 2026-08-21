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


WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture(autouse=True)
def webhook_secret(monkeypatch):
    """Configure signature verification for every test in this module.

    This is the production configuration, so it is what the handler tests should
    run against. main.views reads the secret through its own environ.Env
    instance, which consults os.environ at call time.
    """
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    return WEBHOOK_SECRET


def sign(payload: str, secret: str = WEBHOOK_SECRET, timestamp: int | None = None):
    """Build a Stripe-Signature header the way Stripe does."""
    import hashlib
    import hmac
    import time

    timestamp = timestamp if timestamp is not None else int(time.time())
    signed = f"{timestamp}.{payload}".encode()
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def event_payload(event_type, obj):
    return json.dumps(
        {
            "id": "evt_test_1",
            "object": "event",
            "type": event_type,
            "data": {"object": obj},
        }
    )


def post_event(client, event_type, obj):
    """POST a correctly signed Stripe-shaped event at the webhook."""
    payload = event_payload(event_type, obj)
    return client.post(
        reverse("main:webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=sign(payload),
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


def test_session_complete_links_stripe_customer(
    anon_client, subscribed_user, stripe_stub
):
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
# Signature verification (only active when STRIPE_WEBHOOK_SECRET is set)
# --------------------------------------------------------------------------


def signed_event(event_type, obj):
    payload = event_payload(event_type, obj)
    return payload, sign(payload)


def test_correctly_signed_webhook_is_processed(anon_client, customer, stripe_stub):
    """The raw body is what gets signed.

    This previously passed a re-serialised dict to construct_event, so a genuine
    Stripe request could never verify.
    """
    payload, signature = signed_event(
        "invoice.payment_failed",
        {"customer": customer.stripe_id, "customer_email": None},
    )

    response = anon_client.post(
        reverse("main:webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=signature,
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.payment_status == 0


def test_wrongly_signed_webhook_is_rejected(anon_client, customer, stripe_stub):
    payload, _ = signed_event(
        "invoice.payment_failed",
        {"customer": customer.stripe_id, "customer_email": None},
    )
    bad_signature = sign(payload, secret="whsec_not_the_secret")

    response = anon_client.post(
        reverse("main:webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=bad_signature,
    )

    assert response.status_code == 400
    customer.refresh_from_db()
    assert customer.payment_status != 0


def test_webhook_without_signature_header_is_rejected(
    anon_client, customer, stripe_stub
):
    """Used to raise KeyError on request.META and return a 500."""
    payload, _ = signed_event(
        "invoice.payment_failed",
        {"customer": customer.stripe_id, "customer_email": None},
    )

    response = anon_client.post(
        reverse("main:webhook"), data=payload, content_type="application/json"
    )

    assert response.status_code == 400
    customer.refresh_from_db()
    assert customer.payment_status != 0


def test_replayed_old_signature_is_rejected(anon_client, customer, stripe_stub):
    """Stripe's default tolerance is five minutes."""
    import time

    payload, _ = signed_event(
        "invoice.payment_failed",
        {"customer": customer.stripe_id, "customer_email": None},
    )
    stale = sign(payload, timestamp=int(time.time()) - 3600)

    response = anon_client.post(
        reverse("main:webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=stale,
    )

    assert response.status_code == 400


def test_tampered_body_with_valid_looking_signature_is_rejected(
    anon_client, customer, stripe_stub
):
    """Sign one payload, send another."""
    original, signature = signed_event(
        "invoice.payment_failed",
        {"customer": customer.stripe_id, "customer_email": None},
    )
    tampered = original.replace("payment_failed", "payment_succeeded")

    response = anon_client.post(
        reverse("main:webhook"),
        data=tampered,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=signature,
    )

    assert response.status_code == 400


# --------------------------------------------------------------------------
# Behaviour when no secret is configured at all
# --------------------------------------------------------------------------


def post_unsigned(client, event_type, obj):
    return client.post(
        reverse("main:webhook"),
        data=event_payload(event_type, obj),
        content_type="application/json",
    )


def test_missing_secret_refuses_to_process_when_debug_is_off(
    anon_client, customer, stripe_stub, monkeypatch, settings
):
    """Production must not act on a webhook it cannot verify."""
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    settings.DEBUG = False

    response = post_unsigned(
        anon_client,
        "invoice.payment_succeeded",
        {"customer": customer.stripe_id, "customer_email": None, "amount_paid": 1900},
    )

    assert response.status_code == 500
    customer.refresh_from_db()
    assert customer.payment_status != 3


def test_missing_secret_still_processes_under_debug(
    anon_client, customer, stripe_stub, monkeypatch, settings
):
    """Local development can exercise the endpoint without the Stripe CLI."""
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    settings.DEBUG = True

    response = post_unsigned(
        anon_client,
        "invoice.payment_succeeded",
        {"customer": customer.stripe_id, "customer_email": None, "amount_paid": 1900},
    )

    assert response.status_code == 200
    customer.refresh_from_db()
    assert customer.payment_status == 3


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
