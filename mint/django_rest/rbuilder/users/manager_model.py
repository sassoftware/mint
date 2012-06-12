#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.modellib import basemodels

class UserManager(basemodels.BaseManager):
    def load_from_object(self, xobjModel, request, flags=None):
        # We absolutely don't want the model to be saved, we'll let the
        # old rbuilder interface handle the saving
        return basemodels.BaseManager.load_from_object(self,
            xobjModel, request, flags=flags.copy(save=False))
