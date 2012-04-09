#!/usr/bin/python
#
# Copyright (c) 2012 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml, access
from mint.django_rest.rbuilder.querysets.views.v1.views import BaseQuerySetService

class FavoriteQuerySetService(BaseQuerySetService):

    # return the list of querysets that I can see that I should also
    # show in the UI left nav.  Eventually this will support a bookmarks
    # feature, now it just applies some basic logic.    

    @access.authenticated
    @return_xml
    def rest_GET(self, request):
        user = request._authUser
        querysets = self.mgr.getQuerySets() 
        return self.mgr.favoriteRbacedQuerysets(user, querysets, request)

