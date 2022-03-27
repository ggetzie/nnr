from django.contrib import admin
from django.db.models import Count
from recipes.models import Recipe, Tag, RecipePhoto


class RecipePhotoInline(admin.TabularInline):
    model = RecipePhoto


class RecipeHasPhotosFilter(admin.SimpleListFilter):
    title = "Recipe Photos"
    parameter_name = "has_photos"

    def lookups(self, request, model_admin):
        return (("yes", "has photos"), ("no", "no photos"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.annotate(num_photos=Count("recipephoto")).filter(
                num_photos__gt=0
            )
        elif self.value() == "no":
            return queryset.annotate(num_photos=Count("recipephoto")).filter(
                num_photos=0
            )
        else:
            return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "username", "created_dt", "approved"]
    list_editable = ["approved"]
    list_filter = ["approved", RecipeHasPhotosFilter]
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
    list_filter = ["hashtag", ("photo", admin.EmptyFieldListFilter)]
