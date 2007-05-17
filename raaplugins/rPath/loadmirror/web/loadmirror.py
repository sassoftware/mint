# Copyright (c) 2005-2007 rPath, Inc
# All rights reserved

import cherrypy
import turbogears

import os
import re
import time

from mint import loadmirror
from mint import config

from raa.db import schedule
from raa.modules.raawebplugin import rAAWebPlugin
from raa.modules.raawebplugin import immedTask
from raa.localhostonly import localhostOnly
from raa.db.database import DatabaseTable, writeOp, readOp

class LoadMirrorTable(DatabaseTable):
    name = 'plugin_rpath_LoadMirrorTable'
    createSQL = """CREATE TABLE %s
                   (
                        schedId INT UNIQUE NOT NULL,
                        command VARCHAR(255),
                        error VARCHAR(255),
                        done INT
                   )""" % (name)
    fields = ['schedId', 'command', 'error', 'done']
    tableVersion = 1

    @writeOp
    def setCommand(self, cu, schedId, command, done = False, error = ''):
        self.db.transaction()
        cu.execute("DELETE FROM %s" % self.name)
        cu.execute("INSERT INTO %s (schedId, command, error, done) VALUES (?, ?, ?, ?)" % \
            self.name, schedId, command, error, str(int(done)))
        return True

    @readOp
    def getCommand(self, cu, schedId):
        cu.execute("""SELECT command, done FROM %s WHERE schedId=?""" % (self.name), schedId)
        command = cu.fetchone()
        if not command:
            return '', False
        else:
            return command[0], command[1]

    @readOp
    def getError(self, cu, schedId):
        cu.execute("""SELECT error FROM %s WHERE schedId=?""" % (self.name), schedId)
        command = cu.fetchone()
        if not command:
            return ''
        else:
            return command[0]


class LoadMirror(rAAWebPlugin):
    displayName = _("Pre-load Mirrored Repositories")

    tableClass = LoadMirrorTable
    preloadLogPath = '/srv/rbuilder/logs/load-mirror.log'

    @turbogears.expose(html="rPath.loadmirror.index")
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def index(self):
        sids = cherrypy.root.execution.getUnfinishedSchedules(types=schedule.typesValid, taskId=self.taskId)
        if not sids:
            schedId = self._setCommand("mount")
            schedId = schedId['schedId']
            inProgress = False
        else:
            schedId = sids[0]
            inProgress = True
        return dict(schedId = schedId, inProgress=inProgress)


    @immedTask
    def _setCommand(self, command, done = False, error = ''):
        def callback(schedId):
            self.table.setCommand(schedId, command, done, error)

        return dict(callback = callback)

    @turbogears.expose(allow_json=True)
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def callGetPreloads(self, schedId):
        _, done = self.table.getCommand(schedId)
        errors = self.table.getError(schedId)
        if done:
            projects, preloadErrors = self._getProjects()
        else:
            projects = []
            preloadErrors = {}
            done = False
        return dict(done = done, projects = projects, preloadErrors = preloadErrors, errors = errors)

    @turbogears.expose(allow_json=True)
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def callStartPreload(self):
        self._setCommand("preload")
        return dict()

    def _getLog(self):
        f = file(self.preloadLogPath)
        data = f.read()
        f.close()
        return data

    @turbogears.expose(allow_json=True)
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def callGetLog(self):
        return dict(log = self._getLog())

    @turbogears.expose()
    @turbogears.identity.require(turbogears.identity.not_anonymous())
    def downloadLog(self):
        cherrypy.response.headerMap['Content-Type'] = 'text/plain'
        return self._getLog()

    def _getProjects(self):
        cfg = config.MintConfig()
        cfg.read(config.RBUILDER_CONFIG)

        lm = loadmirror.LoadMirror(loadmirror.target,
            'http://%s:%s@localhost/xmlrpc-private/' % (cfg.authUser, cfg.authPass))

        projects = []
        errors = {}
        for serverName in os.listdir(loadmirror.target):
            if not os.path.exists(os.path.join(loadmirror.target, serverName, "MIRROR-INFO")):
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

    @cherrypy.expose()
    @localhostOnly()
    def setError(self, schedId, command, done = False, error = ''):
        return self.table.setCommand(schedId, command, done, error)
