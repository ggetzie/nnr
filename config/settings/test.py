"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="7lt8xamZrLPXOZRYGdR72W5FAK1ps5J79elPz9Uy84mWv8Sz58Yq48EdbyMikkGn",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# DATABASES
# ------------------------------------------------------------------------------
# base.py deliberately defines no DATABASES; local.py and production.py each build
# their own. Tests need one too, or every db-backed test errors out before it runs.
#
# The test runner creates and drops test_<DB_NAME>, which the application role is
# not required to be able to do. Set TEST_DB_USER (and TEST_DB_HOST="" for local
# peer auth) to run as a role that has CREATEDB, without touching the app credentials.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="nnr_db"),
        "USER": env("TEST_DB_USER", default=env("DB_USER", default="")),
        "PASSWORD": env("TEST_DB_PASSWORD", default=env("nnr_DB_PW", default="")),
        "HOST": env("TEST_DB_HOST", default=env("DB_HOST", default="")),
        "PORT": env("DB_PORT", default=""),
    }
}

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# TEMPLATES
# ------------------------------------------------------------------------------
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
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Your stuff...
# ------------------------------------------------------------------------------
# base.py reads the real keys out of .env. Override them here so that a test which
# forgets to stub the stripe module cannot reach the live account.
STRIPE_PK = "pk_test_dummy"
STRIPE_SK = "sk_test_dummy"
