from django.db import models

from mint.django_rest.rbuilder.models import Users

from xobj import xobj

# Create your models here.
class ReportType(models.Model):
    reportTypeId = models.AutoField(primary_key=True, db_column='reporttypeid')
    URIname = models.CharField(unique=True, max_length=128)
    name = models.CharField(max_length=128)
    description = models.TextField()
    _timecreated = models.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    #timecreated = _timecreated.to_eng_string
    _timeupdated = models.DecimalField(max_digits=14, decimal_places=3, db_column='timeupdated')
    #timeupdated = _timeupdated.to_eng_string
    active = models.SmallIntegerField(default=1)
    creator = models.ForeignKey(Users, db_column='creatorid', related_name='typecreator', null=True)
    
    class Meta:
        db_table = u'reporttype'
        
    def __unicode__(self):
        return self.URIname
 
