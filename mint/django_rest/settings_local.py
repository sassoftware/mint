#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


# Settings to run the django rbuilder project locally.

import os

# First, import everything from the production settings_common.py
from mint.django_rest.settings_common import *  # pyflakes=ignore

ROOT_URLCONF = 'mint.django_rest.urls_local'

# Override individual options
DEBUG = True
DATABASES['default'].update(
    ENGINE = 'django.db.backends.postgresql_psycopg2',
    USER = 'testutils',
    PORT = '',
    NAME = os.environ.get('MINT_LOCAL_DB', 'test'),
    TEST_NAME =  'test',
)

AUTHENTICATION_BACKENDS = (
    'mint.django_rest.rbuilder.auth.rBuilderBackend',
    'django.contrib.auth.backends.ModelBackend'
)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'mint.django_rest.middleware.ExceptionLoggerMiddleware',
)

# Commented out misa 2011-07-20 - adding this middleware breaks the test
# suite, so make sure you know what you're doing
#MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
#    ('mint.django_rest.middleware.LocalSetMintAdminMiddleware',)

installedAppsList = list(INSTALLED_APPS)
# Commented out misa 2011-08-02 - this breaks the testsuite under hudson
# installedAppsList.append('mint.django_rest.sdk_builder')
INSTALLED_APPS = tuple(installedAppsList)

TEST_RUNNER = "mint.django_rest.test_utils.TestRunner"
