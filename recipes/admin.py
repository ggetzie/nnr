from django.contrib import admin
from recipes.models import Recipe, Tag, RecipePhoto


class RecipePhotoInline(admin.TabularInline):
    model = RecipePhoto


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "username", "created_dt", "approved"]
    list_editable = ["approved"]
    list_filter = ["approved"]
    autocomplete_fields = ["see_also"]
    search_fields = ["title"]
    exclude = [
        "search_vector",
        "ingredients_html",
        "instructions_html",
        "quantity_html",
        "title_slug",
        "featured",
        "last_featured",
    ]
    ordering = ["-created_dt"]
    inlines = [RecipePhotoInline]

    def username(self, obj):
        return obj.user.username


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    exclude = ["name_slug"]
    list_display = ["name", "hashtag"]
    list_editable = ["hashtag"]
