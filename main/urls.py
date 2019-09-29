# included in config.urls with prefix "main"
from django.urls import include, path
import main.views as views

app_name = "main"

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
    path("recipes/", include(recipe_urls)),
    path("tags/", include(tag_urls)),
]


