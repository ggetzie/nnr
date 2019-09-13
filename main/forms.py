from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from main.models import Recipe, Tag

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

class RecipeForm(forms.ModelForm):
    tags = forms.CharField(label=_("Tags"))
    class Meta:
        model = Recipe
        fields = ("title", "ingredients_text", "instructions_text", "user")
        widgets = {
            "user": forms.HiddenInput()
        }

    def save(self):
        r = Recipe(title=self.cleaned_data["title"],
                   ingredients_text=self.cleaned_data["ingredients_text"],
                   instructions_text=self.cleaned_data["instructions_text"],
                   user=self.cleaned_data["user"])
        r.save()                   
        # for each tag, get it and add it to the recipe, creating a new one if 
        # it doesn't exist

        r.tags.add(*[Tag.objects.get_or_create(name_slug=slugify(tag),
                                              defaults={"name": tag.strip()})[0]
                    for tag in self.cleaned_data["tags"].split(",")])
        r.save()
        return r
    
    def clean_title(self):
        try:
            recipe = Recipe.objects.get(title_slug=slugify(self.cleaned_data["title"]))
            raise forms.ValidationError(
                                _("A recipe with that title already exists!"), 
                                code="duplicate")
        except Recipe.DoesNotExist:
            return self.cleaned_data["title"]
        