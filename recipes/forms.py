from crispy_forms.bootstrap import InlineField, FormActions, FieldWithButtons
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field

from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from recipes.models import Recipe, Tag, UserTag, RecipeRating, RATING_CHOICES
import logging

User = get_user_model()
DUPE_MSG = "A recipe with that title already exists!"
logger = logging.getLogger(__name__)
TAGS_HELP = (
    "Short, descriptive words or phrases, separated by commas. "
    "For example: healthy, cheap, dessert, side dish"
)


class CreateRecipeForm(forms.ModelForm):
    tags = forms.CharField(label="Tags", required=False, help_text=TAGS_HELP)

    class Meta:
        model = Recipe
        fields = (
            "title",
            "ingredients_text",
            "instructions_text",
            "user",
            "quantity_text",
        )
        widgets = {"user": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "recipes:recipe_create"
        self.helper.attrs = {"id": "recipe-form", "autocomplete": "off"}
        self.helper.layout = Layout(
            Div(
                Field("title", wrapper_class="form-group col-md-8"),
                css_class="form-row",
            ),
            Div(
                Field("quantity_text", wrapper_class="form-group col-md-4"),
                css_class="form-row",
            ),
            Div(
                Field("ingredients_text", wrapper_class="form-group col-md-4"),
                Field("instructions_text", wrapper_class="form-group col-md-8"),
                css_class="form-row",
            ),
            Div(
                Field("tags", wrapper_class="form-group col-md-8 autocomplete"),
                css_class="form-row",
            ),
            "user",
            FormActions(Submit("submit", "Submit", css_class="float-right")),
        )

    def save(self):
        user = self.cleaned_data["user"]
        r = Recipe(
            title=self.cleaned_data["title"],
            ingredients_text=self.cleaned_data["ingredients_text"],
            instructions_text=self.cleaned_data["instructions_text"],
            user=user,
            quantity_text=self.cleaned_data["quantity_text"],
        )
        r.approved = user.is_staff
        r.save()
        # for each tag, get it and add it to the recipe, creating a new one if
        # it doesn't exist
        if self.cleaned_data["tags"]:
            tags = [
                Tag.objects.get_or_create(
                    name_slug=slugify(tag), defaults={"name": tag.strip()}
                )[0]
                for tag in self.cleaned_data["tags"].split(",")
            ]
            usertags = [
                UserTag(recipe=r, user=self.cleaned_data["user"], tag=tag)
                for tag in tags
            ]
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
        fields = ("title", "quantity_text", "ingredients_text", "instructions_text")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = ""
        self.helper.attrs = {"id": "recipe-form"}
        self.helper.layout = Layout(
            Div(
                Field("title", wrapper_class="form-group col-md-8"),
                css_class="form-row",
            ),
            Div(
                Field("quantity_text", wrapper_class="form-group col-md-4"),
                css_class="form-row",
            ),
            Div(
                Field("ingredients_text", wrapper_class="form-group col-md-4"),
                Field("instructions_text", wrapper_class="form-group col-md-8"),
                css_class="form-row",
            ),
            FormActions(Submit("submit", "Submit", css_class="btn btn-primary")),
        )

    def save(self):
        r = self.instance
        r.title = self.cleaned_data["title"]
        r.ingredients_text = self.cleaned_data["ingredients_text"]
        r.instructions_text = self.cleaned_data["instructions_text"]
        r.quantity_text = self.cleaned_data["quantity_text"]
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
        # make sure lines end with two spaces to keep line breaks
        lines = self.cleaned_data["ingredients_text"].split("\n")
        return "\n".join([f"{ing.strip()}  " for ing in lines])


class TagRecipeForm(forms.Form):
    tags = forms.CharField(label="Tags", help_text=TAGS_HELP)
    user = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=User.objects.all()
    )
    recipe = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=Recipe.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "recipes:tag_recipe"
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap4/layout/inline_field.html"
        self.helper.layout = Layout(
            Div(
                Div(
                    InlineField("tags", css_class="form-control-sm"),
                    "recipe",
                    "user",
                    css_class="col-sm-10",
                ),
                Div(
                    Submit("Add Tags", "Add Tags", css_class="btn-sm"),
                    css_class="col-sm-2",
                ),
                css_class="form-row",
            ),
        )

    def save_tags(self):
        tags = [
            Tag.objects.get_or_create(
                name_slug=slugify(tag), defaults={"name": tag.strip()}
            )[0]
            for tag in self.cleaned_data["tags"].split(",")
        ]
        recipe = self.cleaned_data["recipe"]
        user = self.cleaned_data["user"]
        for tag in tags:
            usertag = UserTag.objects.get_or_create(recipe=recipe, user=user, tag=tag)[
                0
            ]
            usertag.save()


class UntagRecipeForm(forms.Form):
    recipe = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=Recipe.objects.all()
    )
    tag_slug = forms.SlugField(widget=forms.HiddenInput())


class SaveRecipeForm(forms.Form):
    recipe = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=Recipe.objects.all()
    )
    user = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=User.objects.all()
    )

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
    rating = forms.ChoiceField(choices=RATING_CHOICES, label="Rating", initial=5)
    recipe = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=Recipe.objects.all()
    )
    user = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=User.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "recipes:rate_recipe"
        self.helper.form_class = "form-inline"
        self.helper.field_template = "bootstrap4/layout/inline_field.html"
        self.helper.layout = Layout(
            Div(
                Div(
                    InlineField("rating", css_class="form-control-sm"),
                    "recipe",
                    "user",
                    css_class="col-sm-8",
                ),
                Div(Submit("Rate", "Rate", css_class="btn-sm"), css_class="col-sm-2"),
                css_class="form-row",
            )
        )

    def rate_recipe(self):

        defaults = {"rating": self.cleaned_data["rating"]}
        recipe = self.cleaned_data["recipe"]
        user = self.cleaned_data["user"]
        rr = RecipeRating.objects.update_or_create(
            recipe=recipe, user=user, defaults=defaults
        )[0]


class RecipeSearchForm(forms.Form):
    terms = forms.CharField(label="Search for")

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
        self.fields["terms"].label = False
