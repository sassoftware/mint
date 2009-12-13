from mint.rest.modellib import Model
from mint.rest.modellib import fields

XSI = 'http://www.w3.org/2001/XMLSchema-instance'
SCHEMALOC = 'http://www.rpath.com/permanent/factorydef-1.0.xsd factorydef-1.0.xsd'

class Description(Model):
    desc = fields.CharField()

class Metadata(Model):
    displayName = fields.CharField()
    descriptions = fields.ListField(Description)

class Prompt(Model):
    desc = fields.CharField()

class Constraints(Model):
    descriptions = fields.ListField(Description)
    regexp = fields.CharField()

class DescriptorField(Model):
    name = fields.CharField()
    required = fields.BooleanField()
    descriptions = fields.ListField(Description)
    prompt = fields.ModelField(Prompt)
    type = fields.CharField()
    password = fields.BooleanField()
    constraints = fields.ModelField(Constraints)

class DataFields(Model):
    field = fields.ListField(DescriptorField)

class ConfigDescriptor(Model):
    xsi = fields.CharField(isAttribute=True, displayName='{%s}schemaLocation' % XSI)
    metadata = fields.ModelField(Metadata)
    dataFields = fields.ModelField(DataFields)

def descriptorFactory(*args, **kw):
    d = ConfigDescriptor(xsi=SCHEMALOC, **kw)
    d.nsmap = {'xsi' : XSI}
    return d            
