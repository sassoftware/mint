#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from mint import config
from mint.django_rest.rbuilder import models as rbuildermodels

class RbuilderDjangoManager(object):
    def __init__(self, cfg=None, userName=None):
        self.cfg = cfg
        
        if not self.cfg:
            cfgPath = config.RBUILDER_CONFIG
            self.cfg = config.getConfig(cfgPath)
        
        if userName is None:
            self.user = None
        else:
            # The salt field contains binary data that blows django's little
            # mind when it tries to decode it as UTF-8. Since we don't need it
            # here, defer the loading of that column
            self.user = rbuildermodels.Users.objects.defer("salt").get(username = userName)
