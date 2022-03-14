import json

from crispy_forms.layout import Submit

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    DetailView,
    FormView,
    TemplateView,
)

from mixins import ValidUserMixin, RateLimitMixin

from comments.forms import CreateCommentForm
from decorators import user_is_valid_api
from recipes.forms import (
    CreateRecipeForm,
    UpdateRecipeForm,
    TagRecipeForm,
    SaveRecipeForm,
    RateRecipeForm,
    RecipeSearchForm,
    UntagRecipeForm,
)


from recipes.models import (
    Recipe,
    Tag,
    UserTag,
    RecipeRating,
    LetterCount,
    make_detail_key,
)

import logging

User = get_user_model()

logger = logging.getLogger(__name__)


class CreateRecipe(ValidUserMixin, RateLimitMixin, CreateView):
    model = Recipe
    form_class = CreateRecipeForm

    def get_initial(self):
        initial = super().get_initial()
        initial["user"] = self.request.user
        return initial


class RecipeDetail(DetailView):
    model = Recipe
    slug_field = "title_slug"
    context_object_name = "recipe"

    def get_object(self, queryset=None):
        slug = self.kwargs["slug"]
        recipe_key = make_detail_key(slug)
        self.object = cache.get(recipe_key)
        if not self.object:
            logger.info(f"Cache miss: {recipe_key}")
            self.object = get_object_or_404(Recipe, title_slug=slug)
            cache.set(recipe_key, self.object, 60 * 60 * 24)
        else:
            logger.info(f"Cache hit: {recipe_key}")
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tags = (
            self.object.usertag_set.values("tag__name", "tag__name_slug")
            .annotate(Count("tag"))
            .order_by("-tag__count")
        )

        if self.request.user.is_authenticated:
            # For authenticated users show comments, comment form, tags they've added
            # untag, add tags, save/unsave, submit ratings

            # Comments
            comment_form = CreateCommentForm(
                initial={"user": self.request.user, "recipe": self.object}
            )
            context["comment_form"] = comment_form

            # Tags for logged in users
            user_slugs = {
                tag.name_slug
                for tag in Tag.objects.filter(
                    usertag__user=self.request.user, recipe=self.object
                )
            }
            if tags:

                def add_untag_form(tag_slug):
                    if tag_slug in user_slugs and self.request.user.is_authenticated:
                        return UntagRecipeForm(
                            initial={"tag_slug": tag_slug, "recipe": self.object}
                        )
                    else:
                        return None

                tag_list = [
                    {
                        "name": tag["tag__name"],
                        "slug": tag["tag__name_slug"],
                        "count": tag["tag__count"],
                        "untag_form": add_untag_form(tag["tag__name_slug"]),
                    }
                    for tag in tags
                ]

                # Put user's own tags first (ones that have option to untag)
                tag_list.sort(key=lambda x: x["untag_form"] is None)
            else:
                tag_list = []

            context["tagform"] = TagRecipeForm(
                initial={"user": self.request.user, "recipe": self.object}
            )

            # Save / Unsave
            saveform = SaveRecipeForm(
                initial={"user": self.request.user, "recipe": self.object}
            )
            if self.object in self.request.user.profile.saved_recipes.all():
                btn = "Unsave"
                css = "btn btn-outline-primary btn-sm"
            else:
                btn = "Save"
                css = "btn btn-primary btn-sm"
            submit = Submit(btn, btn)
            submit.field_classes = css
            saveform.helper.add_input(submit)
            context["saveform"] = saveform

            # Rating form
            rate_initial = {"user": self.request.user, "recipe": self.object}
            try:
                rr = RecipeRating.objects.get(
                    recipe=self.object, user=self.request.user
                )
                rate_initial["rating"] = rr.rating
            except RecipeRating.DoesNotExist:
                pass

            context["rateform"] = RateRecipeForm(initial=rate_initial)

        else:
            # Users not logged in get tags only
            tag_list = [
                {
                    "name": tag["tag__name"],
                    "slug": tag["tag__name_slug"],
                    "count": tag["tag__count"],
                }
                for tag in tags
            ]

        # Everyone gets a list of tags and the recipe rating
        context["tag_list"] = tag_list

        context["average_rating"] = RecipeRating.objects.filter(
            recipe=self.object
        ).aggregate(Avg("rating"))["rating__avg"]
        recipe_photos = self.object.recipephoto_set.filter(approved=True)
        tag_photos = Tag.objects.filter(
            photo__isnull=False, usertag__recipe=self.object
        )
        context["photos"] = recipe_photos or tag_photos
        return context


class RecipeOfTheDay(DetailView):
    model = Recipe
    context_object_name = "recipe"
    template_name = "recipes/rotd.html"

    def get_object(self, queryset=None):
        try:
            obj = Recipe.objects.get(featured=True)
        except Recipe.DoesNotExist:
            obj = None
        return obj


class RecipeList(ListView):
    model = Recipe
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lettercounts"] = LetterCount.objects.all()
        context["title"] = "All Recipes"
        return context


class UpdateRecipe(UserPassesTestMixin, UpdateView):
    model = Recipe
    form_class = UpdateRecipeForm
    slug_field = "title_slug"

    def test_func(self):
        self.object = self.get_object()
        return self.request.user.is_staff or self.request.user == self.object.user


class DeleteRecipe(UserPassesTestMixin, DeleteView):
    model = Recipe
    success_url = reverse_lazy("recipes:recipe_list")
    slug_field = "title_slug"

    def test_func(self):
        self.object = self.get_object()
        return self.request.user.is_staff or self.request.user == self.object.user


class TagList(ListView):
    model = Tag
    paginate_by = 150

    def get_queryset(self):
        qs = (
            Tag.objects.annotate(ut_count=Count("usertag"))
            .filter(ut_count__gt=0)
            .order_by("name_slug")
        )
        return qs


