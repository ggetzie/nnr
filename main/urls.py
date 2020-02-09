# included in config.urls with prefix "main"
from django.urls import include, path, register_converter
import main.views as views

app_name = "main"

urlpatterns = [
    path("public_key/", views.public_key, name="public_key"),
    path("webhook/", views.webhook, name="webhook"),
    ]
