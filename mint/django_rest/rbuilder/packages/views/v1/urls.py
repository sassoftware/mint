#
# Copyright (c) 2012 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import patterns
# FIXME: still has legacy structure, needs cleanup
from mint.django_rest.rbuilder.packageindex import views as packageindexviews
from mint.django_rest import urls
URL = urls.URLRegistry.URL

urlpatterns = patterns('',

    # --incomplete -- 
    # note -- this is a case where the urls and views aren't in the same subdir again
    # a sign the namespace should really be packageindex not packages

    URL(r'^/?$',
        packageindexviews.PackagesService(),
        name='Packages'),
    URL(r'^/(?P<package_id>\d+)/?$',
        packageindexviews.PackageService(),
        name='Package'),

)