class TagDetail(ListView):
    model = Recipe
    slug_field = "name_slug"
    paginate_by = 50
    template_name = "recipes/tag_detail.html"

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, name_slug=self.kwargs["slug"])
        qs = Recipe.objects.filter(usertag__tag=self.tag).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context


class UserTagList(ValidUserMixin, ListView):
    model = Tag
    paginate_by = 144
    template_name = "users/usertag_list.html"

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        qs = Tag.objects.filter(usertag__user=self.profile_user).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.profile_user
        return context


class UserTagDetail(ValidUserMixin, ListView):
    model = Recipe
    paginate_by = 50
    template_name = "users/usertag_detail.html"

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        self.tag = get_object_or_404(Tag, name_slug=self.kwargs["tag_slug"])
        qs = Recipe.objects.filter(
            usertag__tag=self.tag, usertag__user=self.profile_user
        ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        context["profile_user"] = self.profile_user
        return context


class TagRecipe(ValidUserMixin, FormView):
    form_class = TagRecipeForm

    def form_valid(self, form):
        form.save_tags()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("recipes:recipe_detail", kwargs=kw))


@user_is_valid_api
@require_POST
def untag(request):
    form = UntagRecipeForm(json.loads(request.body))
    if form.is_valid():
        try:
            ut = UserTag.objects.get(
                user=request.user,
                recipe=form.cleaned_data["recipe"],
                tag__name_slug=form.cleaned_data["tag_slug"],
            )
            ut.delete()
            response = {"message": "Tag Removed"}
        except UserTag.DoesNotExist:
            response = {"error": "Tag does not exist"}
    else:
        response = {"error": form.errors}
    return JsonResponse(response)


class SaveRecipe(ValidUserMixin, FormView):
    form_class = SaveRecipeForm

    def form_valid(self, form):
        if not self.request.user == form.cleaned_data["user"]:
            raise PermissionDenied
        form.save_recipe()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("recipes:recipe_detail", kwargs=kw))


class RateRecipe(ValidUserMixin, FormView):
    form_class = RateRecipeForm

    def form_valid(self, form):
        if not self.request.user == form.cleaned_data["user"]:
            raise PermissionDenied
        form.rate_recipe()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("recipes:recipe_detail", kwargs=kw))


class SavedRecipeList(UserPassesTestMixin, ListView):
    model = Recipe
    template_name = "users/saved_recipes.html"
    paginate_by = 50

    def test_func(self):
        return (
            self.request.user.is_staff
            or self.request.user.username == self.kwargs["username"]
        )

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        qs = self.user.profile.saved_recipes.all()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class SubmittedRecipeList(ValidUserMixin, ListView):
    model = Recipe
    template_name = "users/submitted_recipes.html"
    paginate_by = 50

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        qs = Recipe.objects.filter(user=self.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class RatedRecipeList(UserPassesTestMixin, ListView):
    model = RecipeRating
    template_name = "users/rated_recipes.html"
    paginate_by = 50

    def test_func(self):
        return (
            self.request.user.is_staff
            or self.request.user.username == self.kwargs["username"]
        )

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        ratings = RecipeRating.objects.filter(user=self.user).order_by(
            "-rating", "recipe__sort_title"
        )
        return ratings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class RecipeByLetterList(ListView):
    model = Recipe
    paginate_by = 50

    def get_queryset(self):
        qs = Recipe.objects.filter(first_letter=self.kwargs["first_letter"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f'"{self.kwargs["first_letter"]}" Recipes'
        context["lettercounts"] = LetterCount.objects.all()
        context["current"] = self.kwargs["first_letter"]
        return context


class SearchRecipes(ValidUserMixin, FormView):
    form_class = RecipeSearchForm
    template_name = "recipes/search.html"
    success_url = reverse_lazy("recipes:search_recipes")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        terms = self.request.GET.get("terms", None)
        if terms:
            title_vector = SearchVector("title", weight="A")
            ingredients_vector = SearchVector("ingredients_text", weight="B")
            instructions_vector = SearchVector("instructions_text", weight="B")
            vector = title_vector + ingredients_vector + instructions_vector

            query = SearchQuery(terms, config="pg_catalog.english")
            results = (
                Recipe.objects.filter(search_vector=query)
                .annotate(rank=SearchRank(vector, query))
                .order_by("-rank")
            )
            paginator = Paginator(results, 50)
            page_obj = paginator.page(self.request.GET.get("page", 1))

            tag_results = Tag.objects.filter(name__search=query)

            context["page_obj"] = page_obj
            context["terms"] = terms
            context["tag_results"] = tag_results
        return context


class DashboardView(ValidUserMixin, TemplateView):
    template_name = "recipes/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        saved_none = """
    Looks like you haven't saved any recipes yet. Try clicking the "Save" button
    at the bottom of a recipe page to quickly find it later.
    """
        context.update(
            {
                "recent": Recipe.objects.order_by("-created_dt", "-id")[:5],
                "highest": (
                    Recipe.objects.filter(reciperating__isnull=False)
                    .annotate(average_rating=Avg("reciperating__rating"))
                    .order_by("-average_rating")[:5]
                ),
                "saved": self.request.user.profile.saved_recipes.all(),
                "user_tags": (
                    Tag.objects.filter(usertag__user=self.request.user)
                    .annotate(numtags=Count("name_slug"))
                    .order_by("-numtags")
                )[:10],
                "saved_none": saved_none,
            }
        )
        return context


@user_is_valid_api
def all_tags(request):
    qs = Tag.objects.annotate(ut_count=Count("usertag")).filter(ut_count__gt=0)
    return JsonResponse({"tag_list": [t.name for t in qs]})
