#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj
import sys

   
class UserNotices(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['user_notice', 'global_notice']
    _xobj = xobj.XObjMetadata(tag='user_notices', elements=['global_notice', 'user_notice'])


class UserNotice(modellib.XObjIdModel):
    class Meta:
        db_table = 'notices_usernotice'

    user_notice_id = models.AutoField(primary_key=True)
    notice = models.TextField()
    user_id = modellib.XObjHidden(models.IntegerField())
    

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj