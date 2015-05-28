#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


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
