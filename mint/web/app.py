#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import kid

from mod_python import apache

import conary
from conary.web import webhandler

class MintApp(webhandler.WebHandler):
    def _getHandler(self, cmd, auth):
        self.req.content_type = "application/xhtml+xml"
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            method = self.frontPage
        return method

    def frontPage(self, auth):
        self._write("frontPage")
        return apache.OK

    def register(self, auth):
        self._write("register")
        return apache.OK

    def _write(self, template, **values):
        path = os.path.join(self.cfg.templatePath, template + ".kid")
        t = kid.load_template(path)

        content = t.serialize(encoding="utf-8", cfg = self.cfg,
                                                isInternal = self.auth.isInternal,
                                                **values)
        self.req.write(content) 
