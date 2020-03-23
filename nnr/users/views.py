from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView, RedirectView, UpdateView
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

import stripe

from main.forms import CancelForm, ReactivateForm
User = get_user_model()

class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        
        context =  super().get_context_data(**kwargs)
        subs = None
        has_sub = not self.object.profile.subscription_status in ("admin", "free", "")
        if has_sub:
            stripe.api_key = settings.STRIPE_SK
            subs = stripe.Subscription.list(customer=self.object.profile.stripe_id)
        context["has_sub"] = has_sub
        if subs:
            context["cancel_at_period_end"] = subs.data[0].cancel_at_period_end
            end_date = datetime.fromtimestamp(subs.data[0].current_period_end)
            context["subscription_end"] = end_date.strftime("%B %d, %Y")
            context["amount"] = subs.data[0].plan.amount / 100
            context["cancel_form"] = CancelForm()
            context["reactivate_form"] = ReactivateForm()
        return context

user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    fields = ["name"]
    context_object_name = "user"

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self):
        return User.objects.get(username=self.request.user.username)

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.INFO, _("Infos successfully updated")
        )
        return super().form_valid(form)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
