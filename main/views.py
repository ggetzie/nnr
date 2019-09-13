from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView)

from main.models import (Recipe, RecipeRating, Profile, Tag)
from main.forms import RecipeForm

class CreateRecipe(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    
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

