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
    
    global_notice_id = models.AutoField(primary_key=True)
    global_notice = models.TextField()
    
    
class UserNotices(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['user_notice']
    _xobj = xobj.XObjMetadata(tag='user_notices')


class UserNotice(modellib.XObjIdModel):
    class Meta:
        db_table = 'notices_usernotice'
    
    user_notice_id = models.AutoField(primary_key=True)
    user_notice = models.TextField()
    global_notices = models.ForeignKey(GlobalNotice, null=True)
    user_id = models.IntegerField()