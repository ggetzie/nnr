from crispy_forms.bootstrap import (InlineField, FormActions, 
                                    FieldWithButtons)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Fieldset, Div, HTML, Field

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from main.models import Profile                            
from recipes.models import (Recipe, Tag, UserTag, RecipeRating,
                            RATING_CHOICES)
import datetime                    
import logging



User = get_user_model()
DUPE_MSG = _("A recipe with that title already exists!")
logger = logging.getLogger(__name__)

class CreateRecipeForm(forms.ModelForm):
    tags = forms.CharField(label=_("Tags"), required=False)
    class Meta:
        model = Recipe
        fields = ("title", "ingredients_text", "instructions_text", "user")
        widgets = {
            "user": forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()        
        self.helper.form_method = "post"
        self.helper.form_action = "recipes:recipe_create"
        self.helper.attrs = {"id": "recipe-form"}
        self.helper.layout = Layout(
            HTML("""<p class="text-muted">* = field is required</p>"""),
            Div(
                Field("title", wrapper_class="form-group col-md-12"),
                css_class="form-row"
            ),
            Div(
                Field("ingredients_text", wrapper_class="form-group col-md-6"),
                Field("instructions_text", wrapper_class="form-group col-md-6"),

                css_class="form-row"
            ),
            Div(
                Field("tags", wrapper_class="form-group col-md-12"),
                css_class="form-row"
            ),
            "user",
            FormActions(
                Submit("submit", "Submit", css_class="btn btn-primary")
            )
        )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()        
        self.helper.form_method = "post"
        self.helper.form_action = ""
        self.helper.attrs = {"id": "recipe-form"}
        self.helper.layout = Layout(
            HTML("""<p class="text-muted">* = field is required</p>"""),
            Div(
                Field("title", wrapper_class="form-group col-md-12"),
                css_class="form-row"
            ),
            Div(
                Field("ingredients_text", wrapper_class="form-group col-md-6"),
                Field("instructions_text", wrapper_class="form-group col-md-6"),

                css_class="form-row"
            ),
            FormActions(
                Submit("submit", "Submit", css_class="btn btn-primary")
            )
        )        

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "recipes:tag_recipe"
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap4/layout/inline_field.html"
        self.helper.layout = Layout(
            InlineField("tags", css_class="form-control-sm"),
            "recipe",
            "user",
            Submit("Add Tags", "Add Tags", css_class="btn-sm")
        )        

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
        self.helper.form_action = "recipes:save_recipe"

    def save_recipe(self):
        profile = self.cleaned_data["user"].profile
        recipe = self.cleaned_data["recipe"]
        if recipe in profile.saved_recipes.all():
            profile.saved_recipes.remove(recipe)
        else:
            profile.saved_recipes.add(recipe)
        profile.save()


class RateRecipeForm(forms.Form):
    rating = forms.ChoiceField(choices=RATING_CHOICES,
                                label="Rating",
                                initial=5)
    recipe = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                    queryset=Recipe.objects.all())
    user = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=User.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "recipes:rate_recipe"
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap4/layout/inline_field.html"
        self.helper.layout = Layout(
            InlineField("rating", css_class="form-control-sm"),
            "recipe",
            "user",
            Submit("Rate", "Rate", css_class="btn-sm")
        )
        

    def rate_recipe(self):

        defaults = {"rating": self.cleaned_data["rating"]}
        recipe = self.cleaned_data["recipe"]
        user = self.cleaned_data["user"]
        rr, created = RecipeRating.objects.update_or_create(recipe=recipe,
                                                            user=user,
                                                            defaults=defaults)
        

class RecipeSearchForm(forms.Form):
    terms = forms.CharField(label=_("Search for"))
    
    def search(self):
        return Recipe.objects.all()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.form_action = "recipes:search_recipes"
        self.helper.layout = Layout(
            FieldWithButtons("terms", Submit("search", "Search"))
        )
        self.fields["terms"].label=False