#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from lxml.builder import E
from lxml import etree as ET
import os

from restlib.response import Response

from mint import notices_store
from mint.rest.api import base
from mint.rest.middleware import auth, response

class BaseController(base.BaseController):
    def getStoragePath(self):
        return self.cfg.dataPath

class NoticesContextController(BaseController):
    modelName = "context"
    processSuburls = True

    @auth.public
    def get(self, req, context = None):
        if context != "default" and req.mintAuth is None:
            # We only allow unauthenticated users to fetch the default context
            return Response(status = 403)
        title = "Global notices for context %s" % context
        if req.auth:
            userId = req.auth[0]
        else:
            userId = None
        rss = RssHelper(self.getStoragePath(), title = title, userId = userId)
        if req.unparsedPath:
            return self.getNotice(req, context, rss)
        return rss.serialize(self.enumerateStoreContext(rss, context))

    def getNotice(self, req, context, rss):
        notice = self.retrieveNotice(rss, req.unparsedPath, context = context)
        if notice is None:
            return Response(status = 404)
        return response.XmlStringResponse(notice.content)

    def process(self, req, context = None):
        # Only admins are allowed to push notices
        if not (req.mintAuth and req.mintAuth.admin):
            return Response(status = 403)
        data = req.read()
        # Parse the data that was sent our way
        try:
            elem = ET.fromstring(data)
        except ET.XMLSyntaxError:
            return Response(status = 400)
        # Rename any existing guid
        guids = elem.findall('guid')
        for guid in guids:
            guid.tag = "guid-upstream"
        rss = RssHelper(self.getStoragePath(), userId = req.auth[0])
        notice = self.storeNotice(rss, "", context)

        guid = self.getNoticesUrl(req, notice.id)
        elem.append(E.guid(guid))
        elem.append(E.source(url = self.getSourceUrl(req, context)))
        notice.content = ET.tostring(elem, xml_declaration = False, encoding = 'UTF-8')
        self.storeNotice(rss, notice, None)
        return response.XmlStringResponse(notice.content)

    def destroy(self, req, context = None):
        # One cannot delete the context
        if not req.unparsedPath:
            # Maybe a better error than Forbidden?
            return Response(status = 403)
        rss = RssHelper(self.getStoragePath(), userId = req.auth[0])
        notice = self.storeDismissal(rss, req.unparsedPath, context = context)
        if notice is None:
            return Response(status = 404)
        return response.XmlStringResponse(notice.content)

    def enumerateStoreContext(self, rss, context):
        return rss.store.enumerateStoreGlobal(context)

    def retrieveNotice(self, rss, notice, context = None):
        return rss.store.retrieveGlobal(notice, context = context)

    def storeNotice(self, rss, notice, context = None):
        return rss.store.storeGlobal(context, notice)

    def storeDismissal(self, rss, notice, context = None):
        return rss.store.storeGlobalDismissal(notice, context = context)

    def getNoticesUrl(self, req, noticeId):
        return req.url('notices.contexts', noticeId)

    def getSourceUrl(self, req, context):
        return req.url('notices.contexts', context)


class NoticesAggregationController(BaseController):
    modelName = None

    placeholder = "@PLACEHOLDER@"

    @auth.public
    def index(self, req):
        rss = RssHelper(self.getStoragePath(), title = "Global Notices")
        return rss.serialize(rss.store.enumerateStoreGlobal("default"))

class NoticesController(BaseController):
    urls = dict(aggregation = NoticesAggregationController,
                contexts = NoticesContextController)

class RssHelper(object):
    placeholder = "@PLACEHOLDER@"

    def __init__(self, storagePath, **kwargs):
        userId = kwargs.pop("userId", "None")
        self.store = self.createStore(storagePath, userId)
        self.root, self.channel = self.makeXmlTree(**kwargs)

    def serialize(self, notices):
        ret = ET.tostring(self.root, xml_declaration = True, encoding = 'UTF-8')
        ret = ret.replace(self.placeholder, ''.join(x.content for x in notices))
        return response.XmlStringResponse(ret)

    @classmethod
    def createStore(cls, storagePath, userId):
        return notices_store.createStore(os.path.join(storagePath, "notices"),
            userId)

    @classmethod
    def makeXmlTree(cls, **kwargs):
        root = E.rss(version = "2.0")
        channel = E.channel(**kwargs)
        channel.text = cls.placeholder
        root.append(channel)
        return root, channel

