#
# Copyright (c) 2011 rPath, Inc.
#

import sys
from mint.django_rest.rbuilder import modellib
from xobj import xobj

class XmlResource(modellib.XObjIdModel):
    
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='xml_resource')
    view_name = "XmlResource"
    
    schema = modellib.SyntheticField()
    xml = modellib.SyntheticField()
    status = modellib.SyntheticField()

    def __unicode__(self):
        return self.hostname

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)

        return xobjModel
    
class XmlResourceStatusErrors(modellib.XObjIdModel):
    
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='errors')
    
    list_fields = ['error']
    error = []
    
class XmlResourceStatus(modellib.XObjIdModel):
    
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='status')
        
    success = modellib.SyntheticField()
    code = modellib.SyntheticField()
    details = modellib.SyntheticField()
    errors = XmlResourceStatusErrors()
    
    def __init__(self):
        self.errors = XmlResourceStatusErrors()
    
class XmlResourceStatusError(modellib.XObjIdModel):
    
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='error')
    
    column = modellib.SyntheticField()
    domain = modellib.SyntheticField()
    domain_name = modellib.SyntheticField()
    filename = modellib.SyntheticField()
    level = modellib.SyntheticField()
    level_name = modellib.SyntheticField()
    line = modellib.SyntheticField()
    message = modellib.SyntheticField()
    type = modellib.SyntheticField()
    type_name = modellib.SyntheticField()
    
    def __init__(self, message=None, column=None, domain=None, domain_name=None, filename=None, level=None, level_name=None, line=None, type=None, type_name=None):
        self.message = message
        self.column = column
        self.domain = domain
        self.domain_name = domain_name
        self.filename = filename
        self.level = level
        self.level_name = level_name
        self.line = line
        self.type = type
        self.type_name = type_name

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
