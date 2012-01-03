from mint.django_rest.rbuilder import metrics

# Django settings for rbuilder project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = dict(default=dict(
    ENGINE = 'django.db.backends.postgresql_psycopg2',
    NAME = 'mint',                  # Or path to database file if using sqlite3.
    USER = 'postgres',              # Not used with sqlite3.
    PASSWORD = '',                  # Not used with sqlite3.
    HOST = 'localhost',             # Set to empty string for localhost. Not used with sqlite3.
    PORT = '6432',                  # Set to empty string for default. Not used with sqlite3.
))

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'o5pks8b=o8zmpr%nu=4$##n*o_6s(t%r%i%h)*(9w)#yg=9*4u'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mint.django_rest.middleware.RequestSanitizationMiddleware',
    'mint.django_rest.middleware.CachingMiddleware',
    'mint.django_rest.middleware.SetMintConfigMiddleware',
    'mint.django_rest.middleware.SetMintAuthMiddleware',
    'mint.django_rest.middleware.SetMethodRequestMiddleware',
    'mint.django_rest.middleware.SetMintAuthenticatedMiddleware',
    'mint.django_rest.middleware.SetMintAdminMiddleware',
    'mint.django_rest.middleware.ExceptionLoggerMiddleware',
    'mint.django_rest.middleware.AddCommentsMiddleware',
    'mint.django_rest.middleware.FlashErrorCodeMiddleware',
    'mint.django_rest.middleware.RedirectMiddleware',
    'mint.django_rest.middleware.PerformanceMiddleware',
    'mint.django_rest.middleware.SerializeXmlMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

USE_ETAGS=True

ROOT_URLCONF = 'mint.django_rest.urls'

TEMPLATE_DIRS = (
    '/usr/lib64/python2.6/site-packages/mint/django_rest/templates/',
    'templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.redirects',
    'django.contrib.sessions',
    'django.contrib.sites',
    'mint.django_rest.rbuilder',
    'mint.django_rest.rbuilder.discovery',
    'mint.django_rest.rbuilder.reporting',
    'mint.django_rest.rbuilder.inventory',
    'mint.django_rest.rbuilder.metrics',
    'mint.django_rest.rbuilder.querysets',
    'mint.django_rest.rbuilder.packageindex',
    'mint.django_rest.rbuilder.packages',
    'mint.django_rest.rbuilder.projects',
    'mint.django_rest.rbuilder.users',
    'mint.django_rest.rbuilder.notices',
    'mint.django_rest.rbuilder.jobs',
    'mint.django_rest.rbuilder.platforms',
    'mint.django_rest.rbuilder.repos',
    'mint.django_rest.rbuilder.rbac',
    'mint.django_rest.rbuilder.targets',
    'mint.django_rest.rbuilder.images',
)

AUTHENTICATION_BACKENDS = (
    'mint.django_rest.rbuilder.auth.rBuilderBackend',
)

# Custom settings for pagination
PER_PAGE = 50

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK' : metrics.show_toolbar,
}
