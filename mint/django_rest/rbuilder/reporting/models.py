from django.db import models

from mint.django_rest import rbuilder, logger
from mint.django_rest.rbuilder.models import Users

from xobj import xobj

# Create your models here.
class Report(object):
    
    #xobj Elements   
    def populateElements(self, request):
        url = ((request.build_absolute_uri().find(self.uri + "/") != -1 
            and request.build_absolute_uri()) 
            or request.build_absolute_uri( self.uri + "/"))
        self.id = rbuilder.IDElement(url)
        self.data = rbuilder.LinkElement(url + "data/")
        self.descriptor = rbuilder.LinkElement(url + "descriptor/")
        if self.adminReport:
            self.enabled = request._is_admin
        else:
            self.enabled = True 
    
    #describe how the object should be presented.
    _xobj = xobj.XObjMetadata(
	    attributes = {
		             'id' : str,
				     },
	    elements = ['name','description','descriptor','data','timeCreated',]
	    )

class Reports(object):
    
    def __init__(self):
        self.__class__.__name__ = 'reports'
        
    def addQueryset(self, queryset):
        self.report = queryset

class SystemUpdate(models.Model):
    _systemupdateid = models.AutoField(primary_key=True, db_column='systemupdateid')
    serverName = models.CharField(max_length=128, db_column='servername')
    repositoryName = models.CharField(max_length=128, db_column='repositoryname')
    _updatetime = models.DecimalField(max_digits=14, decimal_places=3, db_column='updatetime')
    updateUser = models.CharField(max_length=128, db_column='updateuser')
    
    class Meta:
        db_table = u'systemupdate'
    
class RepositoryLogStatus(models.Model):
    logname = models.CharField(primary_key=True, max_length=128)
    inode = models.IntegerField()
    logoffset = models.IntegerField()
    
    class Meta:
        db_table = u'repositorylogstatus'