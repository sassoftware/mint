#
# Copyright (c) 2006 rPath, Inc.
# All Rights Reserved
#

from mint import config, client, database
import os

class LoadMirror:
    client = None

    def __init__(self, sourceDir, serverUrl):
        self.sourceDir = sourceDir
        self.serverUrl = serverUrl

    def parseMirrorInfo(self):
        f = open(os.path.join(self.sourceDir, "MIRROR-INFO"))
        serverName = f.readline().strip()
        _, _ = f.readline().strip().split("/") # don't need these
        numFiles = int(f.readline().strip())

        return serverName, numFiles

    def _openMintClient(self):
        self.client = client.MintClient(self.serverUrl)

    def findTargetProject(self, serverName):
        if not self.client:
            self._openMintClient()

        try:
            proj = self.client.getProjectByFQDN(serverName)
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
