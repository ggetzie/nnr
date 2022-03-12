from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "nnr_SECRET_KEY",
    default="DYxZ5TboLlYPho9TaGQZSs5ysDy8PJvB04U0aJSNvjJYoXbxb5LrKlQaKo5AKdGk",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "nnr"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend

# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
# EMAIL_HOST = 'localhost'
INSTALLED_APPS += ["anymail"]  # noqa
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"

ANYMAIL = {"AMAZON_SES_CLIENT_PARAMS": {"region_name": "us-east-1"}}
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

# EMAIL_FILE_PATH = '/tmp/nnr_emails'

INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "nnr_db",
        "USER": "nnr_db_user",
        "PASSWORD": env("nnr_DB_PW"),
        "HOST": env("DB_HOST"),
        "PORT": "",
    }
}

DATABASES["default"]["ATOMIC_REQUESTS"] = True

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/usr/local/src/nnr/logs/debug.log",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
    },
    "root": {"level": "INFO", "handlers": ["file"]},
}

# Your stuff...
# ------------------------------------------------------------------------------
