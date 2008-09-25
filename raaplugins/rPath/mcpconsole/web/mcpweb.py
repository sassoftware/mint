# Copyright (c) 2007 rPath, Inc
# All rights reserved

from gettext import gettext as _

import logging
import sys
import traceback

import raa
import raa.web
import raa.authorization

from conary.lib.cfgtypes import CfgEnvironmentError

from raa.modules.raawebplugin import rAAWebPlugin
from raa.db.database import writeOp, readOp

from mcp import client as mcpclient
import mint.jobstatus

log = logging.getLogger('raa.web')

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
        self.messages = []
        self.errors = []

    def getMcpClient(self):
        cfg = mcpclient.MCPClientConfig()
        try:
            cfg.read('/srv/rbuilder/mcp/client-config')
            c = mcpclient.MCPClient(cfg)
        except:
            exc_cl, exc, bt = sys.exc_info()
            log.error(''.join(traceback.format_tb(bt)))
            log.error(exc)
            c = None
        return c

    @raa.web.expose(template="rPath.mcpconsole.templates.jobs")
    @raa.web.require(raa.authorization.NotAnonymous())
    @marshallMessages
    def index(self):
        mcpClient = self.getMcpClient()
        if mcpClient:
            try:
                jobStatus = mcpClient.jobStatus()

                # sort helpers
                sortOrder = ['-', '1', '2', '0', '3', '4']
                cmpKey = lambda x: sortOrder.index(str(x[1]['status'][0])[0])

                # get all the jobs into a list and sort by status then name,
                # with the jobid descending
                jobs = [(k, jobStatus[k]) for k in jobStatus]
                jobs.sort(lambda a, b: cmp(cmpKey(a), cmpKey(b)) or cmp(b[0], a[0]))

                # truncate the list to 10 stopped jobs ( 5 cooks, 5 builds )
                running = [x for x in jobs if x[1]['status'][0] <  mint.jobstatus.FINISHED]
                stopped = [x for x in jobs if x[1]['status'][0] >= mint.jobstatus.FINISHED]

                # split the stopped jobs into 5 cooks and 5 image builds due
                # to lack of a decent sort key
                stopped_builds = [x for x in stopped if     'build' in x[0]][0:5]
                stopped_cooks  = [x for x in stopped if not 'build' in x[0]][0:5]

                jobs = running + stopped_builds + stopped_cooks

                return {'jobStatus' : jobs, 'disabled' : False}
            finally:
                mcpClient.disconnect()
        return {'disabled' : True}

    @raa.web.expose(template="rPath.mcpconsole.templates.nodes")
    @raa.web.require(raa.authorization.NotAnonymous())
    @marshallMessages
    def nodes(self):
        mcpClient = self.getMcpClient()
        if mcpClient:
            try:
                nodeStatus = mcpClient.nodeStatus()
                return {'nodeStatus' : nodeStatus, 'disabled' : False}
            finally:
                mcpClient.disconnect()
        return {'disabled' : True}

    # rpc interface for javascript
    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def getJobStatus(self):
        mcpClient = None
        while not mcpClient:
            mcpClient = self.getMcpClient()
            if not mcpClient:
                time.sleep(1)
            else:
                try:
                    return mcpClient.jobStatus()
                finally:
                    mcpClient.disconnect()

    # rpc interface for javascript
    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def getNodeStatus(self):
        while not mcpClient:
            mcpClient = self.getMcpClient()
            if not mcpClient:
                time.sleep(1)
            else:
                try:
                    return mcpClient.nodeStatus()
                finally:
                    mcpClient.disconnect()

    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def killJob(self, jobId):
        mcpClient = self.getMcpClient()
        if mcpClient:
            try:
                try:
                    mcpClient.stopJob(jobId)
                except Exception, e:
                    self.errors.append(str(e))
                else:
                    self.messages.append('Sent kill request for job: %s' % jobId)
            finally:
                mcpClient.disconnect()
        else:
            self.errors.append("Could not connect to MCP")
        raa.web.raiseHttpRedirect('index', 302)

    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def stopSlave(self, slaveId):
        mcpClient = self.getMcpClient()
        if mcpClient:
            try:
                try:
                    mcpClient.stopSlave(slaveId)
                except Exception, e:
                    self.errors.append(str(e))
                else:
                    self.messages.append('Sent kill request for %s' %  slaveId)
            finally:
                mcpClient.disconnect()
        else:
            self.errors.append("Could not connect to MCP")
        raa.web.raiseHttpRedirect('nodes', 302)

    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def setSlaveLimit(self, masterId, limit):
        if limit.isdigit():
            limit = max(0, int(limit))
            mcpClient = self.getMcpClient()
            if mcpClient:
                try:
                    try:
                        mcpClient.setSlaveLimit(masterId, limit)
                    except Exception, e:
                        self.errors.append(str(e))
                    else:
                        self.messages.append('Sent slave limit for %s to %d' % \
                                                 (masterId, limit))
                finally:
                    mcpClient.disconnect()
            else:
                self.errors.append("Could not connect to MCP")
        else:
            self.errors.append("Limit must be an integer")
        raa.web.raiseHttpRedirect('nodes', 302)

