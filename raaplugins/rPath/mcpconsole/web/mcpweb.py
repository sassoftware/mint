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
        try:
            c = mcpclient.Client()
        except:
            log.exception("Could not connect to dispatcher:")
            c = None
        return c

    @raa.web.expose(template="rPath.mcpconsole.templates.jobs")
    @raa.web.require(raa.authorization.NotAnonymous())
    @marshallMessages
    def index(self):
        mcpClient = self.getMcpClient()
        if not mcpClient:
            return {'disabled' : True}

        return {
                'disabled': False,
                'queued': mcpClient.list_queued_jobs(),
                'nodes': mcpClient.list_nodes(),
                }

    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def killJob(self, jobId):
        mcpClient = self.getMcpClient()
        if mcpClient:
            try:
                mcpClient.stop_job(jobId)
            except Exception, e:
                self.errors.append(str(e))
            else:
                self.messages.append('Sent kill request for job: %s' % jobId)
        else:
            self.errors.append("Could not connect to MCP")
        raa.web.raiseHttpRedirect('index', 302)

    @raa.web.expose()
    @raa.web.require(raa.authorization.NotAnonymous())
    def setSlaveLimit(self, masterId, limit):
        if limit.isdigit():
            limit = max(0, int(limit))
            mcpClient = self.getMcpClient()
            if mcpClient:
                try:
                    mcpClient.set_node_slots(masterId, limit)
                except Exception, e:
                    self.errors.append(str(e))
                else:
                    self.messages.append('Set slot limit for %s to %d'
                            % (masterId, limit))
            else:
                self.errors.append("Could not connect to MCP")
        else:
            self.errors.append("Limit must be an integer")
        raa.web.raiseHttpRedirect('index', 302)

