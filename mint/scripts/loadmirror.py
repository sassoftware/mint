#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#

from mint.db import database
from mint.rest.db import database as restDatabase
from mint import config, client
from mint.lib import scriptlibrary, copyutils
from mint.helperfuncs import getProjectText
from mint.mint_error import *
from conary.lib import util
from conary.repository.netrepos import netserver

import logging
from math import floor
import re
import os
import sys

# set up logging
cfg = config.MintConfig()
cfg.read(config.RBUILDER_CONFIG)
logFile = os.path.join(cfg.logPath, 'load-mirror.log')
try:
    scriptlibrary.setupScriptLogger(logfile = logFile,
        logfileLevel = logging.DEBUG)
except (OSError, IOError):
    pass
logger = scriptlibrary.getScriptLogger()

target = "/mnt/mirror/"


class Callback:
    def __init__(self, serverName, totalFiles, statusFile = None):
        self.serverName = serverName
        self.totalFiles = totalFiles
        self.filesCopied = 0
        self.lastCopied = 0

        if statusFile:
            self.f = open(statusFile, "w")
        else:
            self.f = sys.stdout

    def callback(self, files):
        self.filesCopied += files

        msg = "Copying files for %s: %2.0f%%" % \
            (self.serverName,
             floor(float(self.filesCopied)/float(self.totalFiles) * 100.0))

        if self.filesCopied > (self.lastCopied + 1000):
            self._write(msg)
            self.lastCopied = self.filesCopied

    def _write(self, msg):
        if self.f != sys.stdout:
            self.f.truncate()
        print >> self.f, msg


def call(cmd):
    logger.debug("+ %s" % cmd)
    return os.system(cmd)


def getFsLabel(dev):
    f = os.popen("/sbin/dumpe2fs -h %s 2> /dev/null" % dev, "r")
    label = None
    for x in f.readlines():
        if x.startswith("Filesystem volume name:"):
            label = x.split(":")[1].strip()

    f.close()
    return label

def getMountPoints(filter = "sd", source = "/proc/partitions"):
    f = open(source, "r")

    partitions = []
    partLine = re.compile(".*(%s\w+\d+)" % filter)

    for x in f.readlines():
        match = partLine.match(x.strip())
        if match:
            partitions.append(match.groups()[0])

    f.close()
    return ['/dev/' + x for x in partitions]

def mountMirrorLoadDrive(partitions = "/proc/partitions", mounts = "/proc/mounts"):
    dev = None
    for x in getMountPoints(source = partitions):
        logger.debug("checking %s for MIRRORLOAD partition label" % x)
        if getFsLabel(x) == "MIRRORLOAD":
            logger.debug("found matching partition label on %s" % x)
            dev = x
            break

    if dev:
        unmountIfMounted(dev, source = mounts)
        mountTarget(dev)
    else:
        raise NoMirrorLoadDiskFound
    logger.flush()

def mountTarget(dev):
    logger.debug("attempting to mount %s %s" % (dev, target))
    call("mount %s %s" % (dev, target))

def unmountIfMounted(dev, source = "/proc/mounts"):
    f = open(source, "r")

    for x in f.readlines():
        if x.startswith(dev):
            logger.debug("%s already mounted, attempting to unmount" % dev)
            rc = call("umount %s" % dev)
            if rc:
                raise UnmountFailed(dev)
            break


class LoadMirror:
    client = None

    def __init__(self, sourceDir, serverUrl, logger = None):
        self.sourceDir = sourceDir
        self.serverUrl = serverUrl
        if not logger:
            self.log = scriptlibrary.getScriptLogger()
        else:
            self.log = logger

        self.cfg = config.MintConfig()
        self.cfg.read(config.RBUILDER_CONFIG)

    def parseMirrorInfo(self, serverName):
        """Parse a mirror info file: <sourceDir>/<serverName>/MIRROR-INFO"""
        f = open(os.path.join(self.sourceDir, serverName, "MIRROR-INFO"))
        readServerName = f.readline().strip()
        _, _ = f.readline().strip().split("/") # don't need these
        numFiles = int(f.readline().strip())

        assert(serverName == readServerName)
        return numFiles + 1 # pad for containing dir

    def _openMintClient(self):
        self.client = client.MintClient(self.serverUrl)

    def findTargetProject(self, serverName):
        pText = getProjectText()
        if not self.client:
            self._openMintClient()

        found = None
        for projectId, _, _ in self.client.getProjectsList():
            project = self.client.getProject(projectId)
            label = project.getLabel()
            if label.startswith(serverName):
                found = project
                break

        if not found:
            raise RuntimeError, "Can't find external %s %s on rBuilder. " \
                "Please add the %s through the web interface first." % (pText.lower(), serverName, pText.lower())

        if not found.external:
            raise RuntimeError, "%s %s is not external: " \
                "can't load mirror" % (pText.title(), serverName)

        if self.client.isLocalMirror(found.id):
            raise RuntimeError, "%s %s is already mirrored" \
                % (pText.title(), serverName)

        return found

    def _addUsers(self, serverName, mintCfg):
        mintDb = database.Database(mintCfg)
        restDb = restDatabase.Database(mintDb)
        restDb.productMgr.reposMgr.addUser(serverName, 'anonymous',
                                          'anonymous', userlevel.USER)
        restDb.productMgr.reposMgr.addUser(serverName, mintCfg.authUser,
                                           mintCfg.authPass, userlevel.ADMIN)

    def copyFiles(self, serverName, project, targetOwner = None, callback = None):
        labelIdMap, _, _, _ = self.client.getLabelsForProject(project.id)
        label, labelId = labelIdMap.items()[0]

        # Delete any existing repository before copying the new data
        targetBase = os.path.join(self.cfg.dataPath, "repos")
        targetPath = os.path.join(targetBase, serverName)
        util.mkdirChain(targetBase)
        if os.path.exists(targetPath):
            util.rmtree(targetPath)

        sourcePath = os.path.join(self.sourceDir, serverName)

        copyutils.copytree(sourcePath, targetBase, fileowner = targetOwner,
            dirowner = targetOwner, callback = callback)
        os.unlink(os.path.join(targetPath, "MIRROR-INFO"))
        call("chown -R apache.apache %s" % targetPath)

        self._addUsers(serverName, self.cfg)
        localUrl = "http%s://%s%srepos/%s/" % (self.cfg.SSL and 's' or \
                   '', self.cfg.siteHost, self.cfg.basePath, project.hostname)

        # set the internal label to our authUser and authPass
        project.editLabel(labelId, label, localUrl, "userpass", self.cfg.authUser, self.cfg.authPass, "")
        self.client.addInboundMirror(project.id, [label], "http://%s/conary/" % serverName, "none", "", "")
