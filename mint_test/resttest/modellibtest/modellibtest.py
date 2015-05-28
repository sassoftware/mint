#!/usr/bin/python
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


import os
import re
from testrunner import testcase

from mint.rest import modellib
from mint.rest.modellib import fields
from mint.rest.modellib import converter

class _Controller(object):
    def url(slf, req, *components):
        return os.path.join(*components)


class ModelLibTest(testcase.TestCase):

    def toString(self, item):
        controller = _Controller()
        return converter.toText('xml', item, controller, None)

    def fromString(self, cls, text):
        controller = _Controller()
        return converter.fromText('xml', text, cls, controller, None)

    def getFieldString(self, item, fieldName):
        txt = self.toString(item)
        match = re.search('(<%s>.*</%s>)' % (fieldName, fieldName), txt)
        if match:
            return match.groups()[0]
        match = re.search('(<%s[^>]*\>)' % (fieldName,), txt)
        if match:
            return match.groups()[0]
        raise RuntimeError('no field %s' % fieldName)
        
        
    def testModelXmlFormatter(self):
        class Field1(fields.Field):
            pass
        class Field2(fields.Field):
            pass
        class Field3(object):
            pass
        class Model(modellib.Model):
            foo1 = Field1()
            foo2 = Field2()
            foo3 = Field3()

        m = Model(foo1 = 'a', foo2 = 'b')
        self.failUnlessEqual(m.foo1, "a")
        self.failUnlessEqual(m.foo2, "b")

        self.failUnlessEqual(self.toString(m), """\
<?xml version='1.0' encoding='UTF-8'?>
<model>
  <foo1>a</foo1>
  <foo2>b</foo2>
</model>
""")

        #m = self.failUnlessRaises(TypeError, Model, foo3 = "c")
        #self.failUnlessEqual(str(m),
        #    "Model() got an unexpected keyword argument 'foo3'")

    def testModelXmlFormatterTypes(self):
        raise testcase.SkipTestException("elements are spontaneously reordered during automated tests")
        class Model1(modellib.Model):
            class Meta(object):
                name = "subnode"

            intField2 = fields.IntegerField()

        class Model(modellib.Model):
            class Meta(object):
                name = "root"
            intField = fields.IntegerField()
            charField = fields.CharField()
            boolField = fields.BooleanField()
            subNode = fields.ModelField(Model1)
            absoluteUrl = fields.AbsoluteUrlField()
            emailField = fields.EmailField()
            dateTimeField = fields.DateTimeField()
            versionField = fields.VersionField()
            labelField = fields.LabelField()
            flavorField = fields.FlavorField()
            listField = fields.ListField(Model1,
                displayName = "list_field")

            def get_absolute_url(self):
                return [ "http://world.top/plateau" ]

        m1 = Model1(intField2 = 2)
        m = Model(intField = 1, charField = "a", boolField = 1, subNode = m1,
            listField = [ Model1(intField2 = j) for j in range(2) ],
            absoluteUrl = "http://nowhere.net/42",
            emailField = "who@nowhere.net",
            dateTimeField = "12/13/2004",
            versionField = "/localhost@rpl:1/1.0-1-1",
            labelField = "example.label@rpl:devel",
            flavorField = "is: x86",)
        self.failUnlessEqual(m.intField, 1)
        self.failUnlessEqual(m.charField, "a")

        xml = self.toString(m)
        self.failUnlessEqual(xml, """\
<?xml version='1.0' encoding='UTF-8'?>
<root>
  <intField>1</intField>
  <charField>a</charField>
  <boolField>true</boolField>
  <subNode>
    <intField2>2</intField2>
  </subNode>
  <absoluteUrl>http://world.top/plateau</absoluteUrl>
  <emailField>who@nowhere.net</emailField>
  <dateTimeField>12/13/2004</dateTimeField>
  <versionField>/localhost@rpl:1/1.0-1-1</versionField>
  <labelField>example.label@rpl:devel</labelField>
  <flavorField>is: x86</flavorField>
  <list_field>
    <intField2>0</intField2>
  </list_field>
  <list_field>
    <intField2>1</intField2>
  </list_field>
</root>
""")

        m2 = self.fromString(Model, xml)
        self.failUnlessEqual(len(m2.listField), 2)

    def testBooleanField(self):
        class Model(modellib.Model):
            boolField = fields.BooleanField()
        xml = self.getFieldString(Model(True), 'boolField')
        assert(xml == "<boolField>true</boolField>")
        xml = self.getFieldString(Model(False), 'boolField')
        assert(xml == "<boolField>false</boolField>")
        assert(self.fromString(Model,
                    self.toString(Model(True))).boolField == True)
        assert(self.fromString(Model,
                    self.toString(Model(False))).boolField == False)

    def testModelField(self):
        class Model1(modellib.Model):
            intField = fields.IntegerField()
        
        class Model(modellib.Model):
            subNode = fields.ModelField(Model1)

        xml = self.toString(Model(Model1(1)))
        self.assertEquals(xml, """\
<?xml version='1.0' encoding='UTF-8'?>
<model>
  <subNode>
    <intField>1</intField>
  </subNode>
</model>
""")
        model = self.fromString(Model, xml)
        assert(model.subNode.intField == 1)
        self.assertEquals(self.toString(model), xml)

    def testAbsoluteUrl(self):
        class Model(modellib.Model):
            url = fields.AbsoluteUrlField()
            def get_absolute_url(self):
                return ['http://foo']

        xml = self.getFieldString(Model(), 'url')
        self.assertEquals(xml, '<url>http://foo</url>')
