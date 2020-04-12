# included in config.urls with prefix "main"
from django.urls import include, path, register_converter
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
import main.views as views

app_name = "main"

urlpatterns = [
    path("public_key/", views.public_key, name="public_key"),
    path("webhook/", views.webhook, name="webhook"),
    path("create-checkout-session/", 
         views.create_checkout_session, 
         name="create_checkout_session"),
    path("success/", 
         views.checkout_success,
         name="checkout_success"),
    path("cancel_checkout/",
         TemplateView.as_view(template_name="main/cancel.html"),
         name="checkout_cancel"),
     path("payment/",
          TemplateView.as_view(template_name="main/payment.html"),
          name="payment"),
     path("cancel_subscription/",
          views.cancel_subscription,
          name="cancel_subscription"),
     path("reactivate/",
          views.reactivate_subscription,
          name="reactivate_subscription"),
     path("expired/",
          cache_page(60*60*24)(TemplateView.as_view(template_name="main/expired.html")),
          name="expired"),
     path("processing/",
          cache_page(60*60*24)(TemplateView.as_view(template_name="main/processing.html")),
          name="processing"),
    ]
