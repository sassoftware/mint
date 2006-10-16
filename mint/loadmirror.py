#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#

from mint import config, client, database
from mint import scriptlibrary, copyutils
from conary.lib import util
from conary.repository.netrepos import netserver

import re
import os

import logging
logger = scriptlibrary.getScriptLogger()
target = "/mnt/mirror/"

class NoMirrorLoadDiskFound(Exception):
    def __str__(self):
        return "No mirror-load disk was found attached to your appliance."

class UnmountFailed(Exception):
    def __init__(self, dev):
        self.dev = dev
    def __str__(self):
        return "Unable to automatically unmount %s; please manually unmount" % self.dev

def call(cmd):
    logger.info("+ %s" % cmd)
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
        logger.info("checking %s for MIRRORLOAD partition label" % x)
        if getFsLabel(x) == "MIRRORLOAD":
            logger.info("found matching partition label on %s" % x)
            dev = x
            break

    if dev:
        unmountIfMounted(dev, source = mounts)
        mountTarget(dev)
    else:
        raise NoMirrorLoadDiskFound

def mountTarget(dev):
    logger.info("attempting to mount %s %s" % (dev, target))
    call("mount %s %s" % (dev, target))

def unmountIfMounted(dev, source = "/proc/mounts"):
    f = open(source, "r")

    for x in f.readlines():
        if x.startswith(dev):
            logger.info("%s already mounted, attempting to unmount" % dev)
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
        if not self.client:
            self._openMintClient()

        try:
            proj = self.client.getProjectByHostname(serverName.split(".")[0])
        except database.ItemNotFound:
            raise RuntimeError, "Can't find external project %s on rBuilder: " \
                "please add the project through the web interface first." % serverName

        if not proj.external:
            raise RuntimeError, "Project %s is not external: " \
                "can't load mirror" % serverName

        if self.client.isLocalMirror(proj.id):
            raise RuntimeError, "Project %s is already mirrored" \
                % serverName

        return proj

    def _addUsers(self, serverName, mintCfg):
        cfg = netserver.ServerConfig()
        cfg.repositoryDB = ("sqlite", mintCfg.reposDBPath % serverName)
        cfg.serverName = serverName
        cfg.contentsDir = os.path.join(mintCfg.dataPath, "repos", serverName, "contents")
        repos = netserver.NetworkRepositoryServer(cfg, '')

        repos.auth.addUser("anonymous", "anonymous")
        repos.auth.addAcl("anonymous", None, None, False, False, False)

        # add the mint auth user so we can add additional permissions
        # to this repository
        repos.auth.addUser(mintCfg.authUser, mintCfg.authPass)
        repos.auth.addAcl(mintCfg.authUser, None, None, True, False, True)
        repos.auth.setMirror(mintCfg.authUser, True)

    def copyFiles(self, serverName, project, callback = None):
        labelIdMap, _, _ = self.client.getLabelsForProject(project.id)
        label, labelId = labelIdMap.items()[0]

        cfg = config.MintConfig()
        cfg.read(config.RBUILDER_CONFIG)
        targetPath = os.path.join(cfg.dataPath, "repos") + os.path.sep
        util.mkdirChain(targetPath)

        sourcePath = os.path.join(self.sourceDir, serverName)

        copyutils.copytree(sourcePath, targetPath, callback = callback)
        os.unlink(os.path.join(targetPath, serverName, "MIRROR-INFO"))
        call("chown -R apache.apache %s" % targetPath)

        self._addUsers(serverName, cfg)
        self.client.addInboundLabel(project.id, labelId, "http://%s/conary/" % serverName, "", "")
        self.client.addRemappedRepository(".".join((serverName.split(".")[0], cfg.projectDomainName)), serverName)
