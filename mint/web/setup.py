#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

from cStringIO import StringIO
from copy import deepcopy
import kid
import sys
import os
import time

from mod_python import apache

from mint import mint_error
from mint import shimclient
from mint.session import SqlSession
from webhandler import WebHandler, normPath, HttpNotFound, HttpForbidden
from conary.web.fields import strFields, intFields, listFields, boolFields

configGroups = {
    'Server Setup':
        ('siteDomainName', 'hostName', 'SSL'),
    'Branding':
        ('companyName', 'productName', 'corpSite'),
    'Repository Setup':
        ('defaultBranch',),
}


class SetupHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
   
        path = normPath(context['cmd'])
        cmd = path.split('/')[1]
        print >> sys.stderr, context['cmd'], self.req.uri

        # only admins are allowed here
        if not self.auth.admin and self.cfg.configured:
            raise HttpForbidden
        
        # first-time setup; check for <sid>.txt
        if not self.cfg.configured:
            if not self.session:    
                print >> sys.stderr, "calling _session_start"
                sys.stderr.flush()
                self._session_start()

            self.session.save()
            # FIXME: parameterize /srv/mint/
            if not os.path.exists(self.cfg.dataPath + "/%s.txt" % self.session.id()):
                return self.secure
                
        if not cmd:
            return self.setup
        try:
            return self.__getattribute__(cmd)
        except AttributeError:
            raise HttpNotFound
        
    def setup(self, auth):
        return self._write("setup/setup", configGroups = configGroups)

    def processSetup(self, auth, **kwargs):
        keys = self.fields.keys()
        newCfg = deepcopy(self.cfg)

        for key in keys:
            newCfg[key] = self.fields[key]

        newCfg.configured = True
        cfg = file('/srv/mint/mint.conf', 'w')
        newCfg.display(out = cfg)
        return self._write("setup/saved")

    def config(self, auth):
        self.req.content_type = 'text/plain'

        buf = StringIO()
        self.cfg.display(out = buf)
        return buf.getvalue()

    def restart(self, auth):
        os.system("killall -USR1 httpd")
        time.sleep(5)
        self._redirect(self.cfg.basePath)

    def secure(self, auth):
        return self._write("setup/secure", sid = self.session.id())

    def _write(self, template, templatePath = None, **values):
        if not templatePath:
            templatePath = self.cfg.templatePath

        path = os.path.join(templatePath, template + ".kid")
        template = kid.load_template(path)

        t = template.Template(cfg = self.cfg, **values)
        return t.serialize(encoding = "utf-8", output = "xhtml")
