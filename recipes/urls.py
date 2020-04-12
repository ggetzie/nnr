# Recipes urls. Imported with no prefix
from django.urls import include, path, register_converter
from django.views.decorators.cache import cache_page
import recipes.views as views
import recipes.converters as converters

app_name = "recipes"

register_converter(converters.LetterConverter, "letter")

recipe_urls = [
     path("browse", 
          view=cache_page(60*60)(views.RecipeList.as_view()),
          name="recipe_list"),
     path("add/",
          view=views.CreateRecipe.as_view(),
          name="recipe_create"),
     path("edit/<slug:slug>/",
          view=views.UpdateRecipe.as_view(),
          name="recipe_update"),
     path("delete/<slug:slug>/",
         view=views.DeleteRecipe.as_view(),
         name="recipe_delete"),         
     path("save/",
          view=views.SaveRecipe.as_view(),
          name="save_recipe"),         
     path("rate/",
          view=views.RateRecipe.as_view(),
          name="rate_recipe"),
     path("search/",
          view=cache_page(60*60)(views.SearchRecipes.as_view()),
          name="search_recipes"),
     path("<letter:first_letter>/",
          view=cache_page(60*60)(views.RecipeByLetterList.as_view()),
          name="letter_recipe"),
     path("<slug:slug>/",
          view=cache_page(60*10)(views.RecipeDetail.as_view()),
          name="recipe_detail"),         
]

tag_urls = [
     path("",
          view=cache_page(60*60)(views.TagList.as_view()),
          name="tag_list"),
     path("tagrecipe/",
          view=views.TagRecipe.as_view(),
          name="tag_recipe"),
     path("untag/",
          view=views.untag,
          name="untag"),
     path("<slug:slug>",
          view=cache_page(60*60)(views.TagDetail.as_view()),
          name="tag_detail"),
]

urlpatterns = [
    path("rotd/", 
          view=cache_page(60*60*24)(views.RecipeOfTheDay.as_view()),
          name="rotd"),
     path("home/",
          view=cache_page(60*60)(views.DashboardView.as_view()),
          name="home"),
    path("tags/", include(tag_urls)),
    path("", include(recipe_urls)),    
]