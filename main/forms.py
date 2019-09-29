from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from main.models import Recipe, Tag, UserTag, RecipeRating

User = get_user_model()
DUPE_MSG = _("A recipe with that title already exists!")

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

    def clean_title(self):
        try:
            slug = slugify(self.cleaned_data["title"])
            recipe = Recipe.objects.get(title_slug=slug)
            raise forms.ValidationError(DUPE_MSG, code="duplicate")
        except Recipe.DoesNotExist:
            return self.cleaned_data["title"]

    def clean_ingredients(self):
        lines = self.cleaned_data["ingredients"].split("\n")
        return "\n".join([f"{ing.strip()}  " for ing in lines])


class CreateRecipeForm(forms.ModelForm):
    tags = forms.CharField(label=_("Tags"), required=False)
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
        if self.cleaned_data["tags"]:
            tags = [Tag.objects.get_or_create(name_slug=slugify(tag), 
                                              defaults={"name": tag.strip()})[0]
                    for tag in self.cleaned_data["tags"].split(",")]
            usertags = [UserTag(recipe=r,
                                user=self.cleaned_data["user"],
                                tag=tag) for tag in tags]
            UserTag.objects.bulk_create(usertags)

        return r
    
    def clean_title(self):
        # check that the title creates a unique slug
        try:
            recipe = Recipe.objects.get(title_slug=slugify(self.cleaned_data["title"]))
            raise forms.ValidationError(DUPE_MSG, code="duplicate")
        except Recipe.DoesNotExist:
            return self.cleaned_data["title"]

    def clean_ingredients_text(self):
        # make sure each ingredient line ends with two spaces
        # so markdown will put them on separate lines
        lines = self.cleaned_data["ingredients_text"].split("\n")
        return "\n".join([f"{ing.strip()}  " for ing in lines])


class UpdateRecipeForm(forms.ModelForm):

    class Meta:
        model = Recipe
        fields = ("title", "ingredients_text", "instructions_text")

    def save(self):
        r = self.instance
        r.title = self.cleaned_data["title"]
        r.ingredients_text = self.cleaned_data["ingredients_text"]
        r.instructions_text = self.cleaned_data["instructions_text"]
        r.save()
        return r

    def clean_title(self):
        # make sure the title doesn't get changed to something that exists
        try:
            slug = slugify(self.cleaned_data["title"])
            recipe = Recipe.objects.exclude(id=self.instance.id).get(title_slug=slug)
            raise forms.ValidationError(DUPE_MSG, code="duplicate")
        except Recipe.DoesNotExist:
            return self.cleaned_data["title"]

    def clean_ingredients_text(self):
        lines = self.cleaned_data["ingredients_text"].split("\n")
        return "\n".join([f"{ing.strip()}  " for ing in lines])

class TagRecipeForm(forms.Form):
    tags = forms.CharField(label=_("Tags"))
    user = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=User.objects.all())
    recipe = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                    queryset=Recipe.objects.all())

    def save_tags(self):
        tags = [Tag.objects.get_or_create(name_slug=slugify(tag), 
                                              defaults={"name": tag.strip()})[0]
                    for tag in self.cleaned_data["tags"].split(",")]
        usertags = [UserTag(recipe=self.cleaned_data["recipe"],
                            user=self.cleaned_data["user"],
                            tag=tag) for tag in tags]
        UserTag.objects.bulk_create(usertags)


class SaveRecipeForm(forms.Form):
    recipe = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                    queryset=Recipe.objects.all())
    user = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=User.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "main:save_recipe"

    def save_recipe(self):
        profile = self.cleaned_data["user"].profile
        recipe = self.cleaned_data["recipe"]
        if recipe in profile.saved_recipes.all():
            profile.saved_recipes.remove(recipe)
        else:
            profile.saved_recipes.add(recipe)
        profile.save()


class RateRecipeForm(forms.Form):
    rating = forms.ChoiceField(choices=((1, "1 Star"),
                                        (2, "2 Stars"),
                                        (3, "3 Stars"),
                                        (4, "4 Stars"),
                                        (5, "5 Stars")),
                                label="Rating")
    recipe = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                    queryset=Recipe.objects.all())
    user = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=User.objects.all())

    def rate_recipe(self):
        
        rr = RecipeRating(rating=self.cleaned_data["rating"],
                          recipe = self.cleaned_data["recipe"],
                          user=self.cleaned_data["user"])
        rr.save()

        