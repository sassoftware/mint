#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved
#
import logging
import os
import time

from raa import rpath_error
from raa.lib import command
from raa.modules import raasrvplugin
from raaplugins.services.srv import services

from rmake import plugins
from rmake.build import buildcfg
from rmake.cmdline import helper
from rmake.errors import OpenError
from rmake.node import nodecfg


from rPath import rmakemanagement

log = logging.getLogger('raa.server.rmakemanagement')

class BuildLog:

    log = ""

    def write(self, line):
        self.log += line

class DummyMain:
    # We need this class for loading the rMake plugins properly
    def _registerCommand(self, *args, **kwargs):
        pass

class rMakeManagement(services.Services):
    """
    Plugin for the backend work of the rMake management plugin.
    """

    def __init__(self, *args, **kwargs):
        raasrvplugin.rAASrvPlugin.__init__(self, *args, **kwargs)
        self.config = self.server.getConfigData()

    def _getrMakeHelper(self):
        self.config = self.server.getConfigData()

        certPath = self.config['rmake.client_certificate']
        if not os.path.exists(certPath):
            return None

        pluginManager = self._getPluginManager()
        buildConfig = buildcfg.BuildConfiguration(readConfigFiles=True)
        buildConfig['clientCert'] = certPath
        return helper.rMakeHelper(buildConfig=buildConfig, configureClient=True)

    def _getPluginManager(self):
        cfg = buildcfg.BuildConfiguration(True, ignoreErrors = True)
        if not cfg.usePlugins:
            return plugins.PluginManager([])
        pluginmgr = plugins.getPluginManager([], buildcfg.BuildConfiguration)
        pluginmgr.loadPlugins()
        pluginmgr.callClientHook('client_preInit', DummyMain(), [])
        return pluginmgr

    def getBuilds(self, schedId, execId, limit):
        """
        Return a list of builds, up to the configured limit.
        """
        self.rmakeHelper = self._getrMakeHelper()
        statusmsg = ''
        ret = []

        if not self.rmakeHelper:
            log.info('rMake client certificate not available')
            return 'rMake client certificiate not configured', []

        # Gracefully handle an rMake server communication error.
        try:
            builds = self.rmakeHelper.client.listJobs(jobLimit=limit)
        except OpenError, e:
            log.info('Error communicating to the rMake Server: %s' % str(e))
            return 'Could not contact rMake Server.', []

        for build in builds:
            statusmsg = 'Builds found'
            job = self.rmakeHelper.getJob(build)
            
            # The first trove in the build is the only one we will display.
            for trove in job.troves:
                ret.append((build, trove[0], job.getStateName(), job.isFinished(),
                            time.strftime("%m-%d-%Y %I:%M %p", 
                                          time.gmtime(job.finish))))
                break
        if not builds:
            statusmsg = 'No Builds found'

        return statusmsg, ret

    def getBuildLog(self, schedId, execId, buildId): 
        """
        Return the log for a given build.
        """
        self.rmakeHelper = self._getrMakeHelper()
        if self.rmakeHelper:
            build_log = BuildLog()
            self.rmakeHelper.displayJobInfo(jobId=buildId,
                                            proxy=self.rmakeHelper,
                                            out=build_log)

            return build_log.log
        else:
            return 'rMake client certificate not configured\n'


    def getServiceStatus(self, schedId, execId, serviceName):
        try:
            (stdout, stderr, retcode) = \
                command.executeCommand([rmakemanagement.COMMAND_SERVICE, 
                                        serviceName, "status"])

            if 'is running' in stdout.lower():
                stdout = rmakemanagement.status.RUNNING
            elif 'not running' in stdout.lower():
                stdout = rmakemanagement.status.STOPPED
            elif 'stopped' in stdout.lower():
                stdout = rmakemanagement.status.STOPPED
            elif 'locked' in stdout.lower():
                stdout = rmakemanagement.status.LOCKED
            else:
                stdout = rmakemanagement.status.UNKNOWN

        except rpath_error.UnknownException, e:
            stdout = rmakemanagement.status.UNKNOWN

        return stdout


    def getNodes(self, schedId, execId):
        # nodes = self.rmakedb.listNodes()
        node_list = []
        # for node in nodes:
        node_status = self.getServiceStatus(schedId, execId,
                             rmakemanagement.nodeServiceName)
        nc = nodecfg.NodeConfiguration()
        nc.readFiles()
        node_list.append((node_status, nc.slots, nc.chrootLimit))
        return node_list

    def editNode(self, schedId, execId, name, slots, chrootLimit):
        conf = dict(slots=slots, chrootLimit=chrootLimit)
        self._writeConfigToFile(self.config['rmake.node_config_file'],
                                conf, ' ')
        return True

    def resetServer(self, schedId, execId):
        """Reset the rMake server."""
        stdout, stderr, rv = command.executeCommand([
                rmakemanagement.COMMAND_RESET])
        if rv:
            return dict(errors=['Failed to reset rMake server:\n%s'
                % (stdout + stderr)])
        return dict(message='The rMake server has been reset')

    def _writeConfigToFile(self, filename, conf, delimiter):
        content = ""
        try:
            content = self._read(filename)
        except IOError, e:
            # Maybe the file doesn't exist, so ignore.
            pass

        content = "\n" + content.strip() + "\n"

        for (key, val) in conf.items():
            if val:
                val = "\n".join( [ "%s%s%s" % (key, delimiter, val)
                    for val in val.split(",") ] )

            start = 0
            indexKey = content.find("\n" + key, start)
            if -1 == indexKey and val:
                content += "%s\n" % (val)

            while -1 != indexKey:
                indexEnd = content.find("\n", indexKey+1)
                assert indexEnd > indexKey
                if not val or 0 != start:
                    content = "%s%s" % (content[:indexKey], content[indexEnd:])
                    start = indexKey
                else:
                    content = "%s\n%s%s" % (content[:indexKey], val,
                        content[indexEnd:])
                    start = indexKey + 1 + len(val)

                indexKey = content.find("\n" + key, start)

        self._write(filename, content.lstrip())


    def _read(self, filename):
        f = open(filename)
        content = f.read()
        f.close()
        return content

    def _write(self, filename, content):
        f = open(filename, "w")
        f.write(content)
        f.close()

