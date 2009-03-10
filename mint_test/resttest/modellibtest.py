#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os

import testsetup
import testsuite

from mint.rest import modellib
from mint.rest.modellib import xmlformatter

class ModelLibTest(testsuite.TestCase):
    def testModelXmlFormatter(self):
        class Field1(modellib.fields.Field):
            pass
        class Field2(modellib.fields.Field):
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

        controller = None
        request = None
        formatter = xmlformatter.XMLFormatter(controller)
        self.failUnlessEqual(formatter.toText(request, m), """\
<?xml version='1.0' encoding='UTF-8'?>
<model>
  <foo1>a</foo1>
  <foo2>b</foo2>
</model>
""")

        m = self.failUnlessRaises(TypeError, Model, foo3 = "c")
        self.failUnlessEqual(str(m),
            "Model() got an unexpected keyword argument 'foo3'")

    def testModelXmlFormatterTypes(self):
        class Model1(modellib.Model):
            class Meta(object):
                name = "subnode"

            intField2 = modellib.fields.IntegerField()

        class Model(modellib.Model):
            class Meta(object):
                name = "root"
            intField = modellib.fields.IntegerField()
            charField = modellib.fields.CharField()
            boolField = modellib.fields.BooleanField()
            subNode = modellib.fields.ModelField(Model1)
            absoluteUrl = modellib.fields.AbsoluteUrlField()
            emailField = modellib.fields.EmailField()
            dateTimeField = modellib.fields.DateTimeField()
            versionField = modellib.fields.VersionField()
            flavorField = modellib.fields.FlavorField()
            listField = modellib.fields.ListField(Model1,
                displayName = "list_field")

            def get_absolute_url(slf):
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

        class Controller(object):
            def url(slf, req, *components):
                return os.path.join(*components)
        controller = Controller()
        request = None
        formatter = xmlformatter.XMLFormatter(controller)
        self.failUnlessEqual(formatter.toText(request, m), """\
<?xml version='1.0' encoding='UTF-8'?>
<root>
  <intField>1</intField>
  <charField>a</charField>
  <boolField>1</boolField>
  <subNode>
    <intField2>2</intField2>
  </subNode>
  <absoluteUrl>http://world.top/plateau</absoluteUrl>
  <emailField>who@nowhere.net</emailField>
  <dateTimeField>12/13/2004</dateTimeField>
  <versionField>1.0</versionField>
  <flavorField>is: x86</flavorField>
  <list_field>
    <intField2>0</intField2>
  </list_field>
  <list_field>
    <intField2>1</intField2>
  </list_field>
</root>
""")


if __name__ == "__main__":
    testsetup.main()
