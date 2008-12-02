# Copyright (c) 2005-2007 rPath, Inc
# All rights reserved

from gettext import gettext as _

from raa.modules import raawebplugin
import raa

import os
markerFile = os.path.join(os.path.sep, 'tmp', 'rbuilder_migration')

class rBuilderMigration(raawebplugin.rAAWebPlugin):
    '''
    rBuilder migration plugin
    '''
    displayName = _("rBuilder Migration")

    def disable(self):
        self.wizardDone()
        self.setPropertyValue('raa.hidden', True)
        if os.path.exists(markerFile):
            os.unlink(markerFile)

    @raa.web.expose(template = "rPath.postmigrate.index")
    def index(self, restore = False):
        prompt = not restore
        diskPresent, backups = self.callBackend('getBackups')
        complete = os.path.exists(markerFile)
        return {'complete': complete,
                'prompt': prompt,
                'diskPresent': diskPresent,
                'backups': backups}

    @raa.web.expose(allow_xmlrpc = True, allow_json = True)
    def skipPlugin(self):
        self.disable()
        return dict()

    @raa.web.expose(allow_xmlrpc = True, allow_json = True)
    def doRestore(self, filename):
        return self.callBackend('doRestore', filename)
