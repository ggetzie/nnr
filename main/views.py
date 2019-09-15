from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView)

from main.models import (Recipe, RecipeRating, Profile, Tag)
from main.forms import CreateRecipeForm, UpdateRecipeForm

class CreateRecipe(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = CreateRecipeForm
    
    def get_initial(self):
        initial = super().get_initial()
        initial["user"] = self.request.user
        return initial


class RecipeDetail(LoginRequiredMixin, DetailView):
    model = Recipe
    slug_field = "title_slug"
    context_object_name = "recipe"


class RecipeList(LoginRequiredMixin, ListView):
    model = Recipe


class UpdateRecipe(UserPassesTestMixin, UpdateView):
    model = Recipe
    form_class = UpdateRecipeForm
    slug_field = "title_slug"

    def test_func(self):
        return (self.request.user.is_staff or 
                self.request.user == self.object.user)


class DeleteRecipe(UserPassesTestMixin, DeleteView):
    model = Recipe
    success_url = reverse_lazy("main:recipe_list")
    slug_field = "title_slug"

    def test_func(self):
        return (self.request.user.is_staff or
                self.request.user == self.object.user)