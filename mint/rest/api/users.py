#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib import response
from mint.rest.api import base, notices

class UserNoticesAggregationController(notices.NoticesAggregationController):
    def index(self, req, username = None):
        if username != req.auth[0]:
            return response.Response(status = 403)
        title = "Notices for user %s" % username
        rss = notices.RssHelper(self.getStoragePath(), title = title,
            userId = username)
        return rss.serialize(rss.store.enumerateAllStore())

class UserNoticesContextController(notices.NoticesContextController):
    def get(self, req, username = None, context = None):
        if username != req.auth[0]:
            return response.Response(status = 403)
        return notices.NoticesContextController.get(self, req,
            context = context)

    def process(self, req, username = None, context = None):
        if username != req.auth[0]:
            return response.Response(status = 403)
        return notices.NoticesContextController.process(self, req,
            context = context)

    def destroy(self, req, username = None, context = None):
        if username != req.auth[0]:
            return response.Response(status = 403)
        return notices.NoticesContextController.destroy(self, req,
            context = context)

    def enumerateStoreContext(self, rss, context):
        return rss.store.enumerateStoreUser(context)

    def retrieveNotice(self, rss, notice, context = None):
        return rss.store.retrieveUser(notice, context = context)

    def storeNotice(self, rss, notice, context = None):
        return rss.store.storeUser(context, notice)

    def storeDismissal(self, rss, notice, context = None):
        return rss.store.storeUserDismissal(notice, context = context)

    def getNoticesUrl(self, req, noticeId):
        return "%s%s/%s" % (req.baseUrl,
            "users/%s/notices/contexts" % req.auth[0], noticeId)

    def getSourceUrl(self, req, context):
        return "%s%s/%s/%s/%s" % (req.baseUrl, "users", req.auth[0],
                                  "notices/contexts", context)

class UserNoticesController(base.BaseController):
    urls = dict(aggregation = UserNoticesAggregationController,
                contexts = UserNoticesContextController)

class UserController(base.BaseController):
    modelName = 'username'

    urls = {'products' : 'listProducts',
            'groups'   : 'listGroups',
            'notices'  : UserNoticesController}

    def index(self, request):
        return self.db.listUsers()

    def get(self, request, username):
        return self.db.getUser(username)
    
    def listProducts(self, request, username):
        return self.db.listMembershipsForUser(username)

    def listGroups(self, request, username):
        return self.db.listUserGroupsForUser(username)
