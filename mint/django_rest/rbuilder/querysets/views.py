#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django import http

from mint.django_rest.deco import return_xml, requires, access, xObjRequires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.querysets import filterdescriptors
from mint.django_rest.rbuilder.querysets import models
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.errors import PermissionDenied


def rbac_can_read_queryset(view, request, query_set_id, *args, **kwargs):
    obj = view.mgr.getQuerySet(query_set_id)
    user = view.mgr.getSessionInfo().user[0]
    return view.mgr.userHasRbacPermission(user, obj, 'rqueryset')

def rbac_can_write_queryset(view, request, query_set_id, *args, **kwargs):
    obj = view.mgr.getQuerySet(query_set_id)
    user = view.mgr.getSessionInfo().user[0]
    return view.mgr.userHasRbacPermission(user, obj, 'wqueryset')

class BaseQuerySetService(service.BaseService):
    pass

class QuerySetService(BaseQuerySetService):

    # rbac is handled semimanually for this function, because it is the only
    # on that has result filtering
    @return_xml
    @access.authenticated
    def rest_GET(self, request, query_set_id=None):
        user = self.mgr.getSessionInfo().user[0]
        if query_set_id is None:
            querysets = self.mgr.getQuerySets() 
            return self.mgr.filterRbacQuerysets(user, querysets, request)
        else:
            queryset = self.mgr.getQuerySet(query_set_id)
            if not self.mgr.userHasRbacPermission(
                user, queryset, 'rqueryset', request
            ):
                raise PermissionDenied()
            return queryset

    # not used above, but still needed by load_from_href and other
    # functions
    def get(self, query_set_id=None):
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
        oldQuerySet = self.mgr.getQuerySet(query_set_id)
        if oldQuerySet.pk != query_set.pk:
            raise PermissionDenied()
        return self.mgr.updateQuerySet(query_set)

    @access.admin
    def rest_DELETE(self, request, query_set_id):
        querySet = self.mgr.getQuerySet(query_set_id)
        self.mgr.deleteQuerySet(querySet)
        response = http.HttpResponse(status=204)
        return response

class QuerySetAllResultService(BaseQuerySetService):
    
    @rbac(rbac_can_read_queryset)
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetAllResult(query_set_id)

class QuerySetChosenResultService(BaseQuerySetService):

    @rbac(rbac_can_read_queryset)
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetChosenResult(query_set_id)

    @rbac(rbac_can_write_queryset)
    @requires('systems') 
    @return_xml
    def rest_PUT(self, request, query_set_id, systems=None):
        return self.mgr.addQuerySetChosen(query_set_id, systems)

    @rbac(rbac_can_write_queryset)
    @requires('system')
    @return_xml
    def rest_POST(self, request, query_set_id, system):
        self.mgr.updateQuerySetChosen(query_set_id, system)
        return system

    @rbac(rbac_can_write_queryset)
    @requires('system')
    @return_xml
    def rest_DELETE(self, request, query_set_id, system):
        return self.mgr.deleteQuerySetChosen(query_set_id, system)

class QuerySetFilteredResultService(BaseQuerySetService):

    @rbac(rbac_can_read_queryset)
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetFilteredResult(query_set_id)

class QuerySetChildResultService(BaseQuerySetService):

    @rbac(rbac_can_read_queryset)
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetChildResult(query_set_id)

class QuerySetJobsService(BaseQuerySetService):

    # no way to list running jobs at the moment
    # since all jobs run immediately

    @rbac(rbac_can_read_queryset)
    @xObjRequires('job')
    @return_xml
    def rest_POST(self, request, query_set_id, job):
        '''launch a job on this queryset'''
        queryset = self.mgr.getQuerySet(query_set_id)
        return self.mgr.scheduleQuerySetJobAction(
            queryset, job
        )

class QuerySetFilterDescriptorService(BaseQuerySetService):

    @access.authenticated
    def rest_GET(self, request):
        filterDescriptor = models.FilterDescriptor()
        filterDescriptorId = filterDescriptor.get_absolute_url(request)
        code = 200
        response = http.HttpResponse(status=code, content_type='text/xml')
        response.content = \
            filterdescriptors.system_filter_descriptor.replace('@@ID@@', 
                filterDescriptorId)
        return response

