from mint.rest import modellib
from mint.rest.modellib import fields

class ServiceLevel(modellib.Model):
    status = fields.CharField(isAttribute=True)
    daysRemaining = fields.IntegerField(isAttribute=True)
    expired = fields.BooleanField(isAttribute=True)
    limited = fields.BooleanField(isAttribute=True)

class Identity(modellib.Model):
    rbuilderId = fields.CharField()
    serviceLevel = fields.ModelField(ServiceLevel)
    registered = fields.BooleanField()


class RegistrationStub(modellib.Model):
    class Meta(object):
        name = 'registration'
    id = fields.AbsoluteUrlField(isAttribute=True)
    registrationForm = fields.UrlField('registration.form', None)

    def get_absolute_url(self):
        return 'registration',
