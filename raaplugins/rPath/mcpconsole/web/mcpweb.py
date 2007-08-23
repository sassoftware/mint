# Copyright (c) 2007 rPath, Inc
# All rights reserved

import cherrypy
import logging
import sys
import turbogears
import traceback

import raa

from conary.lib.cfgtypes import CfgEnvironmentError

from raa.modules.raawebplugin import rAAWebPlugin
from raa.db.database import writeOp, readOp

from mcp import client as mcpclient
import mint.jobstatus

log = logging.getLogger('raa.web')

def print_error():
    exc_cl, exc, bt = sys.exc_info()
    log.error(''.join(traceback.format_tb(bt)))
    log.error(str(exc))

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
        self.c = None
        cherrypy.server.on_stop_thread_list.append(self.disconnect)

    def getMcpClient(self):
        cfg = mcpclient.MCPClientConfig()
        try:
            cfg.read('/srv/rbuilder/config/mcp-client.conf')
            c = mcpclient.MCPClient(cfg)
        except:
            exc_cl, exc, bt = sys.exc_info()
            log.error(''.join(traceback.format_tb(bt)))
            log.error(exc)
            c = None
        return c

    def disconnect(self):
        if self.c:
            try:
                self.c.disconnect()
            except:
                print_error()
        self.c = None

    #mcpConsoleLogPath = '/srv/rbuilder/logs/mcp-console.log'

    @raa.expose(html="rPath.mcpconsole.templates.jobs")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    @marshallMessages
    def index(self):
        if not self.c:
            self.c = self.getMcpClient()
        if True or self.c:
            try:
                jobStatus = self.c.jobStatus()

                # sort helpers
                sortOrder = ['-', '1', '2', '0', '3', '4']
                cmpKey = lambda x: sortOrder.index(str(x[1]['status'][0])[0])

                # get all the jobs into a list and sort by status then name,
                # with the jobid descending
                jobs = [(k, jobStatus[k]) for k in jobStatus]
                jobs.sort(lambda a, b: cmp(cmpKey(a), cmpKey(b)) or cmp(b[0], a[0]))

                # truncate the list to 10 stopped jobs
                running = [x for x in jobs if x[1]['status'][0] <  mint.jobstatus.FINISHED]
                stopped = [x for x in jobs if x[1]['status'][0] >= mint.jobstatus.FINISHED][0:10]
                jobs = running + stopped
                
                return {'jobStatus' : jobs, 'disabled' : False}
            except:
                print_error()
                self.disconnect()
        return {'disabled' : True}

    @raa.expose(html="rPath.mcpconsole.templates.nodes")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    @marshallMessages
    def nodes(self):
        if not self.c:
            self.c = self.getMcpClient()
        if self.c:
            try:
                nodeStatus = self.c.nodeStatus()
                return {'nodeStatus' : nodeStatus, 'disabled' : False}
            except:
                print_error()
                self.disconnect()
        return {'disabled' : True}

    # rpc interface for javascript
    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def getJobStatus(self):
        while not self.c:
            self.c = self.getMcpClient()
            if not self.c:
                time.sleep(1)
            else:
                try:
                    return self.c.jobStatus()
                except:
                    print_error()
                    self.disconnect()

    # rpc interface for javascript
    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def getNodeStatus(self):
        while not self.c:
            self.c = self.getMcpClient()
            if not self.c:
                time.sleep(1)
            else:
                try:
                    return self.c.nodeStatus()
                except:
                    print_error()
                    self.disconnect()

    @raa.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def killJob(self, jobId):
        try:
            self.c.stopJob(jobId)
        except Exception, e:
            self.errors.append(str(e))
            self.disconnect()
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
            self.disconnect()
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
            self.disconnect()
        else:
            self.messages.append('Sent slave limit for %s to %d' % \
                                     (masterId, limit))
        raise cherrypy.HTTPRedirect('nodes', 302)
