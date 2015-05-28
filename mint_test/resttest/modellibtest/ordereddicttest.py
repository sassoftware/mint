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


from testrunner import testcase


from mint.rest.modellib import ordereddict


class OrderedDictTest(testcase.TestCase):
    def testDict(self):
        items = [ (x,x+10) for x in range(10) ]
        odict = ordereddict.OrderedDict(items)
        assert(odict.keys() == range(10))
        assert(list(odict.iterkeys()) == range(10))
        assert(odict.values() == range(10,20))
        assert(list(odict.itervalues()) == range(10, 20))
        assert(list(odict.iteritems()) == items)
        assert(list(odict.items()) == items)
        assert(odict.pop(3) == 13)
        assert(odict.keys() == [0,1,2,4,5,6,7,8,9])
        odict[3] = 23
        assert(odict.keys() == [0,1,2,4,5,6,7,8,9,3])
        odict[1] = 22
        assert(odict.keys() == [0,1,2,4,5,6,7,8,9,3])
        assert(odict.values() == [10,22,12,14,15,16,17,18,19,23])
        assert(odict.copy().keys() == [0,1,2,4,5,6,7,8,9,3])
        assert(odict.fromkeys([1,2,3,4]).keys() == [1,2,3,4])
