from django import forms
from django.utils.translation import ugettext_lazy as _

from main.models import Recipe

class SignupForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=200)
    title = forms.CharField(label=_("Title"), max_length=100)
    ingredients = forms.CharField(label=_("Ingredients"),
                                  widget=forms.widgets.Textarea)

    instructions = forms.CharField(label=_("Instructions"), 
                                   widget=forms.widgets.Textarea)

    def signup(self, request, user):
        recipe = Recipe(title=self.cleaned_data["title"],
                        ingredients_text=self.cleaned_data["ingredients"],
                        instructions_text=self.cleaned_data["instructions"],
                        user=user)
        recipe.save()

        return user
    