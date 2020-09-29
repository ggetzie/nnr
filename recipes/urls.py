# Recipes urls. Imported with no prefix
from django.urls import include, path, register_converter
import recipes.views as views
import recipes.converters as converters

app_name = "recipes"

register_converter(converters.LetterConverter, "letter")

recipe_urls = [
     path("browse", 
          view=views.RecipeList.as_view(),
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
          view=views.SearchRecipes.as_view(),
          name="search_recipes"),
     path("<letter:first_letter>/",
          view=views.RecipeByLetterList.as_view(),
          name="letter_recipe"),
     path("<slug:slug>/",
          view=views.RecipeDetail.as_view(),
          name="recipe_detail"),         
]

tag_urls = [
     path("",
          view=views.TagList.as_view(),
          name="tag_list"),
     path("tagrecipe/",
          view=views.TagRecipe.as_view(),
          name="tag_recipe"),
     path("untag/",
          view=views.untag,
          name="untag"),
     path("all/",
          view=views.all_tags,
          name="get_all_tags"),
     path("<slug:slug>",
          view=views.TagDetail.as_view(),
          name="tag_detail"),
]

urlpatterns = [
    path("rotd/", 
          view=views.RecipeOfTheDay.as_view(),
          name="rotd"),
     path("home/",
          view=views.DashboardView.as_view(),
          name="home"),
    path("tags/", include(tag_urls)),
    path("", include(recipe_urls)),    
]
