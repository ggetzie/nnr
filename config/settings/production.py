from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("nnr_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
# ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["nononsense.recipes"])
# ALLOWED_HOSTS = ["172.31.84.146", "35.173.32.90", "nononsense.recipes", "www.nononsense.recipes"]
ALLOWED_HOSTS = ["*"]

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "nnr_db",
        "USER": "nnr_db_user",
        "PASSWORD": env("nnr_DB_PW"),
        "HOST": env("DB_HOST"),
        "PORT": "5432",
    }
}

DATABASES["default"]["ATOMIC_REQUESTS"] = True

# DATABASES = {
#     'default': env.db("DATABASE_URL")
# }
# DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
# DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405


# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_PROXY_SSL_HEADER = None
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
# SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
# SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
# CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
# SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
# SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
#     "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
# )
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
# SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
)

# STORAGES
# ------------------------------------------------------------------------------
# https://django-storages.readthedocs.io/en/latest/#installation
INSTALLED_APPS += ["storages"]  # noqa F405
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_QUERYSTRING_AUTH = False
# DO NOT change these unless you know what you're doing.
# changed to 1 day
_AWS_EXPIRY = 60 * 60 * 24
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate"
}
#  https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_DEFAULT_ACL = None
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_REGION_NAME = env("DJANGO_AWS_S3_REGION_NAME", default=None)

AWS_S3_CUSTOM_DOMAIN = env(
    "AWS_S3_CUSTOM_DOMAIN", default="d1q0lpl7gly8q2.cloudfront.net"
)
AWS_IS_GZIPPED = True

# STATIC
# ------------------------
STATICFILES_STORAGE = "config.settings.production.StaticRootS3Boto3Storage"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
# MEDIA
# ------------------------------------------------------------------------------
# region http://stackoverflow.com/questions/10390244/
# Full-fledge class: https://stackoverflow.com/a/18046120/104731
from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402

# from django.contrib.staticfiles.storage import ManifestFilesMixin
# import pathlib
# import os
# import json


class StaticRootS3Boto3Storage(S3Boto3Storage):
    location = "static"
    default_acl = "public-read"

    # def read_manifest(self):
    #     try:
    #         with open(APPS_DIR.path(f"static/{self.manifest_name}")) as manifest:
    #             return manifest.read().decode()
    #     except FileNotFoundError:
    #         return None

    # def save_manifest(self):
    #     payload = {'paths': self.hashed_files,
    #                'version': self.manifest_version}
    #     manifest_path = pathlib.Path(APPS_DIR.path(f"static/{self.manifest_name}"))
    #     if manifest_path.exists(): os.remove(manifest_path)
    #     contents = json.dumps(payload).encode()
    #     with open(manifest_path, "wb") as manifest_file:
    #         manifest_file.write(contents)


class MediaRootS3Boto3Storage(S3Boto3Storage):
    location = "media"
    file_overwrite = False


# endregion
DEFAULT_FILE_STORAGE = "config.settings.production.MediaRootS3Boto3Storage"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="No Nonsense Recipes <support@nononsense.recipes>",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = "server@nononsense.recipes"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX", default="[No Nonsense Recipes]"
)


# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Anymail (Mailgun)
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
INSTALLED_APPS += ["anymail"]  # noqa F405
EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference

ANYMAIL = {"AMAZON_SES_CLIENT_PARAMS": {"region_name": "us-east-1"}}

# Collectfast
# ------------------------------------------------------------------------------
# https://github.com/antonagestam/collectfast#installation
INSTALLED_APPS = ["collectfast"] + INSTALLED_APPS  # noqa F405
AWS_PRELOAD_METADATA = True

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}

# Your stuff...
# ------------------------------------------------------------------------------
INSTALLED_APPS += ["django_extensions"]
