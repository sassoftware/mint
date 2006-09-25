#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#

from mint import config, client, database
from conary.lib import util
from conary.repository.netrepos import netserver
import os

class LoadMirror:
    client = None

    def __init__(self, sourceDir, serverUrl):
        self.sourceDir = sourceDir
        self.serverUrl = serverUrl

    def parseMirrorInfo(self, serverName):
        """Parse a mirror info file: <sourceDir>/<serverName>/MIRROR-INFO"""
        f = open(os.path.join(self.sourceDir, serverName, "MIRROR-INFO"))
        readServerName = f.readline().strip()
        _, _ = f.readline().strip().split("/") # don't need these
        numFiles = int(f.readline().strip())

        assert(serverName == readServerName)
        return numFiles

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

    def copyFiles(self, serverName, project):
        labelIdMap, _, _ = self.client.getLabelsForProject(project.id)
        label, labelId = labelIdMap.items()[0]

        cfg = config.MintConfig()
        cfg.read(config.RBUILDER_CONFIG)
        targetPath = os.path.join(cfg.dataPath, "repos") + os.path.sep
        util.mkdirChain(targetPath)

        sourcePath = os.path.join(self.sourceDir, serverName)

        util.copytree(sourcePath, targetPath)
        os.unlink(os.path.join(targetPath, serverName, "MIRROR-INFO"))
        os.system("chown -R apache.apache %s" % targetPath)

        self._addUsers(serverName, cfg)
        self.client.addInboundLabel(project.id, labelId, "http://%s/conary/" % serverName, "", "")
