#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django import http

from mint.django_rest.deco import return_xml, requires, access
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
        if query_set_id is None:
            return self.mgr.getQuerySets()
        else:
            return self.mgr.getQuerySet(query_set_id)
        
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

class QuerySetReTagService(BaseQuerySetService):
    '''
    Query sets are slow to refresh, but we need to do this periodically, or some
    systems (etc) will remain untagged.
    This surfaces the capability so we can put it on cron, etc
    FIXME -- REMOVE ONCE OBSOLETED (SOON)
    '''

    @access.admin
    @return_xml
    def rest_GET(self, request, query_set_id):
        '''Retag a query set and return the query set'''
        # NOTE: this currently only retags on the leaf node query sets
        # so we'll *PROBABLY* want to run this in a way that runs only
        # against those, and or runs against all of those.
        qs = self.mgr.getQuerySet(query_set_id)
        self.mgr.tagQuerySet(qs)
        return qs

class QuerySetWithTagsService(BaseQuerySetService):
    '''
    Attempt to use query set tags to do a more efficient QuerySet
    fetch.  This is a work in progress and is not production ready
    yet.
    '''
    @access.admin
    @return_xml
    def rest_GET(self, request, query_set_id):
        '''Return the query set using object tags to do the lookup'''
        # NOTE: this currently only retags on the leaf node query sets
        # so we'll *PROBABLY* want to run this in a way that runs only
        # against those, and or runs against all of those.
        # TODO: know when to reTag when results are stale, keep a last_ran_date
        # or equivalent
        return self.mgr.getQuerySetAllResult(query_set_id)

class QuerySetAllResultService(BaseQuerySetService):
    
    @access.anonymous
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
        self.mgr.updateQuerySetChosen(query_set_id, system)
        return system

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
