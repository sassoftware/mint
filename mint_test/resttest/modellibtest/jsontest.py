#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
import re

import testsetup
import testsuite

from mint.rest import modellib
from mint.rest.modellib import fields
from mint.rest.modellib import converter
from mint.rest.modellib import jsonconverter

class _Controller(object):
    def url(slf, req, *components):
        return os.path.join(*components)

class ModelLibTest(testsuite.TestCase):

    def toString(self, item):
        controller = _Controller()
        return converter.toText('json', item, controller, None)

    def fromString(self, cls, text):
        controller = _Controller()
        return converter.fromText('json', text, cls, controller, None)

    def testModelJsonFormatter(self):
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

        m = self.failUnlessRaises(TypeError, Model, foo3 = "c")
        self.failUnlessEqual(str(m),
            "Model() got an unexpected keyword argument 'foo3'")

    def testModelJsonFormatterTypes(self):
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
            versionField = "1.0",
            flavorField = "is: x86",)
        self.failUnlessEqual(m.intField, 1)
        self.failUnlessEqual(m.charField, "a")

        xml = self.toString(m)
        self.failUnlessEqual(xml, '{"root": {"absoluteUrl": "http://world.top/plateau", "flavorField": "is: x86", "boolField": "1", "dateTimeField": "12/13/2004", "intField": "1", "emailField": "who@nowhere.net", "list_field": [{"intField2": "0"}, {"intField2": "1"}], "charField": "a", "versionField": "1.0", "subNode": {"intField2": "2"}}}')

    def testBooleanField(self):
        class Model(modellib.Model):
            boolField = fields.BooleanField()
        xml = self.toString(Model(True))
        assert(xml == '{"model": {"boolField": "true"}}')
        xml = self.toString(Model(False))
        assert(xml == '{"model": {"boolField": "false"}}')
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

if __name__ == "__main__":
    testsetup.main()
