#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
from mint import config
from mint import mint_error
from mint.django_rest.rbuilder import models as rbuildermodels

log = logging.getLogger(__name__)


class RbuilderDjangoManager(object):
    def __init__(self, cfg=None, userName=None):
        self.cfg = cfg
        self._auth = None
        
        if not self.cfg:
            try:
                cfgPath = config.RBUILDER_CONFIG
                self.cfg = config.getConfig(cfgPath)
            except mint_error.ConfigurationMissing:
                log.info("Failed to build mint configuration, "
                        "expected in local mode only")
                # Use an empty config object
                self.cfg = None
        
        if userName is None:
            self.user = None
        else:
            # The salt field contains binary data that blows django's little
            # mind when it tries to decode it as UTF-8. Since we don't need it
            # here, defer the loading of that column
            self.user = rbuildermodels.Users.objects.defer("salt").get(username = userName)

    def setAuth(self, auth, user):
        self._auth = auth
        self.user = user
