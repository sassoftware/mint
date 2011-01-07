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
    def rest_GET(self, request, query_set_id=None):
        return self.get(query_set_id)

    def get(self, query_set_id):
        if query_set_id:
            return self.mgr.getQuerySet(query_set_id)
        else:
            return self.mgr.getQuerySets()
        
    @requires('query_set')
    @return_xml
    def rest_POST(self, request, query_set):
        return self.mgr.addQuerySet(query_set)

    @requires('query_set')
    @return_xml
    def rest_PUT(self, request, query_set_id, systems):
        pass

class QuerySetAllResultService(BaseQuerySetService):
    
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetAllResult(query_set_id)


class QuerySetChosenResultService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetChosenResult(query_set_id)

    # Requires is a list to allow for different types of collections to be
    # PUT'd here.
    @requires(['systems']) 
    @return_xml
    def rest_PUT(self, request, query_set_id, systems=None):
        pass

class QuerySetFilteredResultService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetFilteredResult(query_set_id)

class QuerySetFilterDescriptorService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetFilterDescriptor(query_set_id)
