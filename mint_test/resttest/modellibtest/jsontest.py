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
        txt = converter.toText('json', item, controller, None)
        return re.sub('\n *', '', txt)

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

        self.failUnlessEqual(self.toString(m), '{"model": {"foo1": "a", "foo2": "b"}}')

        #m = self.failUnlessRaises(TypeError, Model, foo3 = "c")
        #self.failUnlessEqual(str(m),
        #    "Model() got an unexpected keyword argument 'foo3'")

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

        txt = self.toString(m)
        self.failUnlessEqual(txt, '{"root": {"absoluteUrl": "http://world.top/plateau", "flavorField": "is: x86", "boolField": "true", "dateTimeField": "12/13/2004", "intField": "1", "emailField": "who@nowhere.net", "list_field": [{"intField2": "0"}, {"intField2": "1"}], "charField": "a", "versionField": "1.0", "subNode": {"intField2": "2"}}}')


    def testBooleanField(self):
        class Model(modellib.Model):
            boolField = fields.BooleanField()
        txt = self.toString(Model(True))
        assert(txt == '{"model": {"boolField": "true"}}')
        txt = self.toString(Model(False))
        assert(txt == '{"model": {"boolField": "false"}}')
        assert(self.fromString(Model,
                    self.toString(Model(True))).boolField == True)
        assert(self.fromString(Model,
                    self.toString(Model(False))).boolField == False)

    def testModelField(self):
        class Model1(modellib.Model):
            intField = fields.IntegerField()
        
        class Model(modellib.Model):
            subNode = fields.ModelField(Model1)

        txt = self.toString(Model(Model1(1)))
        self.assertEquals(txt, '{"model": {"subNode": {"intField": "1"}}}')
        model = self.fromString(Model, txt)
        assert(model.subNode.intField == 1)
        self.assertEquals(self.toString(model), txt)

    def testAbsoluteUrl(self):
        class Model(modellib.Model):
            url = fields.AbsoluteUrlField()
            def get_absolute_url(self):
                return ['http://foo']

        txt = self.toString(Model())
        self.assertEquals(txt, '{"model": {"url": "http://foo"}}')
