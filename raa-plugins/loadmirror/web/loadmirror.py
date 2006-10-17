# Copyright (c) 2006 rPath, Inc
# All rights reserved

import cherrypy
import turbogears

import os
import re

from mint import loadmirror

from raa.modules.raawebplugin import rAAWebPlugin
from raa.modules.raawebplugin import immedTask
from raa.localhostonly import localhostOnly
from raa.db.database import DatabaseTable, writeOp, readOp

class LoadMirrorTable(DatabaseTable):
    name = 'plugin_rpath_LoadMirrorTable'
    createSQL = """CREATE TABLE %s
                   (
                        schedId INT UNIQUE NOT NULL,
                        command VARCHAR(255)
                   )""" % (name)
    fields = ['schedId', 'command']
    tableVersion = 1

    @writeOp
    def setCommand(self, cu, schedId, command):
        self.db.transaction()
        cu.execute("DELETE FROM %s" % self.name)
        cu.execute("INSERT INTO %s (schedId, command) VALUES (?, ?)" % self.name, schedId, command)
        return True

    @readOp
    def getCommand(self, cu, schedId):
        cu.execute("""SELECT command FROM %s WHERE schedId=?""" % (self.name), schedId)
        command = cu.fetchone()
        if not command:
            return ''
        else:
            return command[0]


class LoadMirror(rAAWebPlugin):
    '''
    '''
    displayName = _("Pre-load Mirrored Repositories")

    sourceDir = '/mnt/mirror/'
    tableClass = LoadMirrorTable

    @turbogears.expose(html="rPath.loadmirror.index")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def index(self):
        if os.path.exists(os.path.join(self.sourceDir, 'lost+found')):
            mounted = True
            projects, errors = self._getProjects()
        else:
            mounted = False
            projects = []
            errors = {}


        return dict(projects = projects, errors = errors, mounted = mounted)

    @immedTask
    def _mountPreloadDisk(self):
        def callback(schedId):
            self.table.setCommand(schedId, "mount")

        return dict(callback = callback)

    @turbogears.expose(allow_json=True)
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def callGetPreloads(self):
        self._mountPreloadDisk()

        projects, errors = self._getProjects()
        return dict(projects = projects, preloadErrors = errors)

    def _getProjects(self):
        lm = loadmirror.LoadMirror(self.sourceDir, 'http://mintauth:mintpass@mint.rpath.local/xmlrpc-private/')
        projects = []
        errors = {}
        for serverName in os.listdir(self.sourceDir):
            print serverName
            if not os.path.exists(os.path.join(self.sourceDir, serverName, "MIRROR-INFO")):
                continue
            try:
                proj = lm.findTargetProject(serverName)
                projects.append((proj.name, proj.getFQDN()))
            except RuntimeError, e:
                projects.append(('', serverName))
                errors[serverName] = str(e)

        return projects, errors

    @cherrypy.expose()
    @localhostOnly()
    def getCommand(self, schedId):
        return self.table.getCommand(schedId)
