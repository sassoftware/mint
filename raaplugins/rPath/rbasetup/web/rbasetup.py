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

class rBASetup(rAAWebPlugin):
    """
    Represents the web side of the plugin.
    """
    # Name to be displayed in the side bar.
    displayName = _("rBuilder Setup")

    # Name to be displayed on mouse over in the side bar.
    tooltip = _("Plugin for setting up the rBuilder Appliance")

    @raa.web.expose(template="rPath.rbasetup.index")
    def index(self):
        # Get the configuration from the backend
        isConfigured, configurableOptions = \
                self.callBackend('getRBAConfiguration')

        # if the namespace has already been set, don't allow them to change it
        # FIXME this needs to be changed - implemented for RBL-2905.
        dflNamespace = config.MintConfig().namespace
        allowNamespaceChange = (configurableOptions['namespace'][0] == dflNamespace)

        return dict(isConfigured=isConfigured,
                configurableOptions=configurableOptions,
                configGroups=configGroups,
                allowNamespaceChange=allowNamespaceChange)

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def doSetup(self):
        self.wizardDone()
        return dict()

