from django.urls import path

from nnr.users.views import (
    user_redirect_view,
    user_update_view,
    user_detail_view,
)

from main.views import (
    SavedRecipeList,
    SubmittedRecipeList
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    path("<str:username>/saved", 
         view=SavedRecipeList.as_view(), 
         name="saved_recipes"),
    path("<str:username>/submitted", 
         view=SubmittedRecipeList.as_view(), 
         name="submitted_recipes"),
]
