from dateutil.relativedelta import relativedelta
from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress

from crispy_forms.bootstrap import (
    InlineField,
    FormActions,
    Accordion,
    AccordionGroup,
    FieldWithButtons,
    StrictButton,
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Fieldset, Div, HTML

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from main.models import Profile
from main.payments import get_payment_plans
import datetime
import logging
import string

User = get_user_model()
logger = logging.getLogger(__name__)


class NNRSignupForm(SignupForm):
    tos = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # today = datetime.date.today()
        # paydate = today + relativedelta(days=30)
        # payinfo = ("Your card will be charged an annual fee of $19 "
        #            "USD. The first charge will take place at the end of the "
        #            f"30 day free trial period on {paydate:%B %d, %Y} and thereafter "
        #            "annually on that date.")
        TOS_LINK = (
            f"""<a href="{reverse_lazy('tos')}" """
            """target="_blank">Terms of Service</a>"""
        )
        PP_LINK = (
            f"""<a href="{reverse_lazy('privacy')}" """
            """target="_blank">Privacy Policy</a>"""
        )
        self.fields["tos"].label = mark_safe(
            _("I have read and agree to the " f"{TOS_LINK} and {PP_LINK}")
        )
        self.helper = FormHelper()
        self.helper.form_id = "signup_form"
        self.helper.form_class = "signup"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "email",
            "username",
            "password1",
            "password2",
            "tos",
            Div(Submit("signup", "&raquo; Signup"), css_class="form-row float-right"),
        )

    # class Media:
    #     js = (settings.STATIC_URL + "js/signup.js",)

    def save(self, request):
        user = super().save(request)
        return user


class CancelForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "cancel_form"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("main:cancel_subscription")
        self.helper.layout = Layout(
            Submit("cancel", "Cancel", css_class="btn btn-danger")
        )


class ReactivateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "reactivate_form"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("main:reactivate_subscription")
        self.helper.layout = Layout(
            Submit(
                "reactivate", "Turn On Automatic Renewal", css_class="btn btn-success"
            )
        )


class PaymentPlanForm(forms.Form):
    plan = forms.ChoiceField(choices=get_payment_plans, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "payment_plan_form"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("main:create_checkout_session")
        self.helper.layout = Layout(Div("plan", css_class="form-container"))


class AddFriendForm(forms.Form):
    username = forms.CharField(max_length=100)
    password1 = forms.CharField(
        max_length=100, widget=forms.PasswordInput, label="Password"
    )
    password2 = forms.CharField(
        max_length=100, widget=forms.PasswordInput, label="Re-enter password"
    )
    email = forms.EmailField()

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise ValidationError("A user with that username already exists")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["password1"] != cleaned_data["password2"]:
            raise ValidationError("Password fields must match")
        return cleaned_data

    def save(self):
        email = self.cleaned_data["email"]
        user = User(username=self.cleaned_data["username"], is_ff=True, email=email)
        password = self.cleaned_data["password1"]
        user.set_password(password)
        user.save()
        email_obj = EmailAddress(user=user, email=email, verified=True, primary=True)
        email_obj.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "add-friend-form"
        self.helper.form_method = "post"
        self.helper.form_class = "signup-pitch mt-5"
        self.helper.layout = Layout(
            "email",
            "username",
            "password1",
            "password2",
            Div(
                Submit("submit", "Submit"), css_class="form-row d-flex flex-row-reverse"
            ),
        )
