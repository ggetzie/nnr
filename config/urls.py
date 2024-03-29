from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views

from recipes.models import Recipe

support_context = {"support_email": settings.SUPPORT_EMAIL}

urlpatterns = [
    path(
        "",
        TemplateView.as_view(
            template_name="pages/home.html",
            extra_context={"recipe_count": Recipe.objects.count()},
        ),
        name="home",
    ),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("nnr.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Custom urls
    path(
        "privacy/",
        TemplateView.as_view(
            template_name="privacy.html", extra_context=support_context
        ),
        name="privacy",
    ),
    path(
        "support",
        TemplateView.as_view(
            template_name="support.html", extra_context=support_context
        ),
        name="support",
    ),
    path(
        "tos/",
        TemplateView.as_view(template_name="tos.html", extra_context=support_context),
        name="tos",
    ),
    path("main/", include("main.urls", namespace="main")),
    path("comments/", include("comments.urls", namespace="comments")),
    path("", include("recipes.urls", namespace="recipes")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
