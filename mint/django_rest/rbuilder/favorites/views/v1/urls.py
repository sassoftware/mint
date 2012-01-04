#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
from mint.django_rest.rbuilder.favorites.views.v1 import views
from mint.django_rest import urls
URL = urls.URLRegistry.URL

urlpatterns = patterns('favorites.views.v1',

    # FIXME: this will require a seperate service
    URL(r'/query_sets/?$',
        views.FavoriteQuerySetService(),
        name='FavoriteQuerySets',
        model='querysets.QuerySets'),

)


