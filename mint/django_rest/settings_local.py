# Settings to run the django rbuilder project locally.

import os

# First, import everything from the production settings_common.py
from mint.django_rest.settings_common import *  # pyflakes=ignore

ROOT_URLCONF = 'mint.django_rest.urls_local'

# Override individual options
DEBUG = True
DATABASE_ENGINE = 'sqlite3'                  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.

try:
    DATABASE_NAME = os.environ['MINT_LOCAL_DB']  # Or path to database file if using sqlite3.
except:
    DATABASE_NAME = os.path.realpath('../mint-local.db')
TEST_DATABASE_NAME = '../test-mint-local.db'

AUTHENTICATION_BACKENDS = (
    'mint.django_rest.rbuilder.auth.rBuilderBackend',
    'django.contrib.auth.backends.ModelBackend'
)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'mint.django_rest.middleware.LocalQueryParameterMiddleware',
    'mint.django_rest.middleware.ExceptionLoggerMiddleware',
)

# Custom setting for if we should manage/create the tables in rbuilder.models
MANAGE_RBUILDER_MODELS = True
