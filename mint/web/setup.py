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
from mint.web.webhandler import WebHandler, normPath, HttpNotFound, HttpForbidden

from conary.web.fields import strFields, intFields, listFields, boolFields

configGroups = {
    'Server Setup':
        ('hostName', 'siteDomainName'),
    'Branding':
        ('companyName', 'corpSite'),
    'Repository Setup':
        ('defaultBranch',),
}


class SetupHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        # only admins are allowed here
        if not self.auth.admin and self.cfg.configured:
            raise HttpForbidden

        # first-time setup; check for <sid>.txt
        if not self.cfg.configured:
            if not self.session:
                self._session_start()

            self.session.save()

        if not cmd:
            return self.setup
        try:
            return self.__getattribute__(cmd)
        except AttributeError:
            raise HttpNotFound

    def setup(self, auth):
        if '.' not in self.req.hostname:
            return self._write("error", error = "You must access the rBuilder server as a fully-qualified domain name:"
                                                " eg., <strong>http://rbuilder.example.com/</strong>, not just <strong>http://rbuilder/</strong>")

        self.cfg.hostName = self.req.hostname.split(".")[0]
        self.cfg.siteDomainName = ".".join(self.req.hostname.split(".")[1:])

        return self._write("setup/setup", configGroups = configGroups,
            newCfg = self.cfg, errors = [])

    def processSetup(self, auth, **kwargs):
        mintClient = shimclient.ShimMintClient(self.cfg, [self.cfg.authUser, self.cfg.authPass])

        errors = []

        if '.' in kwargs['hostName']:
            errors.append("""The hostname of the rBuilder server must not contain periods. The
                hostname is only the first part of the fully-qualified domain name.""")
        if 'new_username' not in kwargs:
            errors.append("You must enter a username to be created")
        if 'new_email' not in kwargs:
            errors.append("You must enter a username to be created")
        if 'new_password' not in kwargs or 'new_password2' not in kwargs:
            errors.append("You must enter initial passwords")
        elif kwargs['new_password'] != kwargs['new_password2']:
            errors.append("Passwords must match")

        # rewrite configuration file
        keys = self.fields.keys()
        newCfg = deepcopy(self.cfg)

        for key in keys:
            if key in newCfg:
                newCfg[key] = self.fields[key]

        if errors:
            return self._write("setup/setup", configGroups = configGroups, newCfg = newCfg,
                errors = errors)

        # hack until we support SSL-rbuilder appliance
        newCfg.postCfg()
        newCfg.secureHost = newCfg.siteHost
        newCfg.projectDomainName = newCfg.externalDomainName = newCfg.siteDomainName
        newCfg.bugsEmail = newCfg.adminMail = kwargs['new_email']

        # create new user
        userId = mintClient.registerNewUser(
            str(kwargs['new_username']),
            str(kwargs['new_password']),
            "Administrator",
            str(kwargs['new_email']),
            "", "", active = True)
        self.req.log_error("created initial user account %s (id %d)" % (str(kwargs['new_username']), userId))
        mintClient.promoteUserToAdmin(userId)
        self.req.log_error("promoted %d to admin" % userId)

        # save entitlements
        if 'entitlement' in kwargs:
            for ent in ["conary.rpath.com", "products.rpath.com"]:
                f = open("/etc/conary/entitlements/%s" % ent, "w")
                f.write(kwargs['entitlement'])
                f.close()
                self.req.log_error("wrote entitlement to /etc/conary/entitlements/%s" % ent)

        cfg = file('/srv/mint/mint.conf', 'w')
        newCfg.display(out = cfg)
        self.req.log_error("writing new configuration to /srv/mint/mint.conf")
        self.req.log_error("+ sudo killall -USR1 httpd")
        os.system("sudo killall -USR1 httpd")
        return self._write("setup/saved")

    def config(self, auth):
        self.req.content_type = 'text/plain'

        buf = StringIO()
        self.cfg.display(out = buf)
        return buf.getvalue()

    def restart(self, auth):
        self.cfg.configured = True

        cfg = file('/srv/mint/mint.conf', 'w')
        self.cfg.display(out = cfg)
        self.req.log_error("writing new configuration to /srv/mint/mint.conf")
        self.req.log_error("+ sudo killall -USR1 httpd")
        self.req.log_error("+ sudo /sbin/service rbuilder-isogen restart")

        os.system("sudo killall -USR1 httpd")
        os.system("sudo /sbin/service rbuilder-isogen restart")
        time.sleep(5)
        self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))

    def _write(self, template, templatePath = None, **values):
        if not templatePath:
            templatePath = self.cfg.templatePath

        path = os.path.join(templatePath, template + ".kid")
        template = kid.load_template(path)

        t = template.Template(cfg = self.cfg, req = self.req, **values)
        return t.serialize(encoding = "utf-8", output = "xhtml")
