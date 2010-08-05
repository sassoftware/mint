# Settings to run the django rbuilder project locally.

# First, import everything from the production settings.py
from mint.django_rest.settings_common import *  # pyflakes=ignore

ROOT_URLCONF = 'mint.django_rest.urls_local'

# Override individual options
DEBUG = False
DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'mint-local.db'             # Or path to database file if using sqlite3.

appsList = list(INSTALLED_APPS)
appsList.append('django.contrib.admin')
INSTALLED_APPS = tuple(appsList)

AUTHENTICATION_BACKENDS = (
    'mint.django_rest.rbuilder.auth.rBuilderBackend',
    'django.contrib.auth.backends.ModelBackend'
)

for i in range(len(MIDDLEWARE_CLASSES)):
    if MIDDLEWARE_CLASSES[i] == \
        'mint.django_rest.middleware.AddCommentsMiddleware':
        break

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES[0:i] + \
                     MIDDLEWARE_CLASSES[i+1:]

# Custom setting for if we should manage/create the tables in rbuilder.models
MANAGE_RBUILDER_MODELS = True
