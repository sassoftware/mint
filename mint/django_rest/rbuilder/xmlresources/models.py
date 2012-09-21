#
# Copyright (c) 2011 rPath, Inc.
#

import re
import sys
from django.db import models
from mint import helperfuncs
from mint.django_rest.rbuilder import modellib
from xobj import xobj

class XmlResource(modellib.XObjIdModel):
    
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='xml_resource')
    view_name = "XmlResource"
    
    schema = modellib.SyntheticField()
    xml_data = modellib.SyntheticField()
    error = modellib.SyntheticField()

    def __unicode__(self):
        return self.hostname

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)

        return xobjModel

    def computeSyntheticFields(self, sender, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass
    
class XmlResourceError(modellib.XObjIdModel):
    
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='error')
    code = modellib.SyntheticField()
    message = modellib.SyntheticField()
    details = modellib.SyntheticField()

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
