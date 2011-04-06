#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django import http

from mint.django_rest.deco import return_xml, requires, access
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.querysets import filterdescriptors
from mint.django_rest.rbuilder.querysets import models

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
        
    @access.admin
    @requires('query_set', load=False)
    @return_xml
    def rest_POST(self, request, query_set):
        return self.mgr.addQuerySet(query_set)

    @access.admin
    @requires('query_set')
    @return_xml
    def rest_PUT(self, request, query_set_id, query_set):
        return self.mgr.updateQuerySet(query_set)

    @access.admin
    def rest_DELETE(self, request, query_set_id):
        querySet = self.mgr.getQuerySet(query_set_id)
        self.mgr.deleteQuerySet(querySet)
        response = http.HttpResponse(status=204)
        return response

class QuerySetAllResultService(BaseQuerySetService):
    
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetAllResult(query_set_id)


class QuerySetChosenResultService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetChosenResult(query_set_id)

    @access.admin
    @requires('systems') 
    @return_xml
    def rest_PUT(self, request, query_set_id, systems=None):
        return self.mgr.addQuerySetChosen(query_set_id, systems)

    @access.admin
    @requires('system')
    @return_xml
    def rest_POST(self, request, query_set_id, system):
        return self.mgr.updateQuerySetChosen(query_set_id, system)

    @access.admin
    @requires('system')
    @return_xml
    def rest_DELETE(self, request, query_set_id, system):
        return self.mgr.deleteQuerySetChosen(query_set_id, system)

class QuerySetFilteredResultService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetFilteredResult(query_set_id)

class QuerySetChildResultService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetChildResult(query_set_id)


class QuerySetFilterDescriptorService(BaseQuerySetService):

    def rest_GET(self, request):
        filterDescriptor = models.FilterDescriptor()
        filterDescriptorId = filterDescriptor.get_absolute_url(request)
        code = 200
        response = http.HttpResponse(status=code, content_type='text/xml')
        response.content = \
            filterdescriptors.system_filter_descriptor.replace('@@ID@@', 
                filterDescriptorId)
        return response

class QueryTagService(BaseQuerySetService):

    @return_xml
    def rest_GET(self, request, query_set_id, query_tag_id=None):
        return self.get(query_set_id, query_tag_id)

    def get(self, query_set_id, query_tag_id):
        if query_tag_id:
            return self.mgr.getQueryTag(query_set_id, query_tag_id)
        else:
            return self.mgr.getQueryTags()
