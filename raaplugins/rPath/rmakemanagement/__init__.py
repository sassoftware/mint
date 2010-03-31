#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved.
#

from gettext import gettext as _

from raaplugins.services import *

pluginpath='/rmakemanagement'

rMakeServiceName = "rmake"
nodeServiceName = "rmake-node"

pageList = {
    'index' : _("Manage Server"),
    'nodes' : _("Manage Nodes")
}


COMMAND_RESET = '/usr/share/rbuilder/scripts/rmake-reset'


