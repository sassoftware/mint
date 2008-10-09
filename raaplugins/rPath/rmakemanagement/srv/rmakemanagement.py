#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved
#

import time

from raa import rpath_error
from raa.lib import command
from raa.modules import raasrvplugin
from raaplugins.services.srv import services
from rmake.cmdline import helper
from rmake.db import database
from rmake_node import nodecfg
from rPath import rmakemanagement

class BuildLog:

    log = ""

    def write(self, line):
        self.log += line

class DatabaseProxy:
    def __init__(self, db):
        self.db = db

    def __getattr__(self, name):
        if name == 'client':
            return self
        else:
            return getattr(self.db, name)

class rMakeManagement(services.Services):
    """
    Plugin for the backend work of the rMake management plugin.
    """

    def __init__(self, *args, **kwargs):
        raasrvplugin.rAASrvPlugin.__init__(self, *args, **kwargs)
        self.config = self.server.getConfigData()
        db = database.Database(
                           path=self.config['rmake.db'],
                           contentsPath=self.config['rmake.contents'])
        self.rmakedb = DatabaseProxy(db)
        self.rmakehelper = helper.rMakeHelper(buildConfig=True, 
                                              configureClient=False)
        
    def getBuilds(self, schedId, execId, limit):
        """
        Return a list of builds, up to the configured limit.
        """
        ret = []
        builds = self.rmakedb.listJobs(jobLimit=limit)

        for build in builds:
            job = self.rmakedb.getJob(build)
            
            # The first trove in the build is the only one we will display.
            for trove in job.troves:
                ret.append((build, trove[0], 
                            time.strftime("%m-%d-%Y %I:%M %p", 
                                          time.gmtime(job.finish))))
                break
        return ret

    def getBuildLog(self, schedId, execId, buildId): 
        """
        Return the log for a given build.
        """
        build_log = BuildLog()
        self.rmakehelper.displayJobInfo(jobId=buildId,
                                        proxy=self.rmakedb,
                                        out=build_log)

        return build_log.log


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

