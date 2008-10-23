#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

from copy import deepcopy
from mint import helperfuncs
import kid
import os
import os.path
import random
random = random.SystemRandom()
import time

from mint import helperfuncs
from mint import shimclient
from mint import config
from mint.config import RBUILDER_GENERATED_CONFIG, RBUILDER_RMAKE_CONFIG
from mint.config import keysForGeneratedConfig
from mint.web.webhandler import WebHandler, normPath, HttpNotFound, HttpForbidden
from mint.web.decorators import postOnly
from mint.web.fields import intFields

from conary.repository.netrepos import netauth
from conary.lib.util import mkdirChain

# be careful with 'Server Setup', code below and the associated kid template
# refer to this key directly. be sure to find all instances if you change it.
configGroups = {
    'Server Setup':
        ('hostName', 'siteDomainName'),
    'Branding':
        ('companyName', 'corpSite'),
    'Repository Setup':
        ('namespace',),
    '(Optional) External Passwords':
        ('externalPasswordURL', 'authCacheTimeout'),
    '(Optional) Miscellaneous':
        ('requireSigs',),
}


class SetupHandler(WebHandler):

    def _generateConfig(self, cfg):
        """ Write the generated configuration file using only the keys
            listed in keysForGeneratedConfig. """

        assert(self.req)
        genCfgPath = self.req.get_options().get('generatedConfigFile',
                RBUILDER_GENERATED_CONFIG)
        self.req.log_error("writing new configuration to %s" % genCfgPath)
        f = file(genCfgPath, 'w')
        for k in keysForGeneratedConfig:
            cfg.displayKey(k, out = f)
        f.close()

    def handle(self, context):
        self.__dict__.update(**context)

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        # enforce trailing / on /setup/
        if self.req.uri[-1].endswith('/setup'):
            self._redirect("http://%s/setup/" % self.req.hostname)

        # only admins are allowed here
        if not self.auth.admin and self.cfg.configured:
            raise HttpForbidden

        if self.client.getNewProjects(1, True) \
               and 'Server Setup' in configGroups:
            del configGroups['Server Setup']

        if not cmd:
            return self.setup
        try:
            ret = self.__getattribute__(cmd)
        except AttributeError:
            raise HttpNotFound

        if not callable(ret):
            raise HttpNotFound

        return ret

    def _copyCfg(self):
        newCfg = deepcopy(self.cfg)
        # deepcopy loses doc strings, which actually matters for this case.
        # of course some builtins (like int) can't have docstrings...
        for key, val in self.cfg._options.iteritems():
            try:
                newCfg._options[key].__doc__ = val.__doc__
            except:
                pass
        return newCfg
    
    def processTos(self, auth, **kwargs):        
        return self.setup(auth, (('acceptTos' in kwargs) and True or False))   

    def setup(self, auth, acceptedTos=False):
        if '.' not in self.req.hostname:
            return self._write("setup/error", error = "You must access the rBuilder server as a fully-qualified domain name:"
                                                " eg., <strong>http://rbuilder.example.com/</strong>, not just <strong>http://rbuilder/</strong>")
        
        newCfg = self._copyCfg()
        
        # enforce acceptance of terms of service
        if not acceptedTos:
            return self._write("setup/tos")

        # if the namespace has already been set, don't allow them to change it
        # FIXME this needs to be changed - implemented for RBL-2905.
        dflNamespace = config.MintConfig().namespace
        allowNamespaceChange = (newCfg.namespace == dflNamespace)

        if not self.cfg.configured:
            newCfg.hostName = self.req.hostname.split(".")[0]
            newCfg.siteDomainName =  ".".join(self.req.hostname.split(".")[1:])

        return self._write("setup/setup", configGroups = configGroups,
            newCfg = newCfg, errors = [], 
            allowNamespaceChange = allowNamespaceChange)

    @intFields(authCacheTimeout = 0)
    @postOnly
    def processSetup(self, auth, **kwargs):
        mintClient = shimclient.ShimMintClient(self.cfg, [self.cfg.authUser, self.cfg.authPass])

        errors = []

        if self.cfg.configured:
            if 'hostName' not in kwargs:
                kwargs['hostName'] = self.cfg.hostName
            if 'siteDomainName' not in kwargs:
                kwargs['siteDomainName'] = self.cfg.siteDomainName

        if '.' in kwargs['hostName']:
            errors.append("""The hostname of the rBuilder server must not contain periods. The
                hostname is only the first part of the fully-qualified domain name.""")
        if 'siteDomainName' not in kwargs or not kwargs['siteDomainName']:
            errors.append("""You must specify a domain name for this installation.""")
        if not self.cfg.configured and 'new_username' not in kwargs:
            errors.append("You must enter a username to be created")
        if not self.cfg.configured and 'new_email' not in kwargs:
            errors.append("You must enter an administrator email address")
        if not self.cfg.configured and \
               ('new_password' not in kwargs or 'new_password2' not in kwargs):
            errors.append("You must enter initial passwords")
        elif not self.cfg.configured and kwargs['new_password'] != \
                 kwargs['new_password2']:
            errors.append("Passwords must match")
        if kwargs.get('externalPasswordURL'):
            userAuth = netauth.UserAuthorization( \
                None, pwCheckUrl = kwargs['externalPasswordURL'],
                cacheTimeout = kwargs.get('authCacheTimeout'))
            if self.auth.admin and not userAuth._checkPassword( \
                self.auth.username, None, None, self.auth.token[1]):
                errors.append('Username: %s was not accepted by: %s' % \
                              (self.auth.username,
                               kwargs['externalPasswordURL']))
            if kwargs.get('new_username') and \
                   not userAuth._checkPassword(kwargs.get('new_username'),
                                               None, None,
                                               kwargs.get('new_password')):
                errors.append('Username: %s was not accepted by: %s' % \
                              (kwargs.get('new_username'),
                               kwargs.get('new_password')))
        
        # validate the namespace
        namespaceValid = False
        if 'namespace' not in kwargs or not kwargs['namespace']:
            errors.append("You must specify a namespace for this installation.")
        else:
            # returns text explanation if invalid
            valid = helperfuncs.validateNamespace(kwargs['namespace'])
            if valid != True:
                errors.append(valid)
            else:
                namespaceValid = True
       
        allowNamespaceChange = kwargs['allowNamespaceChange']
        if isinstance(allowNamespaceChange, str):
            # this comes back as a string from the web
            if allowNamespaceChange == 'True' or allowNamespaceChange == 'true':
                allowNamespaceChange = True
            else:
                allowNamespaceChange = False
        
        # always allow them to change invalid namespace.
        if not namespaceValid:
            allowNamespaceChange = True

        # rewrite configuration file
        keys = self.fields.keys()
        newCfg = self._copyCfg()

        for key in keys:
            if key in newCfg:
                newCfg[key] = self.fields[key]

        if errors:
            return self._write("setup/setup", configGroups = configGroups,
                               newCfg = newCfg, errors = errors,
                               allowNamespaceChange = allowNamespaceChange)

        newCfg.postCfg()
        newCfg.SSL = True
        newCfg.requireSigs = False
        newCfg.secureHost = newCfg.siteHost
        newCfg.projectDomainName = newCfg.externalDomainName = newCfg.siteDomainName
        if not self.cfg.configured:
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

        if kwargs.get('requireSigs'):
            newCfg.requireSigs = True

        if self.cfg.configured and self.cfg.authPass:
            newCfg.authPass = self.cfg.authPass
        else:
            newCfg.authPass = helperfuncs.genPassword(32)
        self._generateConfig(newCfg)
        if os.environ.get('RBUILDER_NOSUDO', False):
            sudo = ''
        else:
            sudo = 'sudo '
        os.system("%skillall -USR1 httpd" % sudo)

        if not self.cfg.configured:
            # Create a product (as the admin user) for use by the internal rmake.
            adminClient = shimclient.ShimMintClient(newCfg, 
                [kwargs['new_username'], kwargs['new_password']])

            shortName = 'rmake-repository'
            projectId = adminClient.newProject(name="rMake Repository",
                hostname=shortName,
                domainname=str(newCfg.projectDomainName),
                projecturl="",
                desc="This product's repository is used by the rMake server running on this rBuilder for building packages and groups with Package Creator and Appliance Creator.",
                appliance="no",
                shortname=shortName,
                namespace="rpath",
                prodtype="Component",
                version="1",
                commitEmail="",
                isPrivate=False,
                projectLabel="")

            rmakeUser = "%s-user" % shortName
            rmakePassword = helperfuncs.genPassword(32)
            adminClient.addProjectRepositoryUser(projectId, rmakeUser, 
                rmakePassword)
    
            self._writeRmakeConfig(rmakeUser, rmakePassword, 
                "https://%s" % newCfg.siteHost, 
                "%s.%s" % (shortName, newCfg.projectDomainName),
                "https://%s/repos/%s" % (newCfg.siteHost, shortName))

            if os.environ.get('RBUILDER_NOSUDO', False):
                sudo = ''
            else:
                sudo = 'sudo '

            os.system("%s/sbin/service rmake restart" % sudo)                
            os.system("%s/sbin/service rmake-node restart" % sudo)                

        return self._write("setup/saved")

    def _writeRmakeConfig(self, user, password, rBuilderUrl, reposName, reposUrl):
        path = self.req.get_options().get('rmakeConfigFilePath',
            RBUILDER_RMAKE_CONFIG)
        mkdirChain(os.path.dirname(path))
        f = file(path, 'w')
        f.write('%s %s %s %s\n' % ('reposUser', reposName, user, password))
        f.write('%s %s\n' % ('reposName', reposName))
        f.write('%s %s\n' % ('reposUrl', reposUrl))
        f.write('%s %s\n' % ('rBuilderUrl', rBuilderUrl))
        f.close()

    def restart(self, auth):

        newCfg = self._copyCfg()
        newCfg.configured = True
        self._generateConfig(newCfg)
        if os.environ.get('RBUILDER_NOSUDO', False):
            sudo = ''
        else:
            sudo = 'sudo '
        os.system("%skillall -USR1 httpd" % sudo)
        os.system("%s/sbin/service multi-jobserver restart" % sudo)
        time.sleep(5)
        self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))

    def _write(self, template, templatePath = None, **values):
        if not templatePath:
            templatePath = self.cfg.templatePath

        path = os.path.join(templatePath, template + ".kid")
        template = kid.load_template(path)

        t = template.Template(cfg = self.cfg, req = self.req, cacheFakeoutVersion = helperfuncs.getVersionForCacheFakeout(), **values)
        return t.serialize(encoding = "utf-8", output = "xhtml")

