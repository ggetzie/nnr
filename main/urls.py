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
    path("<slug:slug>/",
         view=views.RecipeDetail.as_view(),
         name="recipe_detail"),         
]

urlpatterns = [
    path("recipes/", include(recipe_urls)),
]


