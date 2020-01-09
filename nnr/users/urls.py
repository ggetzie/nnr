from django.urls import path

from nnr.users.views import (
    user_redirect_view,
    user_update_view,
    user_detail_view,
)

from main.views import (
    SavedRecipeList,
    SubmittedRecipeList,
    RatedRecipeList,
    update_payment
)

app_name = "users"
urlpatterns = [
     path("~redirect/", view=user_redirect_view, name="redirect"),
     path("~update/", view=user_update_view, name="update"),
     path("~update_payment",
         view=update_payment,
         name="update_payment"),   
     path("<str:username>/", view=user_detail_view, name="detail"),
     path("<str:username>/saved/", 
          view=SavedRecipeList.as_view(), 
          name="saved_recipes"),
     path("<str:username>/submitted/", 
          view=SubmittedRecipeList.as_view(), 
          name="submitted_recipes"),
     path("<str:username>/rated/",
          view=RatedRecipeList.as_view(),
          name="rated_recipes"),
    
]
