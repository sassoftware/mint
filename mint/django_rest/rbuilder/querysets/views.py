#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml, requires
from mint.django_rest.rbuilder import service

class BaseQuerySetService(service.BaseService):
    pass

class QuerySetService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, querySetId=None):
        return self.get(querySetId)

    def get(self, querySetId):
        if querySetId:
            return self.mgr.getQuerySet(querySetId)
        else:
            return self.mgr.getQuerySets()
        
    @requires('query_set')
    @return_xml
    def rest_POST(self, request, query_set):
        return self.mgr.addQuerySet(query_set)
