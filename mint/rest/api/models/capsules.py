from mint.rest.modellib import Model
from mint.rest.modellib import fields

class ResourceError(Model):
    class Meta(object):
        name = 'resourceError'

    id = fields.AbsoluteUrlField(isAttribute=True)
    code = fields.CharField()
    message = fields.CharField()
    resolved = fields.BooleanField()
    resolvedMessage = fields.CharField()
    timestamp = fields.IntegerField()
    contentSourceName = fields.CharField(display = False)
    instanceName = fields.CharField(display = False)

    def get_absolute_url(self):
        return ('contentSources', self.contentSourceName,
            "instances", self.instanceName, "errors", str(self.id))

class ResourceErrors(Model):
    resourceError = fields.ListField(ResourceError)
