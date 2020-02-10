from dateutil.relativedelta import relativedelta

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

import datetime
import markdown
import string

def next_year():
    today = datetime.date.today()
    return today + relativedelta(years=+1)

def get_basic_plan():
    plan, created =  PaymentPlan.objects.get_or_create(name_slug="basic", 
                                                       defaults={"name": "Basic"})
    return plan.id

PAYMENT_STATUS = ((0, "FAILED"),
                  (1, "NEEDS CONFIRMATION"),
                  (2, "TRIAL"),
                  (3, "SUCCESS"))
                  
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
    payment_status = models.PositiveSmallIntegerField(_("Payment Status"), 
                                                      choices=PAYMENT_STATUS,
                                                      default=2)
    subscription_end = models.DateField(_("Subscription End"))
    
    
    def __str__(self):
        return f"{self.user.name} ({self.user.id})"


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
