# Settings to run the django rbuilder project locally.

# First, import everything from the production settings.py
from mint.django_rest.settings import *  # pyflakes=ignore

ROOT_URLCONF = 'mint.django_rest.urls_local'

# Override individual options
DEBUG = True
DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = '@SERVER_PATH@/rbuilder/data/db'             # Or path to database file if using sqlite3.

appsList = list(INSTALLED_APPS)
appsList.append('django.contrib.admin')
INSTALLED_APPS = tuple(appsList)

AUTHENTICATION_BACKENDS = (
    'mint.django_rest.rbuilder.auth.rBuilderBackend',
    'django.contrib.auth.backends.ModelBackend'
)

# Custom setting for if we should manage/create the tables in rbuilder.models
MANAGE_RBUILDER_MODELS = True
