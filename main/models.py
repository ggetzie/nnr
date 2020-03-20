from dateutil.relativedelta import relativedelta

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

import datetime
import logging
import markdown
import string

UTC = datetime.timezone.utc
BASE_RATE = 30 if settings.DEBUG else 5

logger = logging.getLogger(__name__)

def next_year():
    today = datetime.date.today()
    return today + relativedelta(years=+1)

def get_basic_plan():
    plan, _ =  PaymentPlan.objects.get_or_create(name_slug="basic", 
                                                 defaults={"name": "Basic"})
    return plan.id

PAYMENT_STATUS = ((0, "FAILED"),
                  (1, "NEEDS CONFIRMATION"),
                  (2, "TRIAL"),
                  (3, "SUCCESS"),
                  (4, "PENDING"),
                  (5, "CANCELED"))
                  
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("PaymentPlan", 
                             on_delete=models.SET_DEFAULT, 
                             default=get_basic_plan)
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    next_payment = models.DateField(_("Next Payment"), default=next_year)
    saved_recipes = models.ManyToManyField("recipes.Recipe", 
                                           related_name="saved_by")
    stripe_id = models.CharField(_("Stripe Customer Id"), max_length=50, 
                                 default="")
    checkout_session = models.CharField(_("Stripe Checkout Session"), max_length=100, 
                                        default="")
    payment_status = models.PositiveSmallIntegerField(_("Payment Status"), 
                                                      choices=PAYMENT_STATUS,
                                                      default=4)
    subscription_end = models.DateField(_("Subscription End"))
    rate_level = models.PositiveSmallIntegerField(_("Rate Level"),
                                                  default=1)
    last_sub = models.DateTimeField(_("Last Submission"), 
                                    default=datetime.datetime(year=1970,
                                                              month=1,
                                                              day=1,
                                                              tzinfo=UTC))
    
    
    def __str__(self):
        return f"{self.user.username} ({self.user.id})"

    def is_valid(self):
        return self.payment_status in (2, 3)

    def paid(self):
        return self.payment_status == 3

    def rate_limit_exceeded(self):
        now = datetime.datetime.now(tz=UTC)
        limit = BASE_RATE ** self.rate_level
        diff = now - self.last_sub
        exceeded = diff.total_seconds() < limit
        if exceeded:
            # submission is too soon after the last one
            self.rate_level += 1
            msg = (f"Posting too fast. Try again in "
                   f"{BASE_RATE ** self.rate_level} seconds.")
        else:
            self.rate_level = 1
            msg = ""
        self.last_sub = now
        self.save()
        
        return exceeded, msg

    def reset_rate_limit(self):
        self.rate_level = 1
        self.save()


class PaymentPlan(models.Model):
    name = models.CharField(_("Name"), max_length=25)
    name_slug = models.SlugField(_("Name Slug"), max_length=25, unique=True)
    interval = models.PositiveSmallIntegerField(_("Days between payments"), default=365)
    amount = models.PositiveSmallIntegerField(_("Amount"), default=10)
    stripe_id = models.CharField(_("Stripe Plan Id"), max_length=50,
                                 default="")

    class Meta:
        ordering = ["name_slug"]

    def save(self, *args, **kwargs):
        self.name_slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
