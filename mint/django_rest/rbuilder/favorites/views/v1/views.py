#!/usr/bin/python
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
