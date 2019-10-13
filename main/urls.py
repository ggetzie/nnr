# included in config.urls with prefix "main"
from django.urls import include, path, register_converter
import main.views as views
import main.converters as converters

app_name = "main"

register_converter(converters.LetterConverter, "letter")

recipe_urls = [
     path("", 
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
     path("saverecipe/",
          view=views.SaveRecipe.as_view(),
          name="save_recipe"),         
     path("raterecipe/",
          view=views.RateRecipe.as_view(),
          name="rate_recipe"),                   
     path("<letter:first_letter>/",
          view=views.RecipebyLetterList.as_view(),
          name="letter_recipe"),
     path("<slug:slug>/",
          view=views.RecipeDetail.as_view(),
          name="recipe_detail"),         
]

tag_urls = [
     path("",
          view=views.TagList.as_view(),
          name="tag_list"),
     path("<slug:slug>",
          view=views.TagDetail.as_view(),
          name="tag_detail"),
     path("tagrecipe/",
          view=views.TagRecipe.as_view(),
          name="tag_recipe"),
]

urlpatterns = [
    path("rotd/", 
          view=views.RecipeOfTheDay.as_view(),
          name="rotd"),
    path("recipes/", include(recipe_urls)),
    path("tags/", include(tag_urls)),
]


