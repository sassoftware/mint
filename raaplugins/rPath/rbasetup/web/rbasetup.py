#
# Copyright (c) 2006-2008 rPath, Inc
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
from raa.db import wizardrun
from raa.modules.raawebplugin import rAAWebPlugin

from mint import config
from mint import helperfuncs

class rBASetup(rAAWebPlugin):
    """
    Represents the web side of the plugin.
    """
    # Name to be displayed in the side bar.
    displayName = _("rBuilder Setup")

    # Name to be displayed on mouse over in the side bar.
    tooltip = _("Plugin for setting up the rBuilder Appliance")

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

        if '.' in options['hostName']:
            errorList.append("""The hostname of the rBuilder server must not contain periods. The
                hostname is only the first part of the fully-qualified domain name.""")
        if 'siteDomainName' not in options:
            errorList.append("""You must specify a domain name for this installation.""")
        if not options['configured'] and 'new_username' not in options:
            errorList.append("You must enter a username to be created")
        if not options['configured'] and 'new_email' not in options:
            errorList.append("You must enter an administrator email address")
        if not options['configured'] and \
               ('new_password' not in options or 'new_password2' not in options):
            errorList.append("You must enter initial passwords")
        elif not options['configured'] and options['new_password'] != \
                 options['new_password2']:
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
        isConfigured, configurableOptions = \
                self.callBackend('getRBAConfiguration')

        # if the namespace has already been set, don't allow them to change it
        # FIXME this needs to be changed - implemented for RBL-2905.
        dflNamespace = config.MintConfig().namespace
        allowNamespaceChange = not isConfigured or (configurableOptions['namespace'] == dflNamespace)

        # Backend returns Unicode for keys, which is suboptimal for Kid
        sanitizedConfigurableOptions = \
                dict([(str(k),v) for k, v in configurableOptions.iteritems()])

        import epdb;epdb.st()
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
    def doSetup(self, *args, **kwargs):
        """
        Called upon posting the setup form.
        """

        # Normalize kwargs into a minimal set of options
        normalizedOptions = self._normalizeFormKwargs(kwargs)

        # Validate the setup form
        errorList = self._validateSetupForm(normalizedOptions)
        if errorList:
            return dict(errors=errorList)

        # Call backend to save, return error if unsuccessful
        saved = self.callBackend('updateRBAConfig', normalizedOptions)
        if not saved:
            return dict(errors=['Failed to save rBuilder configuration.'])

        # Attempt to restart Apache; warn if we can't
        apacheRestarted = self.callBackend('restartApache')
        message = "Successfully saved the rBuilder configuration."
        if not apacheRestarted:
            successMsg += " However, there was a problem restarting the rBuilder " \
                          "web service. You may need to restart the appliance "  \
                          "for the new configuration to take effect."

        # Create the rMake repository and restart rMake if needed.
        # If this gets called twice, it's no big deal, as the
        # underlying code will not create duplicate repositories.
        self.callBackend('setupRMake')

        # Regardless if Apache restarts, move on in the wizard
        self.wizardDone()
        return dict(message=successMsg)

