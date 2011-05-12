from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj
import sys

class GlobalNotices(modellib.Collection):
    class Meta:
        abstract = True
        db_table = 'notices_globalnotices'
        
    list_fields = ['global_notice']
    _xobj = xobj.XObjMetadata(tag='global_notices')
    
    
class GlobalNotice(modellib.XObjIdModel):
    class Meta:
        db_table = 'notices_globalnotice'
    
    global_notice_id = models.AutoField(primary_key=True)
    notice = models.TextField()
    
    
class UserNotices(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['user_notice']
    _xobj = xobj.XObjMetadata(tag='user_notices', elements=['global_notices', 'user_notice'])
    global_notices = models.ForeignKey(GlobalNotice, db_tablespace='notices_globalnotice', null=True)


class UserNotice(modellib.XObjIdModel):
    class Meta:
        db_table = 'notices_usernotice'

    _xobj_hidden_accessors = set(['user_id'])

    user_notice_id = models.AutoField(primary_key=True)
    notice = models.TextField()
    user_id = models.IntegerField()
    

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj