from dateutil.relativedelta import relativedelta
from allauth.account.forms import SignupForm

from crispy_forms.bootstrap import (InlineField, FormActions, Accordion, 
                                    AccordionGroup, FieldWithButtons, 
                                    StrictButton)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Fieldset, Div, HTML

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from main.models import Profile
import datetime                    
import logging

User = get_user_model()
DUPE_MSG = _("A recipe with that title already exists!")
logger = logging.getLogger(__name__)

class NNRSignupForm(SignupForm):
    tos = forms.BooleanField()
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = datetime.date.today()
        paydate = today + relativedelta(days=30)
        payinfo = ("Your card will be charged an annual fee of $19 "
                   "USD. The first charge will take place at the end of the "
                   f"30 day free trial period on {paydate} and thereafter "
                   "annually on that date.")
        TOS_LINK = (f"""<a href="{reverse_lazy('tos')}" """ 
                     """target="_blank">Terms of Service</a>""")
        PP_LINK = (f"""<a href="{reverse_lazy('privacy')}" """ 
                    """target="_blank">Privacy Policy</a>""")
        self.fields["tos"].label = mark_safe(_("I have read and agree to the "
                                               f"{TOS_LINK} and {PP_LINK}"))
                
        self.helper = FormHelper()
        self.helper.form_id = "signup_form"
        self.helper.form_class = "signup"
        self.helper.form_method = "post"
        self.helper.form_action = "account_signup"
        
        self.helper.layout = Layout(
            "email",
            "username",
            "password1",
            "password2",
            Div(
                HTML("""<label for="card-element">
                            Payment Information
                     </label>"""),
                Div(css_id="card-element"),
                Div(css_id="card-errors", role="alert"),
                HTML(f'<div id="pay-info">{payinfo}</div>'),
                css_class="form-group"
            ),
            "tos",
            Submit("signup", "&raquo; Signup"),
        )

    class Media:
        js = (settings.STATIC_URL + "js/signup.js",)

    def save(self, request):
        user = super().save(request)
        return user
