from mint.rest import modellib
from mint.rest.modellib import fields

class ServiceLevel(modellib.Model):
    status = fields.CharField(isAttribute=True)
    expired = fields.BooleanField(isAttribute=True)
    daysRemaining = fields.IntegerField(isAttribute=True)
    limited = fields.BooleanField(isAttribute=True)

class Identity(modellib.Model):
    rbuilderId = fields.CharField()
    serviceLevel = fields.ModelField(ServiceLevel)
    registered = fields.BooleanField()
