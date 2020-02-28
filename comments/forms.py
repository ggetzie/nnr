from crispy_forms.bootstrap import (InlineField, FormActions, 
                                    FieldWithButtons)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Fieldset, Div, HTML, Field

from django import forms
from django.urls import reverse

from comments.models import Comment

class CreateCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text", "recipe", "user")
        widgets = {
            "text": forms.Textarea(attrs={"rows": 5}),
            "recipe": forms.HiddenInput(),
            "user": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "addCommentForm"
        self.helper.form_action = reverse("comments:add")
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            "text",
            "recipe",
            "user",
            Div(
                Submit("comment", "Comment"),
                css_class="form-actions"
            )
        )
