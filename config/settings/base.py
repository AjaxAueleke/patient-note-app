# ruff: noqa: ERA001, E501
"""Base settings to build other settings files upon."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# pulse_ai/
APPS_DIR = BASE_DIR / "pulse_ai"
env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#languages
# from django.utils.translation import gettext_lazy as _
# LANGUAGES = [
#     ('en', _('English')),
#     ('fr-fr', _('French')),
#     ('pt-br', _('Portuguese')),
# ]
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL", default="postgres:///pulse_ai", ), }
DATABASES["default"]["ATOMIC_REQUESTS"] = True
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.sites",
               "django.contrib.messages", "django.contrib.staticfiles",
               # "django.contrib.humanize", # Handy template tags
               "django.contrib.admin", "django.forms", ]
THIRD_PARTY_APPS = ["crispy_forms", "crispy_bootstrap5", "allauth", "allauth.account", "allauth.mfa",
                    "allauth.socialaccount", "rest_framework", "rest_framework.authtoken", "corsheaders",
                    "drf_spectacular", ]

LOCAL_APPS = ["pulse_ai.users", "pulse_ai.therapist_session", ]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "pulse_ai.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend",
                           "allauth.account.auth_backends.AuthenticationBackend", ]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "users:redirect"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [  # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher", "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher", "django.contrib.auth.hashers.BCryptSHA256PasswordHasher", ]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
                            {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
                            {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
                            {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}, ]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
              "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.locale.LocaleMiddleware",
              "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
              "django.contrib.auth.middleware.AuthenticationMiddleware",
              "django.contrib.messages.middleware.MessageMiddleware",
              "django.middleware.clickjacking.XFrameOptionsMiddleware",
              "allauth.account.middleware.AccountMiddleware", ]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = ["django.contrib.staticfiles.finders.FileSystemFinder",
                       "django.contrib.staticfiles.finders.AppDirectoriesFinder", ]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [{  # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
    "DIRS": [str(APPS_DIR / "templates")],  # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
    "APP_DIRS": True, "OPTIONS": {  # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
        "context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request",
                               "django.contrib.auth.context_processors.auth", "django.template.context_processors.i18n",
                               "django.template.context_processors.media", "django.template.context_processors.static",
                               "django.template.context_processors.tz",
                               "django.contrib.messages.context_processors.messages",
                               "pulse_ai.users.context_processors.allauth_settings", ], }, }, ]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"
# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend", )
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""Muhammad Ahmed""", "ahmed.jamil7410@gmail.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# https://cookiecutter-django.readthedocs.io/en/latest/settings.html#other-environment-settings
# Force the `admin` sign in process to go through the `django-allauth` workflow
DJANGO_ADMIN_FORCE_ALLAUTH = env.bool("DJANGO_ADMIN_FORCE_ALLAUTH", default=False)

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {"version": 1, "disable_existing_loggers": False, "formatters": {
    "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s", }, },
           "handlers": {"console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose", }, },
           "root": {"level": "INFO", "handlers": ["console"]}, }

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "email"
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_USERNAME_REQUIRED = False
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_ADAPTER = "pulse_ai.users.adapters.AccountAdapter"
# https://docs.allauth.org/en/latest/account/forms.html
ACCOUNT_FORMS = {"signup": "pulse_ai.users.forms.UserSignupForm"}
# https://docs.allauth.org/en/latest/socialaccount/configuration.html
SOCIALACCOUNT_ADAPTER = "pulse_ai.users.adapters.SocialAccountAdapter"
# https://docs.allauth.org/en/latest/socialaccount/configuration.html
SOCIALACCOUNT_FORMS = {"signup": "pulse_ai.users.forms.UserSocialSignupForm"}

# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": (
    "rest_framework_simplejwt.authentication.JWTAuthentication",
   ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema", }

# django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
CORS_URLS_REGEX = r"^/api/.*$"

# By Default swagger ui is available only to admin user(s). You can change permission classes to change that
# See more configuration options at https://drf-spectacular.readthedocs.io/en/latest/settings.html#settings
SPECTACULAR_SETTINGS = {"TITLE": "pulse-ai API", "DESCRIPTION": "Documentation of API endpoints of pulse-ai",
                        "VERSION": "1.0.0", "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"], }
# Your stuff...
# ------------------------------------------------------------------------------

# STORAGES
# ------------------------------------------------------------------------------
# https://django-storages.readthedocs.io/en/latest/#installation
INSTALLED_APPS += ["storages"]
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_ACCESS_KEY_ID = env("S3_AWS_ACCESS_KEY_ID")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_SECRET_ACCESS_KEY = env("S3_AWS_SECRET_ACCESS_KEY")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")

# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_QUERYSTRING_AUTH = False
# DO NOT change these unless you know what you're doing.
_AWS_EXPIRY = 60 * 60 * 24 * 7
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate", }
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_MAX_MEMORY_SIZE = env.int("DJANGO_AWS_S3_MAX_MEMORY_SIZE", default=100_000_000,  # 100MB
                                 )
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_REGION_NAME = env("DJANGO_AWS_S3_REGION_NAME", default=None)
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#cloudfront
AWS_S3_CUSTOM_DOMAIN = env("DJANGO_AWS_S3_CUSTOM_DOMAIN", default=None)
aws_s3_domain = AWS_S3_CUSTOM_DOMAIN or f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# STATIC & MEDIA
# ------------------------
STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage",
                        "OPTIONS": {"location": "media", "file_overwrite": False, }, },
            "staticfiles": {"BACKEND": "storages.backends.s3.S3Storage",
                            "OPTIONS": {"location": "static", "default_acl": "public-read", }, }, }
MEDIA_URL = f"https://{aws_s3_domain}/media/"
COLLECTFAST_STRATEGY = "collectfast.strategies.boto3.Boto3Strategy"
STATIC_URL = f"https://{aws_s3_domain}/static/"

SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(days=10), 'REFRESH_TOKEN_LIFETIME': timedelta(days=300),
              'ROTATE_REFRESH_TOKENS': True, 'BLACKLIST_AFTER_ROTATION': True, }

# SQS

SQS_AWS_ACCESS_KEY_ID = env("SQS_AWS_ACCESS_KEY_ID", default='')
SQS_AWS_SECRET_ACCESS_KEY = env("SQS_AWS_SECRET_ACCESS_KEY", default='')
FUNCTION_QUEUE_AWS_S3_AWS_ACCESS_KEY_ID = env('FUNCTION_QUEUE_AWS_S3_AWS_ACCESS_KEY_ID', default='')
FUNCTION_QUEUE_AWS_S3_AWS_SECRET_ACCESS_KEY = env("FUNCTION_QUEUE_AWS_S3_AWS_SECRET_ACCESS_KEY", default='')
AWS_REGION = env("AWS_REGION", default=None)

CELERY_BROKER_URL = f'sqs://{SQS_AWS_ACCESS_KEY_ID}:{SQS_AWS_SECRET_ACCESS_KEY}@'

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'region': AWS_REGION,
    'polling-interval': 20,
    'visibility_timeout': 300,
    'queue_name_prefix': 'pulse-ai-'
}
SQS_URL = env("SQS_URL", default=None)
