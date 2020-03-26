from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import redirect

import datetime
import logging

from main.models import BASE_RATE

logger = logging.getLogger(__name__)

class ValidUserMixin(UserPassesTestMixin):
    payment_failed_message = ("We were unable to process your last payment. "
                              "Please update your payment information to proceed")

    payment_confirm_message = ("Your payment method requires additional confirmation "
                               "Please check your email and complete the required "
                               "confirmation steps to proceed")

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        if self.request.user.profile.subscription_status in ("admin",
                                                             "free", 
                                                             "trialing",
                                                             "active"):
            return True
        if self.request.user.profile.subscription_status in ("",
                                                             "incomplete",
                                                             "incomplete_expired",
                                                             "past_due",
                                                             "unpaid"):
            # payment failed
            if self.request.user.profile.stripe_id:
                messages.warning(self.request, self.payment_failed_message)
            self.permission_denied_message = self.payment_failed_message
        if self.request.user.profile.subscription_status == "canceled":
            # canceled account
            self.permission_denied_message = "Your account has been canceled."
        return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if self.request.user.profile.subscription_status in ("",
                                                                "incomplete",
                                                                "incomplete_expired",
                                                                "past_due",
                                                                "unpaid"):
                return redirect("main:payment")
            elif self.request.user.profile.subscription_status == "canceled":
                return redirect("main:expired")
            else:
                pass

        return super().handle_no_permission()


class HttpResponseTooManyRequests(HttpResponse):
    status_code = 429


class RateLimitMixin():

    def post(self, request, *args, **kwargs):
        profile = self.request.user.profile
        exceeded, msg = profile.rate_limit_exceeded()
        if exceeded:
            return HttpResponseTooManyRequests(msg)
        
        return super().post(request, *args, **kwargs)