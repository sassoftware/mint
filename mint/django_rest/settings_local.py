# Settings to run the django rbuilder project locally.

import os

# First, import everything from the production settings_common.py
from mint.django_rest.settings_common import *  # pyflakes=ignore

ROOT_URLCONF = 'mint.django_rest.urls_local'

# Override individual options
DEBUG = True
DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
DATABASES['default']['NAME'] = os.environ.get('MINT_LOCAL_DB',
    os.path.realpath('../mint-local.db'))
TEST_DATABASE_NAME = os.path.realpath('../test-mint-local.db')

AUTHENTICATION_BACKENDS = (
    'mint.django_rest.rbuilder.auth.rBuilderBackend',
    'django.contrib.auth.backends.ModelBackend'
)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
    ('mint.django_rest.middleware.LocalQueryParameterMiddleware',)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
    ('mint.django_rest.middleware.LocalSetMintAdminMiddleware',)

installedAppsList = list(INSTALLED_APPS)
installedAppsList.append('mint.django_rest.sdk_builder')
INSTALLED_APPS = tuple(installedAppsList)

