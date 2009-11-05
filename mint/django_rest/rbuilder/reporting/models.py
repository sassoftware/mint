from django.db import models

from mint.django_rest import rbuilder
from mint.django_rest.rbuilder.models import Users

from xobj import xobj

# Create your models here.
class ReportType(models.Model):
    
    name = models.CharField(max_length=128)
    description = models.TextField()
        
    #Hide from xobj
    _reportTypeId = models.AutoField(primary_key=True, db_column='reporttypeid')
    _timecreated = models.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    _timeupdated = models.DecimalField(max_digits=14, decimal_places=3, db_column='timeupdated')
    _active = models.SmallIntegerField(default=1, db_column='active')
    _creator = models.ForeignKey(Users, db_column='creatorid', related_name='typecreator', null=True)
    _uri = models.CharField(unique=True, max_length=128, db_column='uriname')
    
    #xobj Elements   
    def populateElements(self, request):
        self.id = rbuilder.IDElement(request.build_absolute_uri("./" +self._uri))
        self.timeCreated = self._timecreated.to_eng_string()
        self.timeModified = self._timeupdated.to_eng_string()
        if self._creator is not None:
            self.creator = rbuilder.LinkElement(request.build_absolute_uri("../../users/" + self._creator.username), self._creator.username)
        self.active = bool(self._active)
        self.data = rbuilder.LinkElement(request.build_absolute_uri("./" + self._uri + "/data/"))
        self.descriptor = rbuilder.LinkElement(request.build_absolute_uri("./" + self._uri + "/descriptor/"))
    
    class Meta:
        db_table = u'reporttype'
        
    def __unicode__(self):
        return self._uri
    
    #describe how the object should be presented.
    _xobj = xobj.XObjMetadata(
	    attributes = {
		             'id' : str,
				     },
	    elements = ['name','description','descriptor','data','timeCreated','timeModified','creator',]
	    )

class ReportTypes(object):
    
    def __init__(self):
        self.__class__.__name__ = 'reportTypes'
        
    def addQueryset(self, queryset):
        self.reportType = queryset

class SystemUpdate(models.Model):
    _systemupdateid = models.AutoField(primary_key=True, db_column='systemupdateid')
    serverName = models.CharField(max_length=128, db_column='servername')
    repositoryName = models.CharField(max_length=128, db_column='repositoryname')
    _updatetime = models.DecimalField(max_digits=14, decimal_places=3, db_column='updatetime')
    updateUser = models.CharField(max_length=128, db_column='updateuser')
    
    class Meta:
        db_table = u'systemupdate'
    
    