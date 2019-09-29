from crispy_forms.layout import Submit

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView, FormView)

from main.models import (Recipe, RecipeRating, Profile, Tag, UserTag)
from main.forms import (CreateRecipeForm, UpdateRecipeForm, TagRecipeForm,
                        SaveRecipeForm, RateRecipeForm)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usertags"] = UserTag.objects.filter(user=self.request.user,
                                                     recipe=self.object)
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
        context["rateform"] = RateRecipeForm(initial={"user": self.request.user,
                                                      "recipe": self.object})                                                                                                              
        return context


class RecipeList(LoginRequiredMixin, ListView):
    model = Recipe
    paginate_by = 25


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


class TagList(LoginRequiredMixin, ListView):
    model = Tag
    paginate_by = 144


class TagDetail(LoginRequiredMixin, DetailView):
    model = Tag
    slug_field = "name_slug"
    context_object_name = "tag"


class TagRecipe(LoginRequiredMixin, FormView):
    form_class = TagRecipeForm

    def form_valid(self, form):
        form.save_tags()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("main:recipe_detail", kwargs=kw))


class SaveRecipe(LoginRequiredMixin, FormView):
    form_class = SaveRecipeForm

    def form_valid(self, form):
        if not self.request.user == form.cleaned_data["user"]:
            raise PermissionDenied        
        form.save_recipe()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("main:recipe_detail", kwargs=kw))


class RateRecipe(LoginRequiredMixin, FormView):
    form_class = RateRecipeForm

    def form_valid(self, form):
        if not self.request.user == form.cleaned_data["user"]:
            raise PermissionDenied
        form.rate_recipe()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect (reverse_lazy("main:recipe_detail", kwargs=kw))