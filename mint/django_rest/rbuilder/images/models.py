#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# Image models -- may be heavily in flux as Target service evolves
# or may be replaced by target service.  Don't get attached.
# **THESE ARE CURRENTLY JUST STUBS TO UNBLOCK DEVELOPMENT**

from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj

APIReadOnly = modellib.APIReadOnly

class Images(modellib.Collection):

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'images')
    list_fields = ['image']
    grant = []
    objects = modellib.RbacPermissionsManager()
    view_name = 'Images'

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.image]

################################################
# WHAT IS THIS?  IT's JUST A PLACEHOLDER
#
# THIS SHOULD PROBABLY BE / MERGE WITH OUR MODEL
# OF A UNIFIED TABLE that contains images
# from targets (target service) as well as 
# ones we can deploy
#
#  V V V V V V V V V V V V V V V V V V V V 
################################################

class Image(modellib.XObjIdModel):
    
    # XSL = "fixme.xsl" # TODO

    class Meta:
        # db_table = 'to_be_determined'
        abstract = True

    view_name = 'Image'

    _xobj = xobj.XObjMetadata(
        tag = 'image'
    )
    _xobj_hidden_accessors = set([])
    summary_view = []

    id = D(models.AutoField(primary_key=True),
        "the database ID for the permission")
    name = D(models.TextField(), 
        "the database ID for the permission")


