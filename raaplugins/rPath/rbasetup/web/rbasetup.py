#
# Copyright (c) 2006-2009 rPath, Inc
# All rights reserved
#
import time
import os
import md5
import re
import socket
import urllib

from gettext import gettext as _
import raa
import raa.web
import logging
log = logging.getLogger('raa.web')

from raa import rpath_error
from raa import constants
from raa.db.data import RDT_BOOL, RDT_INT, RDT_JSON, RDT_STRING
from raa.db import schedule
from raa.db import wizardrun
from raa.modules import raawebplugin
from raa.modules.raawebplugin import rAAWebPlugin
from raa.lib import validate

from mint import config
from mint import helperfuncs

from rPath.rbasetup import lib

ipAddrMatch = re.compile('^[0-9.]+$')
userNameMatch = re.compile('^[A-Za-z0-9._-]+$')
namespaceMatch = re.compile('^[A-Za-z0-9-]+$')

def validateNamespace(n):
    if not namespaceMatch.match(n):
        return "The namespace may only contain alphanumeric characters and hyphens."
    return ""

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
            return dict(schedId=-1, errors=['No setup task is running.'])
        status = raa.web.getWebRoot().callGetStatus(schedId)
        ret = dict(schedId=status['schedId'],
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
            # validate the hostname
            if 'hostName' not in options:
                errorList.append("You must specify a fully-qualified hostname")
            elif ipAddrMatch.match(options['hostName']):
                errorList.append("The hostname appears to be an IP address.")
            elif not validate.validateFqdn(options['hostName']):
                errorList.append("The hostname is invalid.")

            # validate the site domain name
            if 'projectDomainName' not in options:
                errorList.append("You must specify a domain name for this installation.")
            elif ipAddrMatch.match(options['projectDomainName']):
                errorList.append("The domain name appears to be an IP address.")
            elif not validate.validateFqdn(options['projectDomainName']):
                errorList.append("The domain name is invalid.")

            # validate the username
            if 'new_username' not in options:
                errorList.append("You must enter a username to be created")
            elif not userNameMatch.match(options['new_username']):
                errorList.append("Your username must contain only alphnumeric characters, periods, hyphens, and underscores")

            # validate the email address
            if 'new_email' not in options:
                errorList.append("You must enter an administrator email address")

            # validate password
            if  ('new_password' not in options or 'new_password2' not in options):
                errorList.append("You must enter initial passwords")
            elif options['new_password'] != options['new_password2']:
                errorList.append("Passwords must match")
            elif options['new_password'].find('#') != -1:
                errorList.append("Passwords must not contain a #")
                
            # entitlement key required
            if 'entitlementKey' not in options:
                errorList.append("You must enter a valid entitlement")
                
            # validate the entitlement key
            res = self.validateNewEntitlement(options.get('entitlementKey'))
            if res.has_key('errors'):
                errorString = "Entitlement is invalid"
                if len(res['errors']) > 0:
                    errorString = res['errors'][0]
                errorList.append(errorString)

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
                errorString = validateNamespace(options['namespace'])
                if errorString:
                    errorList.append(errorString)

        return errorList

    @raa.web.expose(template="rPath.rbasetup.index")
    def index(self):
        # check to see if we're mid-setup

        status = self._getFirstTimeSetupStatus()
        if status['schedId'] != -1: 
            raa.web.raiseHttpRedirect('/rbasetup/rBASetup/firstTimeSetup')

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
        if not sanitizedConfigurableOptions['hostName'] or \
           ipAddrMatch.match(sanitizedConfigurableOptions['hostName']):
            fqdn = raa.web.getRequestHostname()
            ipAddr = None
            if ipAddrMatch.match(fqdn):
                # user is using IP address to access the rbuilder
                # suggest a hostname instead
                ipAddr = fqdn
                fqdn = os.uname()[1]
            if fqdn.find('.') == -1:
                # Maybe we're better off doing a reverse lookup
                try:
                    if not ipAddr:
                        ipAddr = socket.gethostbyname(fqdn)
                    fqdn = socket.gethostbyaddr(ipAddr)[0]
                except:
                    # nothing is fully-qualified.  :-(
                    pass
            bits = fqdn.split('.')
            sanitizedConfigurableOptions['hostName'] = '.'.join(bits)
            try:
                sanitizedConfigurableOptions['siteDomainName'] = '.'.join(bits[1:])
            except IndexError:
                sanitizedConfigurableOptions['siteDomainName'] = ''
            sanitizedConfigurableOptions['projectDomainName'] = sanitizedConfigurableOptions['siteDomainName']
            if not isConfigured and len(bits) > 1:
                sanitizedConfigurableOptions['namespace'] = bits[-2]

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
        isConfigured, cfg = lib.getRBAConfiguration()

        # Validate the setup form
        errorList = self._validateSetupForm(normalizedOptions)
        if errorList:
            return dict(errors=errorList)

        # split hostname & siteDomainName
        if normalizedOptions.has_key('hostName'):
            hostname = normalizedOptions['hostName'].split('.')
            normalizedOptions['hostName'] = hostname[0]
            normalizedOptions['siteDomainName'] = '.'.join(hostname[1:])
           
        # try to save entitlement if we have one
        if normalizedOptions.get('entitlementKey'):
            result = self.setNewEntitlement(normalizedOptions.get('entitlementKey'))
            if result['errors']:
                return dict(errors=result['errors'])

        # Call backend to save generated file
        try:
            result = self.callBackend('updateRBAConfig', normalizedOptions)
            if result.has_key('errors'):
                return dict(errors=result['errors'])
            else:
                ret = dict(message="rBuilder Configuration saved.")
        except Exception, e:
            return dict(errors=["Failed to save rBuilder Configuration: %s" % repr(e)])

        # If this is a first time setup, we must kick off a redirect to do
        # post setup processing.
        if not isConfigured:
            username = raa.identity.current.user_name
            user = raa.identity.current_provider.authenticated_identity(username)
            raa.identity.current_provider.set_password(user,
                    normalizedOptions['new_password'])
            try:
                # do a simple check to catch the case where the user
                # did not fully qualify their hostname
                currentHostname = os.uname()[1]
                if currentHostname != '.'.join(hostname) and currentHostname == hostname[0]:
                    netCfg = self.plugins['/configure/Network'].index()
                    gatewayDHCP = False
                    if netCfg['host_gateway'] == '':
                        gatewayDHCP = True
                    log.info('saving new hostname')
                    self.plugins['/configure/Network']._saveGeneral(
                         netCfg['host_usesdhcp'], 
                         '.'.join(hostname),
                         netCfg['dns_dnsDomain'], 
                         netCfg['dns_dnsServer'],
                         gatewayDHCP,
                         netCfg['host_gateway'],
                         netCfg['host_gatewaydev'],
                         netCfg['dns_dnsdhcp'],
                         )
                    log.info('new hostname saved')
            except Exception, e:
                log.error('Hostname reset failed.  Continuing anyway...')
            # Kick off the first time processing
            sched = schedule.ScheduleOnce(time.time() + 1)
            schedId = self.callBackendAsync(sched, 'firstTimeSetup', normalizedOptions)
            self.setPropertyValue('FTS_SCHEDID', schedId, RDT_INT)
            # store the rBA Admin username, for use in other functions
            self.setPropertyValue('RBA_ADMIN', normalizedOptions['new_username'], RDT_STRING)
            # raa.web.raiseHttpRedirect('/rbasetup/rBASetup/firstTimeSetup')
            return True
        else:
            return ret

        return dict(errors=['An unexpected condition occurred'])

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def callGetStatus(self, schedId):
        return raa.web.getWebRoot().callGetStatus(schedId)       

    @raa.web.expose(allow_json=True)
    def retryFirstTimeSetup(self):
        currentStatus = self._getFirstTimeSetupStatus()
        if currentStatus['status'] == constants.TASK_FATAL_ERROR or \
            (currentStatus['status'] == constants.TASK_SUCCESS and
             not self.getPropertyValue('FINALIZED', False)):
            sched = schedule.ScheduleOnce(time.time() + 1)
            schedId = self.callBackendAsync(sched, 'firstTimeSetup',
                        dict(retry=True, 
                             new_username=self.getPropertyValue('RBA_ADMIN')))
            self.deletePropertyValue('FTS_SCHEDID')
            self.setPropertyValue('FTS_SCHEDID', schedId, RDT_INT)
            return self._getFirstTimeSetupStatus()
        else:
            log.error('not retrying FTS: status is %s' % currentStatus['status'] )   
        return  

    @raa.web.expose(allow_xmlrpc=True, allow_json=True, template="rPath.rbasetup.firstTimeSetup")
    def firstTimeSetup(self):
        status = self._getFirstTimeSetupStatus()
        if status['schedId'] == -1:
            raa.web.raiseHttpRedirect('/rbasetup/rBASetup/')
        return status

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def getFirstTimeSetupStatus(self):
        result = self._getFirstTimeSetupStatus()
        result.update(reload=False)
        if result['schedId'] == -1:
            return result

        # if the task is complete, get the return values
        if result['status'] == constants.TASK_SUCCESS:
            try:
                isException, ret = raa.web.getWebRoot().simpleTasks.getResult(result['schedId'])
                if isException:
                    try:
                        result['errors'] = " ".join( [ x.encode('utf-8') for x in ret ])
                    except:
                        result['errors'] = " ".join( [ x for x in ret ] )
                    result['status'] = constants.TASK_FATAL_ERROR
                    result['statusmsg'] = ''
                else:
                    result['statusmsg'] = ret.get('message', '')
                    result['errors'] = ret.get('errors', '')
                    if result['errors'] != '':
                        result['status'] = constants.TASK_FATAL_ERROR
            except Exception, e:
                # The task no longer exists
                finalized = self.getPropertyValue('FINALIZED', False)
                if not finalized:
                    # assume that it failed.  rerunning should not hurt.
                    result['status'] = constants.TASK_FATAL_ERROR
                result['statusmsg'] = ''
                result['errors'] = ''

            if isinstance(result['errors'], list):
                result['errors'] = "\n".join(result['errors'])
        elif result['status'] == constants.TASK_FATAL_ERROR:
            # NOTE: elif here is not the same as the following if
            result['errors'] = result['statusmsg']
            result['statusmsg'] = ''

        if result['status'] == constants.TASK_FATAL_ERROR:
            if raa.web.inWizardMode():
                self.wizardDone()
                result.update(reload=True)

        return result 

    @raa.web.expose(allow_xmlrpc=True)
    @raa.web.require(raa.authorization.LocalhostOnly())
    def setWizardDone(self):
        log.info('setting wizard done')
        try:
            self._wizardDone()
        except Exception, e:
            log.error('error setting wizard done')
        return dict(message='successfully set wizard done')

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def validateNewEntitlement(self, key):
        return self.plugins['/configure/Entitlements'].validateEntitlement(key)

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    @raa.web.require(raa.authorization.LocalhostOK())
    def setNewEntitlement(self, key):
        return self.plugins['/configure/Entitlements'].doSaveKey(key)

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def finalize(self):
        # mark finalized
        self.setPropertyValue('FINALIZED', True, RDT_BOOL)
        self.deletePropertyValue('FTS_SCHEDID')

        # mark done in the wizard
        self.wizardDone()
        
        # redirect to the rbuilder login screen
        fqdn = raa.web.getRequestHostname()
        query = { 'username': self.getPropertyValue('RBA_ADMIN', 'admin'),
                  'msg': urllib.quote("Please sign in below to enable platforms and complete the setup process.") }
        raa.web.raiseHttpRedirect("http://%s/ui/#/login?%s" % (fqdn, "&".join(["%s=%s" % (k, query[k]) for k in query.keys()])))
