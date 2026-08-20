from django.apps import AppConfig


class RecipesConfig(AppConfig):
    name = "recipes"

    def ready(self):
        import recipes.signals  # noqa: F401

        # Teach Pillow to open HEIF/HEIC. Django's ImageField validates uploads
        # with Pillow, so without this a HEIC photo is rejected at the form and
        # never reaches the raw S3 bucket -- meaning the nnr-photos Lambda that
        # can decode HEIC would never see one.
        from pillow_heif import register_heif_opener

        register_heif_opener()

        super().ready()
