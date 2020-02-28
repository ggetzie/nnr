# Comment urls. Included with prefix "/comments"
from django.urls import path

import comments.views as views

app_name = "comments"

urlpatterns = [
    path("list/",
         view=views.list_comments,
         name="list"),
    path("add/",
         view=views.add_comment,
         name="add"),
    path("edit/",
         view=views.edit_comment,
         name="edit"),
    path("delete/",
         view=views.delete_comment,
         name="delete")
]