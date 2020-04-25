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

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "nnr"
    }
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend

# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
# EMAIL_HOST = 'localhost'
INSTALLED_APPS += ["anymail"] # noqa
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")

EMAIL_BACKEND = 'anymail.backends.amazon_ses.EmailBackend'

ANYMAIL = {
    "AMAZON_SES_CLIENT_PARAMS": {
        "region_name": "us-east-1"
    }
}
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="No Nonsense Recipes <support@nononsense.recipes>"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = "server@nononsense.recipes"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX", default="[No Nonsense Recipes]"
)

# EMAIL_FILE_PATH = '/tmp/nnr_emails'

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa F405

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nnr_db',
        'USER': 'nnr_db_user',
        'PASSWORD': env('nnr_DB_PW'),
        'HOST': 'localhost',
        'PORT': '',
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
STATICFILES_STORAGE = "pipeline.storage.PipelineCachedStorage"
PIPELINE = {
    "PIPELINE_ENABLED": True,
    "STYLESHEETS": {
        "styles": {
            "source_filenames": (
                "css/*.css",
            ),
            "output_filename": "css/nnr.css",
            "extra_context": {
                "media": "screen,projection",
            },
                
        },
    },
    "JAVASCRIPT": {
        "scripts": {
            "source_filenames": (
                "js/*.js",
            ),
            "output_filename": "js/nnr.js"
        }
    }
}
