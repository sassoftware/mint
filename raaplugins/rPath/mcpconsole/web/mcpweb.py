# Copyright (c) 2007 rPath, Inc
# All rights reserved

import cherrypy
import turbogears

import raa

from conary.lib.cfgtypes import CfgEnvironmentError

from raa.modules.raawebplugin import rAAWebPlugin
from raa.db.database import writeOp, readOp

from mcp import client as mcpclient

def marshallMessages(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)

        # strip messages stored in the class and pass them.
        messages = res.get('messages', [])
        messages.extend(self.messages)
        res['messages'] = messages
        self.messages = []

        # strip errors stored in the class and pass them.
        errors = res.get('errors', [])
        errors.extend(self.errors)
        res['errors'] = errors
        self.errors = []

        return res

    # masquerade wrapper as the original function.
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    return wrapper

class MCPConsole(rAAWebPlugin):
    displayName = _("Job Control Console")

    def __init__(self, *args, **kwargs):
        rAAWebPlugin.__init__(self, *args, **kwargs)
        cfg = mcpclient.MCPClientConfig()
        try:
            cfg.read('/srv/rbuilder/config/mcp-client.conf')
        except CfgEnvironmentError:
            cfg.queueHost = 'localhost'
        try:
            self.c = mcpclient.MCPClient(cfg)
            cherrypy.server.on_stop_thread_list.append(self.disconnect)
        except:
            self.c = None
        self.messages = []
        self.errors = []

    def disconnect(self):
        self.c.disconnect()

    #mcpConsoleLogPath = '/srv/rbuilder/logs/mcp-console.log'

    @raa.expose(html="rPath.mcpconsole.templates.jobs")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    @marshallMessages
    def index(self):
        jobStatus = self.c.jobStatus()

        return {'jobStatus' : jobStatus}

    @raa.expose(html="rPath.mcpconsole.templates.nodes")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    @marshallMessages
    def nodes(self):
        nodeStatus = self.c.nodeStatus()

        return {'nodeStatus' : nodeStatus}

    # rpc interface for javascript
    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def getJobStatus(self):
        return self.c.jobStatus()

    # rpc interface for javascript
    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def getNodeStatus(self):
        return self.c.nodeStatus()


    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def killJob(self, jobId):
        try:
            self.c.stopJob(jobId)
        except Exception, e:
            self.errors.append(str(e))
        else:
            self.messages.append('Sent kill request for job: %s' % jobId)
        raise cherrypy.HTTPRedirect('index', 302)

    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def stopSlave(self, slaveId, delayed = '1'):
        delayed = bool(int(delayed))
        try:
            self.c.stopSlave(slaveId, delayed)
        except Exception, e:
            self.errors.append(str(e))
        else:
            self.messages.append('Sent %s kill request for %s' % \
                                     (delayed and 'deferred' or 'immediate',
                                      slaveId))
        raise cherrypy.HTTPRedirect('nodes', 302)

    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def setSlaveLimit(self, masterId, limit):
        limit = int(limit)
        try:
            self.c.setSlaveLimit(masterId, limit)
        except Exception, e:
            self.errors.append(str(e))
        else:
            self.messages.append('Sent slave limit for %s to %d' % \
                                     (masterId, limit))
        raise cherrypy.HTTPRedirect('nodes', 302)
