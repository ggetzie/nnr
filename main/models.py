from dateutil.relativedelta import relativedelta
import stripe

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

import datetime
import logging

UTC = datetime.timezone.utc
BASE_RATE = 30 if settings.DEBUG else 5

logger = logging.getLogger(__name__)


def next_year():
    today = datetime.date.today()
    return today + relativedelta(years=+1)


def get_basic_plan():
    plan, _ = PaymentPlan.objects.get_or_create(
        name_slug="basic", defaults={"name": "Basic"}
    )
    return plan.id


PAYMENT_STATUS = (
    (0, "FAILED"),
    (1, "NEEDS CONFIRMATION"),
    (2, "TRIAL"),
    (3, "SUCCESS"),
    (4, "PENDING"),
    (5, "CANCELED"),
)

SUBSCRIPTION_STATUS = (
    ("", "undefined"),
    ("admin", "Administrator"),
    ("free", "Free Account"),
    ("incomplete", "Incomplete"),
    ("incomplete_expired", "Incomplete, Session Expired"),
    ("trialing", "Free Trial"),
    ("active", "Active"),
    ("past_due", "Past Due"),
    ("canceled", "Canceled"),
    ("unpaid", "Unpaid"),
)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(
        "PaymentPlan", on_delete=models.SET_DEFAULT, default=get_basic_plan
    )
    created = models.DateTimeField("Created", auto_now_add=True)
    next_payment = models.DateField("Next Payment", default=next_year)
    saved_recipes = models.ManyToManyField("recipes.Recipe", related_name="saved_by")
    stripe_id = models.CharField("Stripe Customer Id", max_length=50, default="")
    checkout_session = models.CharField(
        "Stripe Checkout Session", max_length=100, default=""
    )
    payment_status = models.PositiveSmallIntegerField(
        "Payment Status", choices=PAYMENT_STATUS, default=4
    )
    subscription_status = models.CharField(
        "Subscription Status", max_length=25, default="", choices=SUBSCRIPTION_STATUS
    )
    subscription_end = models.DateField("Subscription End")
    rate_level = models.PositiveSmallIntegerField("Rate Level", default=1)
    last_sub = models.DateTimeField(
        "Last Submission",
        default=datetime.datetime(year=1970, month=1, day=1, tzinfo=UTC),
    )

    def __str__(self):
        return f"{self.user.username} ({self.user.id})"

    def is_valid(self):
        return self.subscription_status in ("admin", "free", "trialing", "active")

    def paid(self):
        return self.subscription_status in ("admin", "free", "active")

    def rate_limit_exceeded(self):
        now = datetime.datetime.now(tz=UTC)
        limit = BASE_RATE ** self.rate_level
        diff = now - self.last_sub
        exceeded = diff.total_seconds() < limit
        if exceeded:
            # submission is too soon after the last one
            self.rate_level += 1
            msg = (
                f"Posting too fast. Try again in "
                f"{BASE_RATE ** self.rate_level} seconds."
            )
        else:
            self.rate_level = 1
            msg = ""
        self.last_sub = now
        self.save()

        return exceeded, msg

    def reset_rate_limit(self):
        self.rate_level = 1
        self.save()

    def sync_subscription(self):
        stripe.api_key = settings.STRIPE_SK
        if self.stripe_id:
            subs = stripe.Subscription.list(customer=self.stripe_id)
            if subs.data:
                self.subscription_status = subs.data[0].status
            else:
                self.subscription_status = "canceled"
        elif self.checkout_session:
            self.subscription_status = "incomplete"
        elif self.user.is_staff or self.user.is_superuser:
            self.subscription_status = "admin"
        else:
            self.subscription_status = "free"
        self.save()

    def update_stripe_id(self):
        stripe.api_key = settings.STRIPE_SK
        if not self.stripe_id:
            result = stripe.Customer.list(email=self.user.email, limit=1)
            if result.data:
                self.stripe_id = result.data[0].id
                self.save()


class PaymentPlan(models.Model):
    name = models.CharField("Name", max_length=25)
    name_slug = models.SlugField("Name Slug", max_length=25, unique=True)
    interval = models.PositiveSmallIntegerField("Days between payments", default=365)
    amount = models.PositiveSmallIntegerField("Amount", default=10)
    stripe_id = models.CharField("Stripe Plan Id", max_length=50, default="")

    class Meta:
        ordering = ["name_slug"]

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
