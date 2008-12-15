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


class RBASetup(rAAWebPlugin):
    """
    Represents the web side of the plugin.
    """
    # Name to be displayed in the side bar.
    displayName = _("rBuilder Setup")

    # Name to be displayed on mouse over in the side bar.
    tooltip = _("Plugin for setting up the rBuilder")

    @raa.web.expose(template="rPath.rbasetup.index")
    def index(self):
        return dict()

    @raa.web.expose(allow_xmlrpc=True, allow_json=True)
    def doSetup(self):
        self.wizardDone()
        return dict()

