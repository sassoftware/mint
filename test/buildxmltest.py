#!/usr/bin/python2.4
#
# Copyright (c) 2007 rPath, Inc.
#

import testsuite
testsuite.setup()

import StringIO
import elementtree.ElementTree

from mint import buildxml
from mint import buildtypes
from mint import mint_error

f = open('archive/build.xml')
buildXml = f.read()
f.close()

class BuildXmlTest(testsuite.TestCase):
    def testOrthogonalAggregate(self):
        a = {'1': 1}
        b = {'2': 2}
        res = buildxml.dictAggregate(a, b)

        ref = {'1': 1, '2': 2}

        self.failIf(res != ref, "dictAggregate: Expected %s but got %s" % \
                        (ref, res))

    def testCollideAggregate(self):
        a = {'1': 1}
        b = {'1': 2}
        res = buildxml.dictAggregate(a, b)

        ref = {'1': 2}

        self.failIf(res != ref, "dictAggregate: Expected %s but got %s" % \
                        (ref, res))

        res = buildxml.dictAggregate(b, a)

        ref = {'1': 1}

        self.failIf(res != ref, "dictAggregate: Expected %s but got %s" % \
                        (ref, res))

    def testUpdateAggregate(self):
        a = { 'a': {'1': 1}}
        b = {'a': {'2': 2}}

        res = buildxml.dictAggregate(a, b)

        ref = { 'a': {'1': 1, '2': 2}}

        self.failIf(res != ref, "dictAggregate: Expected %s but got %s" % \
                        (ref, res))

    def testMismatchAggregate(self):
        a = { 'a': {'1': 1}}
        b = {'a': 'b'}

        res = buildxml.dictAggregate(a, b)

        ref = { 'a': 'b'}

        self.failIf(res != ref, "dictAggregate: Expected %s but got %s" % \
                        (ref, res))
        res = buildxml.dictAggregate(b, a)

        ref = a

        self.failIf(res != ref, "dictAggregate: Expected %s but got %s" % \
                        (ref, res))

    def testBuildsFromXml(self):
        res = buildxml.buildsFromXml(buildXml)
        assert len(res) == 5

    def testOrigBuildsFromXml(self):
        res = buildxml.buildsFromXml(buildXml, splitDefault = True)
        assert len(res) == 6

    def testDictFromElem(self):
        sData = StringIO.StringIO(buildXml)
        tree = elementtree.ElementTree.ElementTree(file = sData)

        root = tree.getroot()

        elem = [x for x in root.getchildren() \
                    if x.attrib == {'type': 'live_iso'}][0]

        res = buildxml.dictFromElem(elem)

        ref = {'troveName': 'group-livecd',
               'type': buildtypes.LIVE_ISO,
               'name': 'My Test LiveCD'}
        self.failIf(res != ref, "dictFromElem: Expected %s but got %s" % \
                        (ref, res))

    def testBadType(self):
        sData = StringIO.StringIO(buildXml.replace('live_iso', 'bad_name'))

        tree = elementtree.ElementTree.ElementTree(file = sData)

        root = tree.getroot()

        elem = [x for x in root.getchildren() \
                    if x.attrib == {'type': 'bad_name'}][0]

        self.assertRaises(mint_error.BuildXmlInvalid,
                          buildxml.dictFromElem, elem)

    def testMultiDefault(self):
        self.assertRaises(mint_error.BuildXmlInvalid,
                          buildxml.buildsFromXml,
                          buildXml.replace('live_iso', 'default'))


    def testBadVersion(self):
        self.assertRaises(mint_error.BuildXmlInvalid,
                          buildxml.buildsFromXml,
                          buildXml.replace('version', 'missing'))

    def testDataToXml(self):
        buildList = [{'troveName': 'group-test'},
                     {'baseFlavor': 'is: x86',
                      'type': buildtypes.RAW_FS_IMAGE},
                     {'data': {'swapSize': 128,
                               'freespace': 512},
                      'type': buildtypes.VMWARE_IMAGE},
                     {'type': buildtypes.RAW_HD_IMAGE,
                      'baseFlavor': 'xen,domU is:x86',
                      'troveName': 'group-xen'}]

        ref = [{'baseFlavor': 'is: x86',
                'troveName': 'group-test',
                'type': buildtypes.RAW_FS_IMAGE},
               {'data': {'freespace': '512', 'swapSize': '128'},
                'troveName': 'group-test',
                'type': buildtypes.VMWARE_IMAGE},
               {'baseFlavor': 'xen,domU is:x86',
                'troveName': 'group-xen',
                'type': buildtypes.RAW_HD_IMAGE}]

        xml = buildxml.xmlFromData(buildList)

        refXml = \
"""<buildDefinition version="1.0">
    <build type="default">
        <troveName>group-test</troveName>
    </build>
    <build type="RAW_FS_IMAGE">
        <baseFlavor>is: x86</baseFlavor>
    </build>
    <build type="VMWARE_IMAGE">
        <buildValue name="freespace">512</buildValue>
        <buildValue name="swapSize">128</buildValue>
    </build>
    <build type="RAW_HD_IMAGE">
        <baseFlavor>xen,domU is:x86</baseFlavor>
        <troveName>group-xen</troveName>
    </build>
</buildDefinition>
"""
        self.failIf(xml != refXml, "Expected:\n%s\nbut got:\n%s" % \
                        (refXml, xml))
        res = buildxml.buildsFromXml(xml)
        self.failIf(ref != res, "Expected %s but got %s" % (ref, res))

    def testDefaultXMLToBuilds(self):
        defaultXml = '<buildDefinition version="1.0"/>\n'
        self.failUnlessEqual(buildxml.buildsFromXml(defaultXml), [])

    def testBuildToXmlVer(self):
        self.assertRaises(AssertionError, buildxml.xmlFromData, [], '-1.0')

    def testDoubleDefault(self):
        buildList = [{'troveName': 'group-test'},
                     {'troveName': 'group-test'}]

        self.assertRaises(mint_error.BuildXmlInvalid,
                          buildxml.xmlFromData, buildList)


if __name__ == "__main__":
    testsuite.main()
