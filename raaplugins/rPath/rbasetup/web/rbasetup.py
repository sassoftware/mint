#
# Copyright (c) 2006-2009 rPath, Inc
# All rights reserved
#
import time
import os
import md5
import simplejson

from gettext import gettext as _
from time import time
import raa
import raa.web
import logging
log = logging.getLogger('raa.web')

from raa.web import makeUrl, getCurrentUser, getRequestHeaderValue
from raa import rpath_error
from raa import constants
from raa.db.data import RDT_BOOL, RDT_INT, RDT_JSON, RDT_STRING
from raa.db import schedule
from raa.db import wizardrun
from raa.modules import raawebplugin
from raa.modules.raawebplugin import rAAWebPlugin

from mint import config
from mint import helperfuncs

from rPath.rbasetup import lib

class rBASetup(rAAWebPlugin):
    """
    Represents the web side of the plugin.
    """
    # Name to be displayed in the side bar.
    displayName = _("rBuilder Setup")

    # Name to be displayed on mouse over in the side bar.
    tooltip = _("Plugin for setting up the rBuilder Appliance")
    
    wizardSerial = 1
    
    def initPlugin(self):
        self.checkSkipWizard()
        
    def checkSkipWizard(self):
        # If the system is already configured and this plug-in hasn't been run
        # in the wizard yet (i.e. migration) mark it as done.  We only want to
        # run in the wizard during install.
        isConfigured, cfg = lib.getRBAConfiguration()
        if isConfigured:
            # this initializes the pluginId dict which we need
            raa.modules.helper.getWebPluginIdDict()
            wizardRun = raa.web.getWebRoot().wizardRun
            
            # has wizard already run?
            if wizardRun.getLastRunTime(self.taskId, self.wizardSerial) is not None:
                return
            
            wizardRun.resetSession([(self.taskId, self.wizardSerial)])
            self._wizardDone()
            wizardRun.commit()

    def _getFirstTimeSetupStatus(self):
        # Get some status here
        schedId = self.getPropertyValue('FTS_SCHEDID', -1)
        if schedId == -1:
            # We got here without being scheduled; clear out and move back
            raa.web.raiseHttpRedirect(raa.web.makeUrl('/rbasetup/rBASetup/'))

        status = raa.web.getWebRoot().getStatus(schedId)
        ret = dict(currentStep=self.getPropertyValue('FTS_CURRENTSTEP', lib.FTS_STEP_INITIAL),
                   schedId=schedId,
                   status=status['status'],
                   statusmsg=status['statusmsg'])

        return ret

    def _normalizeFormKwargs(self, kwargsFromForm):
        """
        Takes a pile of kwargs from the form post and normalizes it,
        stripping leading and trailing whitespace and converting
        booleans into the Boolean type.
        """
        boolean_options = ('requireSigs', 'configured', 'allowNamespaceChange')
        normalizedOptions = dict()

        for k, v in kwargsFromForm.iteritems():
            newV = v.strip()
            if k in boolean_options:
                normalizedOptions[k] = bool(int(str(v)))
            else:
                if newV:
                    normalizedOptions[k] = newV

        return normalizedOptions

    def _validateSetupForm(self, options):
        """
        Takes a list of options and validates them.
        Returns a list of errors (empty list if OK).
        """
        errorList = list()

        if not options['configured']:
            if '.' in options['hostName']:
                errorList.append("The hostname of the rBuilder server must not contain periods. The hostname is only the first part of the fully-qualified domain name.")
            if 'siteDomainName' not in options:
                errorList.append("You must specify a domain name for this installation.")
            if 'new_username' not in options:
                errorList.append("You must enter a username to be created")
            if 'new_email' not in options:
                errorList.append("You must enter an administrator email address")
            if  ('new_password' not in options or 'new_password2' not in options):
                errorList.append("You must enter initial passwords")
            elif options['new_password'] != options['new_password2']:
                errorList.append("Passwords must match")

        if options.get('externalPasswordURL'):
            # XXX Removing the validation for this for now;
            #     it was more necessary when you could lock yourself
            #     out of rBuilder if you messed it up.
            #userAuth = netauth.UserAuthorization( \
            #    None, pwCheckUrl = options['externalPasswordURL'],
            #    cacheTimeout = int(options.get('authCacheTimeout')))
            #if self.auth.admin and not userAuth._checkPassword( \
            #    self.auth.username, None, None, self.auth.token[1]):
            #    errorList.append('Username: %s was not accepted by: %s' % \
            #                  (self.auth.username,
            #                   options['externalPasswordURL']))
            #if options.get('new_username') and \
            #       not userAuth._checkPassword(options.get('new_username'),
            #                                   None, None,
            #                                   options.get('new_password')):
            #    errorList.append('Username: %s was not accepted by: %s' % \
            #                  (options.get('new_username'),
            #                   options.get('new_password')))
            pass

        # validate the namespace
        if options.get('allowNamespaceChange'):
            namespaceValid = False
            if 'namespace' not in options:
                errorList.append("You must specify a namespace for this installation.")
            else:
                # returns text explanation if invalid
                valid = helperfuncs.validateNamespace(options['namespace'])
                if valid != True:
                    errorList.append(valid)

        return errorList

    @raa.web.expose(template="rPath.rbasetup.index")
    def index(self):
        # Get the configuration from the backend
        isConfigured, configurableOptions = lib.getRBAConfiguration()

        # if the namespace has already been set, don't allow them to change it
        # FIXME this needs to be changed - implemented for RBL-2905.
        dflNamespace = config.MintConfig().namespace
        allowNamespaceChange = not isConfigured or (configurableOptions['namespace'] == dflNamespace)

        # Backend returns Unicode for keys, which is suboptimal for Kid
        sanitizedConfigurableOptions = \
                dict([(str(k),v) for k, v in configurableOptions.iteritems()])

        # Return the hostname from the request if it's not set
        if not sanitizedConfigurableOptions['hostName']:
            import cherrypy
            fqdn = raa.lib.url.urlparse(cherrypy.request.base)[1].split(':')[0]
            bits = fqdn.split('.',1)
            sanitizedConfigurableOptions['hostName'] = bits[0]
            try:
                sanitizedConfigurableOptions['siteDomainName'] = bits[1]
            except IndexError:
                sanitizedConfigurableOptions['siteDomainName'] = ''

        return dict(isConfigured=isConfigured,
                allowNamespaceChange=allowNamespaceChange,
                **sanitizedConfigurableOptions)

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def saveConfig(self, *args, **kwargs):
        """
        Called upon posting the setup form.
        """
        # Normalize kwargs into a minimal set of options
        normalizedOptions = self._normalizeFormKwargs(kwargs)
        firstTimeSetup = not normalizedOptions.get('configured', False)

        # Validate the setup form
        errorList = self._validateSetupForm(normalizedOptions)
        if errorList:
            return dict(errors=errorList)

        # Call backend to save generated file
        saved = self.callBackend('updateRBAConfig', normalizedOptions)
        if not saved:
            return dict(errors=["Failed to save the rBuilder Configuration"])

        # If this is a first time setup, we must kick off a redirect to do
        # post setup processing.
        if firstTimeSetup:
            # Kick off the first time processing
            self.setPropertyValue('FINALIZED', False, RDT_BOOL)
            self.setPropertyValue('FTS_ADMINUSER',
                    normalizedOptions['new_username'], RDT_STRING)
            self.setPropertyValue('FTS_ADMINPASS',
                    normalizedOptions['new_password'], RDT_STRING)
            self.setPropertyValue('FTS_ADMINEMAIL',
                    normalizedOptions['new_email'], RDT_STRING)
            self.setPropertyValue('FTS_CURRENTSTEP', lib.FTS_STEP_INITIAL, RDT_INT)
            sched = schedule.ScheduleNow()
            self.setPropertyValue('FTS_SCHEDID', self.schedule(sched), RDT_INT)
            # N.B.: the javascript on the page will redirect the user to
            # the first time setup page on success; we don't have to do it here.

        return dict(message="Saved rBuilder configuration.")

    @raa.web.expose(allow_json=True)
    def retryFirstTimeSetup(self):
        currentStatus = self._getFirstTimeSetupStatus()
        if currentStatus['status'] == constants.TASK_FATAL_ERROR:
            sched = schedule.ScheduleNow()
            self.setPropertyValue('FTS_SCHEDID', self.schedule(sched), RDT_INT)
        return   

    @raa.web.expose(allow_xmlrpc=True, allow_json=True, template="rPath.rbasetup.firstTimeSetup")
    def firstTimeSetup(self):
        return self._getFirstTimeSetupStatus()

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def getFirstTimeSetupStatus(self):
        return self._getFirstTimeSetupStatus()

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    @raa.web.require(raa.authorization.LocalhostOnly())
    def setFirstTimeSetupState(self, newState):
        self.setPropertyValue('FTS_CURRENTSTEP', newState, RDT_INT)
        return dict()

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def getFirstTimeSetupStatus(self):
        return self._getFirstTimeSetupStatus()

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    @raa.web.require(raa.authorization.LocalhostOnly())
    def getFirstTimeSetupAdminInfo(self):
        return dict(new_username=self.getPropertyValue('FTS_ADMINUSER', ''),
                    new_password=self.getPropertyValue('FTS_ADMINPASS', ''),
                    new_email=self.getPropertyValue('FTS_ADMINEMAIL', ''))

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    @raa.web.require(raa.authorization.LocalhostOnly())
    def setNewEntitlement(self, key):
        self.plugins['/configure/Entitlements'].doSaveKey(key)
        return True

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def finalize(self):
        # remove gunk
        self.deletePropertyValue('FTS_ADMINUSER', commit=False)
        self.deletePropertyValue('FTS_ADMINPASS', commit=False)
        self.deletePropertyValue('FTS_ADMINEMAIL', commit=False)
        self.deletePropertyValue('FTS_CURRENTSTEP', commit=False)
        self.deletePropertyValue('FTS_SCHEDID', commit=False)

        # mark finalized
        self.setPropertyValue('FINALIZED', True, RDT_BOOL)

        # mark done in the wizard
        self.wizardDone()
        
        # redirect to the rbuilder itself
        raa.web.raiseHttpRedirect("http://" + raa.web.getRequestHostname() + "/")
