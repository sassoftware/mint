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
from raa.db import wizardrun, data
from raa.modules import raawebplugin
from raa.modules.raawebplugin import rAAWebPlugin


class NextSteps(rAAWebPlugin):
    """
    Represents the web side of the plugin.
    """
    # Name to be displayed in the side bar.
    displayName = _("Next Steps")

    # Name to be displayed on mouse over in the side bar.
    tooltip = _("Plugin for the next steps")

    @raa.web.expose(template="rPath.nextsteps.index")
    def index(self):
        return dict()

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def doSetup(self):
        # hide this plugin now
        self.setPropertyValue('raa.hidden', True, data.RDT_BOOL)
        
        self.wizardDone()
        return dict()

