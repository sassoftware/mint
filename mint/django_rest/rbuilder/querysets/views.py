#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from django import http
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from mint.django_rest.deco import return_xml, requires, access, xObjRequires
from mint.django_rest.rbuilder import service
from mint.django_rest.rbuilder.querysets import models
from mint.django_rest.rbuilder.rbac.rbacauth import rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READSET, MODSETDEF

def rbac_can_read_queryset(view, request, query_set_id, *args, **kwargs):
    obj = view.mgr.getQuerySet(query_set_id)
    if obj.is_public:
        # existance of querysets like "All Systems", etc, are not stealthed.
        # but may vary in size depending on the user accessing them's permissions
        # (ReadMember) on their contents.
        return True
    user = view.mgr.getSessionInfo().user[0]
    ok = view.mgr.userHasRbacPermission(user, obj, READSET)
    return ok

def rbac_can_write_queryset(view, request, query_set_id, *args, **kwargs):
    obj = view.mgr.getQuerySet(query_set_id)
    user = view.mgr.getSessionInfo().user[0]
    return view.mgr.userHasRbacPermission(user, obj, MODSETDEF)

class BaseQuerySetService(service.BaseService):
    pass

class QuerySetService(BaseQuerySetService):

    # rbac is handled semimanually for this function -- show only 
    # querysets that we have permission to see
    # but don't use full rbac code, because that is implemented using querysets
    # and is too meta.

    @return_xml
    @access.authenticated
    def rest_GET(self, request, query_set_id=None):
        user = self.mgr.getSessionInfo().user[0]
        if query_set_id is None:
            querysets = self.mgr.getQuerySets() 
            return self.mgr.filterRbacQuerysets(user, querysets, request)
        else:
            queryset = self.mgr.getQuerySet(query_set_id)
            if not queryset.is_public and not self.mgr.userHasRbacPermission(
                user, queryset, READSET, request
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
        return self.mgr.addQuerySet(query_set, request._authUser)

    @access.admin
    @requires('query_set')
    @return_xml
    def rest_PUT(self, request, query_set_id, query_set):
        oldQuerySet = self.mgr.getQuerySet(query_set_id)
        if oldQuerySet.pk != query_set.pk:
            raise PermissionDenied()
        return self.mgr.updateQuerySet(query_set, request._authUser)

    @access.admin
    def rest_DELETE(self, request, query_set_id):
        querySet = self.mgr.getQuerySet(query_set_id)
        self.mgr.deleteQuerySet(querySet)
        response = http.HttpResponse(status=204)
        return response

class QuerySetAllResultService(BaseQuerySetService):
    
    @access.authenticated
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetAllResult(query_set_id, for_user=request._authUser)

class QuerySetUniverseResultService(BaseQuerySetService):
    '''the parent queryset of all objects of a given type'''

    @access.authenticated
    @return_xml
    def rest_GET(self, request, query_set_id):
        self.mgr.getQuerySetUniverseSet(query_set_id)
        url = reverse('QuerySetAllResult', args=[query_set_id])
        return HttpResponseRedirect(url)

class QuerySetChosenResultService(BaseQuerySetService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetChosenResult(query_set_id, for_user=request._authUser)

    @rbac(rbac_can_write_queryset)
    # TODO: source fromc onstant somewhere
    @requires(['systems', 'users', 'project_branch_stages', 'projects', 'grants', 'roles'])
    @return_xml
    def rest_PUT(self, request, query_set_id, *args, **kwargs):
        resources = kwargs.items()[0][1]
        return self.mgr.addQuerySetChosen(query_set_id, resources, request._authUser)

    @rbac(rbac_can_write_queryset)
    # TODO: source fromc onstant somewhere
    @requires(['system', 'user', 'project_branch_stage', 'project_branch', 'project', 'grant', 'role'])
    @return_xml
    def rest_POST(self, request, query_set_id, *args, **kwargs):
        resource = kwargs.items()[0][1]
        self.mgr.updateQuerySetChosen(query_set_id, resource, request._authUser)
        return resource

    @rbac(rbac_can_write_queryset)
    # TODO: source fromc onstant somewhere
    @requires(['system', 'user', 'project_branch_stage', 'project_branch', 'project', 'grant', 'role'])
    @return_xml
    def rest_DELETE(self, request, query_set_id, *args, **kwargs):
        resource = kwargs.items()[0][1]
        return self.mgr.deleteQuerySetChosen(query_set_id, resource, request._authUser)

class QuerySetFilteredResultService(BaseQuerySetService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, query_set_id):
        return self.mgr.getQuerySetFilteredResult(query_set_id, for_user=request._authUser)

class QuerySetChildResultService(BaseQuerySetService):

    @access.authenticated
    @return_xml
    def rest_GET(self, request, query_set_id):
        if rbac_can_read_queryset(self, request, query_set_id):
            return self.mgr.getQuerySetChildResult(query_set_id)
        else:
            return self.mgr.getQuerySetChildResult(query_set_id, for_user=request._authUser)

class QuerySetJobsService(BaseQuerySetService):

    # no way to list running jobs at the moment
    # since all jobs run immediately

    @rbac(rbac_can_read_queryset)
    @xObjRequires('job')
    def rest_POST(self, request, query_set_id, job):
        '''launch a job on this queryset'''
        queryset = self.mgr.getQuerySet(query_set_id)
        self.mgr.scheduleQuerySetJobAction(
            queryset, job
        )
        return http.HttpResponse(status=200)

class QuerySetFilterDescriptorService(BaseQuerySetService):

    # @access.authenticated
    @return_xml
    def rest_GET(self, request, query_set_id=None):
        return  self.mgr.getQuerySetFilterDescriptor(query_set_id)

