#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import kid
import sys

from mod_python import apache
from conary.web import webhandler

from mint import shimclient
from mint import projects

class MintApp(webhandler.WebHandler):
    def _checkAuth(self, authToken):
        self.client = shimclient.ShimMintClient(self.cfg, authToken)
        return self.client.checkAuth()

    def _getHandler(self, cmd, auth):
        self.req.content_type = "application/xhtml+xml"

        fullHost = self.req.hostname
        hostname = fullHost.split('.')[0]
        try:
            if hostname == "www":
                self.project = None
            else:
                try:
                    self.project = self.client.getProjectByHostname(fullHost)
                except projects.ProjectNotFound:
                    return lambda auth: apache.HTTP_NOT_FOUND
                
            method = self.__getattribute__(cmd)
        except AttributeError:
            if hostname == "www":
                method = self.frontPage
            else:
                method = self.projectPage
        return method

    def frontPage(self, auth):
        self._write("frontPage")
        return apache.OK

    def register(self, auth):
        self._write("register")
        return apache.OK

    def projectPage(self, auth):    
        self._write("projectPage", project = self.project)
        return apache.OK

    def _write(self, template, **values):
        path = os.path.join(self.cfg.templatePath, template + ".kid")
        t = kid.load_template(path)

        content = t.serialize(encoding="utf-8", cfg = self.cfg,
                                                auth = self.auth,
                                                **values)
        self.req.write(content) 
