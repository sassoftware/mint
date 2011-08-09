#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.modellib import basemodels

class UserManager(basemodels.BaseManager):
    def load_from_object(self, xobjModel, request, save=True, load=True):
        # We absolutely don't want the model to be saved, we'll let the
        # old rbuilder interface handle the saving
        save = False
        return basemodels.BaseManager.load_from_object(self,
            xobjModel, request, save=save, load=load)
