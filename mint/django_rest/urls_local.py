#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# urls files for running the rbuilder django development app locally.

from urls import *  # pyflakes=ignore

from mint.django_rest.rbuilder.inventory import views as inventoryviews

from django.contrib import admin
admin.autodiscover()

newPatterns = patterns('',
        url(r'^admin/', include(admin.site.urls)),
        
        # added so we can use curl locally to PUT
        url(r'^api/inventory/systems$', 
            inventoryviews.InventorySystemsService(), 
            name='Systems'),
)

urlsList = list(urlpatterns)
for newPattern in newPatterns:
    urlsList.append(newPattern)
urlpatterns = tuple(urlsList)
