from django.contrib import admin
from recipes.models import Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "username", "created_dt", "approved"]
    list_editable = ["approved"]
    exclude = [
        "search_vector",
        "ingredients_html",
        "instructions_html",
        "quantity_html",
        "title_slug",
    ]
    ordering = ["-created_dt"]

    def username(self, obj):
        return obj.user.username


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    exclude = ["name_slug"]
    list_display = ["name", "hashtag"]
    list_editable = ["hashtag"]
