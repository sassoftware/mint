#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# urls files for running the rbuilder django development app locally.

from urls import *  # pyflakes=ignore

from django.contrib import admin
admin.autodiscover()

newPatterns = patterns('',
        url(r'^admin/', include(admin.site.urls))
)

urlsList = list(urlpatterns)
for newPattern in newPatterns:
    urlsList.append(newPattern)
urlpatterns = tuple(urlsList)
