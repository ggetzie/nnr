from django.apps import AppConfig


class RecipesConfig(AppConfig):
    name = "recipes"

    def ready(self):
        import recipes.signals

        super().ready()
