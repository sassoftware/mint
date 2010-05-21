# Settings to run the django rbuilder project locally.

# First, import everything from the production settings.py
from settings import *

ROOT_URLCONF = 'mint.django_rest.urls-local'

# Override individual options
DEBUG = False
DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'mint-local.db'             # Or path to database file if using sqlite3.

appsList = list(INSTALLED_APPS)
appsList.append('django.contrib.admin')
INSTALLED_APPS = tuple(appsList)
