from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj

class GlobalNotices(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['global_notice']
    _xobj = xobj.XObjMetadata(tag='global_notices')
    
    
class GlobalNotice(modellib.XObjIdModel):
    class Meta:
        db_table = 'notices_globalnotice'
    
    _xobj = xobj.XObjMetadata(attributes={'id':str})
    
    id = models.AutoField(primary_key=True)
    notice = models.TextField()
    
    
class UserNotices(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['user_notice']
    _xobj = xobj.XObjMetadata(tag='user_notices', elements=['global_notices', 'user_notice'])
    global_notices = models.ForeignKey(GlobalNotice, db_tablespace='notices_globalnotices', null=True)


class UserNotice(modellib.XObjIdModel):
    class Meta:
        db_table = 'notices_usernotice'
    
    _xobj = xobj.XObjMetadata(attributes={'id':str})
    
    user_notice_id = models.AutoField(primary_key=True, db_column='id')
    notice = models.TextField()
    user_id = models.IntegerField()