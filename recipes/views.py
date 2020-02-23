from crispy_forms.layout import Submit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.postgres.search import (SearchQuery, 
                                            SearchRank, 
                                            SearchVector)
from django.core.exceptions import PermissionDenied                                            
from django.db.models import Avg, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView, FormView)                                            

from mixins import ValidUserMixin, RateLimitMixin

from recipes.forms import (CreateRecipeForm, UpdateRecipeForm, TagRecipeForm,
                           SaveRecipeForm, RateRecipeForm, RecipeSearchForm,)
                           

from recipes.models import (Recipe, Tag, UserTag, RecipeRating, 
                            LetterCount)

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
        

class RecipeDetail(ValidUserMixin, DetailView):
    model = Recipe
    slug_field = "title_slug"
    context_object_name = "recipe"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = self.object.usertag_set.values("tag").\
               annotate(Count("tag")).\
               order_by("-tag__count")
        tag_list = [(Tag.objects.get(id=tag["tag"]),
                    tag["tag__count"]) for tag in tags]
        context["tag_list"] = tag_list
        context["tagform"] = TagRecipeForm(initial={"user": self.request.user,
                                                    "recipe": self.object})
        saveform = SaveRecipeForm(initial={"user": self.request.user,
                                           "recipe": self.object})                                                        
        if self.object in self.request.user.profile.saved_recipes.all():
            btn = "Unsave"
            css = "btn btn-outline-primary btn-sm"
        else:
            btn = "Save"
            css = "btn btn-primary btn-sm"
        submit = Submit(btn, btn)
        submit.field_classes=css
        saveform.helper.add_input(submit)
        context["saveform"] = saveform

        rate_initial = {"user": self.request.user,
                        "recipe": self.object}
        try:
            rr = RecipeRating.objects.get(recipe=self.object,
                                              user=self.request.user)
            rate_initial["rating"] = rr.rating
        except RecipeRating.DoesNotExist:
            pass

        context["rateform"] = RateRecipeForm(initial=rate_initial)
        context["average_rating"] = RecipeRating.objects.\
                                    filter(recipe=self.object).\
                                    aggregate(Avg("rating"))["rating__avg"]
        return context


class RecipeOfTheDay(DetailView):
    model = Recipe
    context_object_name = "recipe"
    template_name = "recipes/rotd.html"

    def get_object(self, queryset=None):
        return Recipe.objects.get(featured=True)


class RecipeList(ValidUserMixin, ListView):
    model = Recipe
    paginate_by = 25

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
        return (self.request.user.is_staff or 
                self.request.user == self.object.user)        


class DeleteRecipe(UserPassesTestMixin, DeleteView):
    model = Recipe
    success_url = reverse_lazy("recipes:recipe_list")
    slug_field = "title_slug"

    def test_func(self):
        self.object = self.get_object()
        return (self.request.user.is_staff or
                self.request.user == self.object.user)


class TagList(ValidUserMixin, ListView):
    model = Tag
    paginate_by = 144


class TagDetail(ValidUserMixin, ListView):
    model = Recipe
    slug_field = "name_slug"
    paginate_by = 25
    template_name = "recipes/tag_detail.html"

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, name_slug=self.kwargs["slug"])
        qs = Recipe.objects.filter(usertag__tag=self.tag).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context    


class TagRecipe(ValidUserMixin, FormView):
    form_class = TagRecipeForm

    def form_valid(self, form):
        form.save_tags()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("recipes:recipe_detail", kwargs=kw))        


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
        return redirect (reverse_lazy("recipes:recipe_detail", kwargs=kw))        


class SavedRecipeList(UserPassesTestMixin, ListView):
    model = Recipe
    template_name = "users/saved_recipes.html"
    paginate_by = 25

    def test_func(self):
        return (self.request.user.is_staff or
                self.request.user.username == self.kwargs["username"])

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
    paginate_by = 25

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
    paginate_by = 25

    def test_func(self):
        return (self.request.user.is_staff or 
                self.request.user.username == self.kwargs["username"])

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        ratings = (RecipeRating.objects
                   .filter(user=self.user)
                   .order_by("-rating", "recipe__sort_title"))
        return ratings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class RecipeByLetterList(ValidUserMixin, ListView):
    model = Recipe
    paginate_by = 25

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
        context =  super().get_context_data(**kwargs)
        terms = self.request.GET.get("terms", None)
        if terms:
            title_vector = SearchVector("title", weight="A")
            ingredients_vector = SearchVector("ingredients_text", weight="B")
            instructions_vector = SearchVector("instructions_text", weight="B")
            vector = title_vector + ingredients_vector + instructions_vector

            query = SearchQuery(terms)
            results = (Recipe.objects
                      .annotate(search=vector).filter(search=terms)
                      .annotate(rank=SearchRank(vector, query))
                      .order_by("-rank"))
            context["results"] = results
            context["terms"] = terms
        return context                