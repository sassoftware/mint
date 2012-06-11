#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import re
import sys
import time
import tempfile
import simplejson
from testutils import mock

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN

from mint import buildtypes, buildtemplates, projects
from mint.lib.data import RDT_STRING, RDT_BOOL, RDT_INT
from mint.mint_error import *
from mint import builds
from mint.server import deriveBaseFunc
from mint import helperfuncs
from mint import notices_store
from mint import urltypes
from mint import userlevels
from mint import jobstatus

from conary import errors
from conary.lib import util
from conary.repository.errors import TroveNotFound
from conary import versions
from conary.deps import deps
from conary import conaryclient
from conary import conarycfg

from rpath_proddef import api1 as proddef
import fixtures

class BuildTest(fixtures.FixturedUnitTest):
    def setUp(self):
        class Counter(object):
            counter = 0
            def _generateString(slf, length):
                slf.__class__.counter += 1
                return str(slf.counter)
        # Predictable IDs
        self.counter = counter = Counter()
        self.mock(notices_store.DiskStorage, '_generateString',
                  counter._generateString)
        fixtures.FixturedUnitTest.setUp(self)

    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        assert(build.getName() == "Test Build")
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        assert(build.getTrove() ==\
            ('group-trove',
             '/conary.rpath.com@rpl:devel/0.0:1.0-1-1', '1#x86'))
        assert(build.getTroveName() == 'group-trove')
        assert(build.getTroveVersion().asString() == \
               '/conary.rpath.com@rpl:devel/1.0-1-1')
        assert(build.getTroveFlavor().freeze() == '1#x86')
        assert(build.getArch() == "x86")

        build.setFiles([["file1", "File Title 1"],
                          ["file2", "File Title 2"]])
        self.assertEquals(build.getFiles(),
            [{'size': 0, 'sha1': '', 'title': 'File Title 1',
                'fileUrls': [(5, 0, 'file1')], 'idx': 0, 'fileId': 5,
                'downloadUrl': 'http://test.rpath.local/downloadImage?fileId=5'},
             {'size': 0, 'sha1': '', 'title': 'File Title 2',
                 'fileUrls': [(6, 0, 'file2')], 'idx': 1, 'fileId': 6,
                 'downloadUrl': 'http://test.rpath.local/downloadImage?fileId=6'}])

        assert(build.getDefaultName() == 'group-trove=1.0-1-1')

        desc = 'Just some random words'
        build.setDesc(desc)
        build.refresh()
        assert(build.timeCreated)
        assert(build.timeUpdated)
        assert desc == build.getDesc()

        self.failUnless(build.createdBy, 'createdBy was not set (RBL-3076)')

    @fixtures.fixture("Full")
    def testBuildData(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        buildType = buildtypes.INSTALLABLE_ISO
        build.setBuildType(buildType)
        assert(buildType == build.buildType)
        dataTemplate = build.getDataTemplate()
        assert('showMediaCheck' in dataTemplate)
        assert('autoResolve' in dataTemplate)
        assert('freespace' not in dataTemplate)

        rDict = build.getDataDict()
        tDict = build.getDataTemplate()
        for key in tDict:
            assert(tDict[key][1] == rDict[key])

        # test behavior of booleans
        for mediaCheck in (False, True):
            build.setDataValue('showMediaCheck', mediaCheck)
            assert (build.getDataValue('showMediaCheck') is mediaCheck)

        # test bad name lockdown
        self.assertRaises(builds.BuildDataNameError,
            build.setDataValue, 'undefinedName', 'test string')
        self.assertRaises(builds.BuildDataNameError,
                          build.getDataValue, 'undefinedName')

        # test bad name with validation override
        build.setDataValue('undefinedName', 'test string',
            dataType = RDT_STRING, validate = False)
        assert('test string' == build.getDataValue('undefinedName'))

        # test bad name with validation override and no data type specified
        self.assertRaises(builds.BuildDataNameError,
            build.setDataValue, 'undefinedName', None, False)

        build.setBuildType(buildtypes.STUB_IMAGE)

        # test string behavior
        build.setDataValue('stringArg', 'foo')
        assert('foo' == build.getDataValue('stringArg'))
        build.setDataValue('stringArg', 'bar')
        assert('bar' == build.getDataValue('stringArg'))

        # test int behavior
        for intArg in range(0,3):
            build.setDataValue('intArg', intArg)
            assert(intArg == build.getDataValue('intArg'))

        # test enum behavior
        for enumArg in range(3):
            build.setDataValue('enumArg', str(enumArg))
            assert(str(enumArg) == build.getDataValue('enumArg'))

        # ensure invalid enum values are not accepted.
        self.assertRaises(ParameterError, build.setDataValue, 'enumArg', '5')
    
    @fixtures.fixture("Full")
    def testImagelessBuild(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['imagelessBuildId'])
        dataTemplate = build.getDataTemplate()
        assert(dataTemplate == {})
        assert(build.getName() == "Test Imageless Build")
        assert(build.getTrove() ==\
            ('group-dist',
             "/testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.0-1-2",
             '1#x86'))
        assert(build.getTroveName() == 'group-dist')
        assert(build.getTroveVersion().asString() == \
               "/testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-1-2")
        assert(build.getTroveFlavor().freeze() == '1#x86')
        assert(build.getArch() == "x86")
    
    @fixtures.fixture("Full")
    def testBuildDataIntegerValidation(self, db, data):
        
        # get a template, doesn't matter what build type is used
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        dataTemplate = build.getDataTemplate()

        # test freespace
        buildtemplates.freespace().validate("3")
        self.assertRaises(InvalidBuildOption, 
            buildtemplates.freespace().validate, "s3")
        self.assertRaises(InvalidBuildOption, 
            buildtemplates.freespace().validate, "-1")

        # test vmMemory
        buildtemplates.vmMemory().validate("3")
        self.assertRaises(InvalidBuildOption, 
            buildtemplates.vmMemory().validate, "s3")
        self.assertRaises(InvalidBuildOption, 
            buildtemplates.vmMemory().validate, "-1")

        # test swap size
        buildtemplates.swapSize().validate("3")
        self.assertRaises(InvalidBuildOption, 
            buildtemplates.swapSize().validate, "s3")
        self.assertRaises(InvalidBuildOption, 
            buildtemplates.swapSize().validate, "-1")

    @fixtures.fixture("Full")
    def testMaxIsoSize(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        buildType = buildtypes.INSTALLABLE_ISO
        build.setBuildType(buildType)

        for size in ('681574400', '734003200', '4700000000', '8500000000'):
            build.setDataValue('maxIsoSize', size)
            self.failIf(build.getDataValue('maxIsoSize') != size,
                        "size was mangled in xml-rpc")

        self.assertRaises(ParameterError, build.setDataValue, 'maxIsoSize',
                          '10000000')

        maxIsoSize = build.getDataDict()['maxIsoSize']
        self.failIf(maxIsoSize != '8500000000',
                    "Data dict contained %s of %s but expected %s of type str"\
                    % (str(maxIsoSize), str(type(maxIsoSize)), '8500000000'))

    @fixtures.fixture("Full")
    def testMissingBuildData(self, db, data):
        # make sure builddata properly returns the default value
        # if the row is missing. this will handle the case of a modified
        # builddata template with old builds in the database.

        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        assert(build.getBuildType() == buildtypes.INSTALLABLE_ISO)
        assert(build.getDataTemplate()['showMediaCheck'])
        assert(build.getDataTemplate()['autoResolve'])
        try:
            build.getDataTemplate()['freespace']
        except KeyError, e:
            pass
        else:
            self.fail("getDataTemplate returned bogus template data")

        db.cursor().execute("DELETE FROM BuildData WHERE name='bugsUrl'")
        db.commit()

        assert(build.getDataValue("bugsUrl") == "http://issues.rpath.com/")

        build.setBuildType(buildtypes.VMWARE_IMAGE)
        assert(build.getDataTemplate()['diskAdapter'])
        # now test new vmware data types
        build.setBuildType(buildtypes.VMWARE_IMAGE)
        assert build.getDataValue('diskAdapter') == 'lsilogic'


    @fixtures.fixture("Full")
    def testPublished(self, db, data):
        client = self.getClient("owner")
        pubBuild = client.getBuild(data['pubBuildId'])

        self.failUnless(pubBuild.getPublished(),
                    "getPublished() should return True")

        self.assertRaises(BuildPublished, pubBuild.setDataValue,
                          'stringArg', 'bar')

        self.assertRaises(BuildPublished, pubBuild.setBuildType,
                          buildtypes.STUB_IMAGE)

        self.assertRaises(BuildPublished, pubBuild.setFiles, list())


        self.assertRaises(BuildPublished, pubBuild.setTrove,
                          'Some','Dummy','Args')

        self.assertRaises(BuildPublished, pubBuild.setDesc, 'Not allowed')

        self.assertRaises(BuildPublished, client.startImageJob,
                          pubBuild.getId())

    @fixtures.fixture("Full")
    def testDelMissingFile(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])

        # ensure there are no files to do a delete over
        cu = db.cursor()
        cu.execute('DELETE FROM BuildFiles')
        db.commit()

        # historically this triggered a bad local variable reference
        build.deleteBuild()

    @fixtures.fixture("Full")
    def testMissingBuild(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])

        # make a build and delete it, to emulate a race condition
        # from the web UI
        buildId = build.getId()

        build.deleteBuild()

        # messing with that same build should now fail in a controlled
        # manner. no UnknownErrors allowed!
        self.assertRaises(BuildMissing, build.setBuildType,
                buildtypes.STUB_IMAGE)

        self.assertRaises(BuildMissing, build.deleteBuild)

        # nasty hack. unwrap the build data value so that we can attack
        # codepaths not normally allowed by client code.
        setBuildDataValue = deriveBaseFunc(client.server._server.setBuildDataValue)

        self.assertRaises(BuildMissing, setBuildDataValue,
                client.server._server, buildId, 'someKey', 'someVal',
                RDT_STRING)

        self.assertRaises(BuildMissing, build.setDesc, 'some string')

        fixtures.stockBuildFlavor(db, build.getId())

        self.assertRaises(BuildMissing, client.startImageJob, buildId)

    @fixtures.fixture("Full")
    def testBuildStatus(self, db, data):
        client = self.getClient("owner")
        buildId = data['buildId']

        cu = db.cursor()
        cu.execute("UPDATE Builds SET status = ?, statusMessage = ? "
                "WHERE buildId = ?", jobstatus.RUNNING, "starting", buildId)
        db.commit()

        self.assertEquals(client.server.getBuildStatus(buildId),
                {'status': jobstatus.RUNNING, 'message': 'starting'})

    @fixtures.fixture("Empty")
    def testGetBuildsForProjectOrder(self, db, data):
        # FIXME broken w/r/t new release arch
        client = self.getClient("test")
        hostname = "foo"
        projectId = client.newProject("Foo", hostname, "rpath.org",
                        shortname=hostname, version="1.0", prodtype="Component")

        build = client.newBuild(projectId, 'build 1')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setFiles([["file1", "File Title 1"]])

        # ugly hack. mysql does not distinguish sub-second time resolution
        time.sleep(1)

        build = client.newBuild(projectId, 'build 2')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setFiles([["file1", "File Title 1"]])

        self.failIf(client.server.getBuildsForProject(projectId) != [2, 1],
                    "getBuildsForProject is not ordered by "
                    "'most recent first'")

    @fixtures.fixture("Empty")
    def testFlavorFlags(self, db, data):
        client = self.getClient("test")
        hostname = "foo"
        projectId = client.newProject("Foo", hostname, "rpath.org",
                        shortname=hostname, version="1.0", prodtype="Component")

        build = client.newBuild(projectId, 'build 1')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86|5#use:appliance")
        self.failUnlessEqual(build.getDataValue("APPLIANCE"), 1)

        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86|5#use:appliance:xen:domU")
        self.failUnlessEqual(build.getDataValue("APPLIANCE"), 1)
        self.failUnlessEqual(build.getDataValue("XEN_DOMU"), 1)

        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        self.failUnless("APPLIANCE" not in build.getDataDict())
        self.failUnless("XEN_DOMU" not in build.getDataDict())

    @fixtures.fixture("Full")
    def testGetDisplayTemplates(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])

        self.failIf([(x[0], x[2]) \
                for x in buildtemplates.getDisplayTemplates()] != \
                    [x for x in buildtemplates.dataTemplates.iteritems()],
                    "dataTemplates lost in display translation")

    @fixtures.fixture("Full")
    def testFreespace(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])

        build.setBuildType(buildtypes.RAW_FS_IMAGE)

        self.failIf(not isinstance(build.getDataValue('freespace'), int),
                    "freespace is not an integer")

        build.setDataValue('freespace', 10, RDT_INT)

        self.failIf(not isinstance(build.getDataValue('freespace'), int),
                    "freespace is not an integer")

    @fixtures.fixture("Full")
    def testDeleteBuildFiles(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        cu = db.cursor()

        # defaults are fine
        tmpdir = tempfile.mkdtemp()
        try:
            subdir = os.path.join(tmpdir, 'subdir')
            os.mkdir(subdir)
            newfile = os.path.join(subdir, 'file')
            f = open(newfile, 'w')
            f.close()
            results = cu.execute("""SELECT urlId 
                                    FROM buildFiles bf
                                       JOIN buildFilesUrlsMap USING (fileId)
                                       JOIN FilesUrls fu USING (urlId)
                                    WHERE buildId = ? AND urlType = ?""",
                                    build.id, urltypes.LOCAL)
            results = cu.fetchall()
            assert(len(results) > 0)
            urlId = results[0][0]
            cu.execute("""UPDATE FilesUrls SET url=? WHERE urlId=?""",
                    newfile, urlId)
            db.commit()
            build.deleteBuild()
            for targ in (newfile, subdir, tmpdir):
                try:
                    os.stat(targ)
                except OSError, e:
                    # ensure the file/dirs really are gone
                    if e.errno != 2:
                        raise
        finally:
            try:
                util.rmtree(tmpdir)
            except:
                pass

    @fixtures.fixture("Full")
    def testDeleteBuildFiles2(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        cu = db.cursor()

        # really create a unqiue directory structure to ensure we don't suffer
        # from unlucky code collission
        tmpdir = tempfile.mkdtemp()
        try:
            subdir = os.path.join(tmpdir, 'subdir')
            os.mkdir(subdir)
            newfile = os.path.join(subdir, 'file')
            f = open(newfile, 'w')
            f.close()
            results = cu.execute("""SELECT urlId 
                                    FROM buildFiles bf
                                       JOIN buildFilesUrlsMap USING (fileId)
                                       JOIN FilesUrls fu USING (urlId)
                                    WHERE buildId = ? AND urlType = ?""",
                                    build.id, urltypes.LOCAL)
            results = cu.fetchall()
            assert(len(results) > 0)
            urlId = results[0][0]
            cu.execute("""UPDATE FilesUrls SET url=? WHERE urlId=?""",
                    newfile, urlId)
            db.commit()
            util.rmtree(tmpdir)
            for targ in (newfile, subdir, tmpdir):
                try:
                    os.stat(targ)
                except OSError, e:
                    # ensure the file/dirs really are gone
                    if e.errno != 2:
                        raise
            # ensure there's no ill effects of deleted a build in this manner
            build.deleteBuild()
        finally:
            try:
                util.rmtree(tmpdir)
            except:
                pass

    @fixtures.fixture('Full')
    def testUpdateMissingBuild(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        buildId = build.id
        build.deleteBuild()
        self.assertRaises(BuildMissing, client.server._server.updateBuild,
                          buildId, {})

    @fixtures.fixture('Full')
    def testUpdatePublishedBuild(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        buildId = build.id
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubRelease.publish()
        self.assertRaises(BuildPublished, client.server._server.updateBuild,
                          buildId, {})

    @fixtures.fixture('Full')
    def testUpdateInvalidColumn(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        buildId = build.id
        self.assertRaises(ParameterError,
                client.server.updateBuild, buildId, {'createdBy':  42})

    @fixtures.fixture('Full')
    def testMissingBuildTrove(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])
        build.setTrove('foo', '/localhost@rpl:1/1-1-1', 'baz')
        self.assertRaises(BuildMissing, client.server._server.setBuildTrove,
                          99, 'foo', '/localhost@rpl:1/1-1-1', 'flav')
    @fixtures.fixture('Full')
    def testMissingBuildName(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])
        build.setName('foo')
        self.assertRaises(BuildMissing, client.server._server.setBuildName,
                          99, 'foo')

    @fixtures.fixture('Full')
    def testPublishedBuildName(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        build = client.getBuild(data['buildId'])
        build.setName('foo')
        pubRel.publish()
        self.assertRaises(BuildPublished, build.setName, 'foo')

    @fixtures.fixture('Full')
    def testMissingSetBuildPublished(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        build = client.getBuild(data['buildId'])

        build.setPublished(pubRel.id, True)
        self.assertRaises(PublishedReleaseMissing, build.setPublished,
                          99, True)

    @fixtures.fixture('Full')
    def testPubSetBuildPublished(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        build = client.getBuild(data['buildId'])
        pubRel.publish()
        self.assertRaises(PublishedReleasePublished, build.setPublished,
                          pubRel.id, True)

    @fixtures.fixture('Full')
    def testEmptySetBuildPublished(self, db, data):
        client = self.getClient('owner')
        pubRel = client.getPublishedRelease(data['pubReleaseId'])
        build = client.getBuild(data['buildId'])
        build.setFiles([])
        self.assertRaises(BuildEmpty, build.setPublished, pubRel.id, True)

        # AMIs shouldn't throw BuildEmpty, as it's expected that they
        # don't have any files
        build.setBuildType(buildtypes.AMI)
        self.failUnless(build.setPublished(pubRel.id, True))

        # IMAGELESS shouldn't throw BuildEmpty, as it's expected that they
        # don't have any files
        build.setBuildType(buildtypes.IMAGELESS)
        self.failUnless(build.setPublished(pubRel.id, True))

    @fixtures.fixture('Full')
    def testMissingGetBuildType(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        self.assertRaises(BuildMissing, client.server._server.getBuildType, 99)

    @fixtures.fixture('Full')
    def testGetAvailableBuildTypes(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])
        excludeBuildTypes = self.cfg.excludeBuildTypes
        includeBuildTypes = self.cfg.includeBuildTypes
        try:
            for exTypes, inTypes in [([], []),
                                     ([buildtypes.INSTALLABLE_ISO, buildtypes.RAW_HD_IMAGE, buildtypes.LIVE_ISO], []),
                                     ([buildtypes.INSTALLABLE_ISO, buildtypes.RAW_HD_IMAGE], [buildtypes.INSTALLABLE_ISO]),
                                     ([], [buildtypes.BOOTABLE_IMAGE])]:
                self.cfg.excludeBuildTypes = exTypes
                self.cfg.includeBuildTypes = inTypes
                ret = client.server._server.getAvailableBuildTypes()
                # Enforce no excluded types are present, unless included
                for x in exTypes:
                    self.failIf(x in ret and x not in inTypes,
                        'Build type %d was not excluded' % x)
                # Enforce all included types are present, sans bootable
                for x in inTypes:
                    self.failIf(x not in ret and
                        x != buildtypes.BOOTABLE_IMAGE,
                        'Build type %d was not included' % x)
                # Enforce bootable is always absent
                self.failIf(buildtypes.BOOTABLE_IMAGE in ret, 'Bootable '
                    'image was not excluded as a valid build type')
        finally:
            self.cfg.excludeBuildTypes = excludeBuildTypes
            self.cfg.includeBuildTypes = includeBuildTypes

    @fixtures.fixture('Full')
    def testGetAvailableBuildTypes2(self, db, data):
        client = self.getClient('admin')
        targetData = client.getTargetData('ec2', 'aws')
        client.deleteTarget('ec2', 'aws')
        self.failIf(buildtypes.AMI in client.getAvailableBuildTypes(),
                "Expected AMI to be omitted")
        client.addTarget('ec2', 'aws', targetData)
        self.failUnless(buildtypes.AMI in client.getAvailableBuildTypes(),
                "AMI should have been included")

    def testAlphabatizeBuildTypes(self):
        refList = [buildtypes.INSTALLABLE_ISO,
                    buildtypes.RAW_HD_IMAGE,
                    buildtypes.VMWARE_IMAGE]
        testList = list(reversed(refList))
        res = buildtypes.alphabatizeBuildTypes(testList)
        self.assertEquals(refList, res)

        # test that ImageLess shows up at the top of the list regardless of
        # the sorting of the other image types
        refList.insert(0, buildtypes.IMAGELESS)
        testList.append(buildtypes.IMAGELESS)
        res = buildtypes.alphabatizeBuildTypes(testList)
        self.assertEquals(refList, res)

    @fixtures.fixture('Full')
    def testSetMissingFilenames(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        self.assertRaises(BuildMissing,
                          client.server._server.setBuildFilenames, 99, [])

    @fixtures.fixture('Full')
    def testSetBrokenFilenames(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        self.assertRaises(ValueError,
                          client.server._server.setBuildFilenames, build.id,
                          [['not right at all']])
        
    @fixtures.fixture('Full')
    def testSetGinormousSize(self, db, data):
        """ Tests sending the size parameter as a string to get around
            XML-RPC limits. (RBL-2789) """
        raise testsuite.SkipTestException('Notices-related transient failure')
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        client.server._server.setBuildFilenames(build.id,
                                                [['reallybigfile', '3 GB build',
                                                 '3147483647', 'F'*40 ]])
        storagePath = os.path.join(self.cfg.dataPath, 'notices', 'users',
            'owner', 'notices', 'builder')
        notices = sorted(os.listdir(storagePath))
        self.failUnlessEqual(notices, ['1', '2', '3', '4', '5'])
        # Test one of the notices
        npath = os.path.join(storagePath, '5', 'content')
        contents = file(npath).read()
        contents = re.sub('Created On:&lt;/b&gt; .*</desc',
            'Created On:&lt;/b&gt; @CREATED-ON@</desc', contents)
        contents = re.sub('<date>.*</date>',
            '<date>@DATE@</date>', contents)
        self.failUnlessEqual(contents, """\
<item><title>Image `Test Build' built (Foo version 1.0)</title><description>&lt;b&gt;Appliance Name:&lt;/b&gt; Foo&lt;br/&gt;&lt;b&gt;Appliance Major Version:&lt;/b&gt; 1.0&lt;br/&gt;&lt;b&gt;Image Type:&lt;/b&gt; Stub Image&lt;br/&gt;&lt;b&gt;File Name:&lt;/b&gt; reallybigfile&lt;br/&gt;&lt;b&gt;Download URL:&lt;/b&gt; &lt;a href="http://test.rpath.local/downloadImage?fileId=5"&gt;http://test.rpath.local/downloadImage?fileId=5&lt;/a&gt;&lt;br/&gt;&lt;b&gt;Created On:&lt;/b&gt; @CREATED-ON@</description><date>@DATE@</date><category>success</category><guid>http://test.rpath.local/api/users/owner/notices/contexts/builder/5</guid></item>""")

    def _testSetBuildFilenamesSafe(self, db, data, hidden):
        ownerClient = self.getClient('owner')
        nobodyClient = self.getClient('anonymous')

        if hidden:
            adminClient = self.getClient('admin')
            adminClient.hideProject(data['projectId'])

        build = ownerClient.getBuild(data['buildId'])
        build.setDataValue('outputToken', 'thisisasecretstring',
                           RDT_STRING, False)

        self.assertRaises(PermissionDenied,
            nobodyClient.server._server.setBuildFilenamesSafe, build.id,
            'thisisthewrongsecret', [['foo', 'bar']])

        nobodyClient.setBuildFilenamesSafe(build.id,
            'thisisasecretstring', [['foo', 'bar', 10, 'abcd']])

        build.refresh()
        self.failUnlessEqual(build.getFiles(),
            [{'sha1': 'abcd', 'idx': 0, 'title': 'bar',
              'fileUrls': [(5, 0, self.cfg.imagesPath + '/foo/1/foo')],
              'fileId': 5, 'size': 10,
              'downloadUrl': 'http://test.rpath.local/downloadImage?fileId=5'}]
        )

        # make sure the outputTokengets removed from the build data
        self.failUnlessEqual(build.getDataValue('outputToken', validate = False), 0)

    @fixtures.fixture('Full')
    def testSetBuildFilenamesSafe(self, db, data):
        return self._testSetBuildFilenamesSafe(db, data, hidden = False)

    @fixtures.fixture('Full')
    def testSetBuildFilenamesSafeHidden(self, db, data):
        return self._testSetBuildFilenamesSafe(db, data, hidden = True)

    def _testSetBuildAMIDataSafe(self, db, data, hidden):
        ownerClient = self.getClient('owner')
        nobodyClient = self.getClient('anonymous')

        if hidden:
            adminClient = self.getClient('admin')
            adminClient.hideProject(data['projectId'])

        build = ownerClient.getBuild(data['buildId'])
        build.setDataValue('outputToken', 'thisisasecretstring',
                           RDT_STRING, False)

        self.assertRaises(PermissionDenied,
            nobodyClient.server._server.setBuildAMIDataSafe, build.id,
            'thisisthewrongsecret', 'bogusAMIId', 'bogusManifestName')

        nobodyClient.setBuildAMIDataSafe(build.id,
            'thisisasecretstring', 'bogusAMIId', 'bogusManifestName')

        build.refresh()

        self.failUnlessEqual(build.getDataDict(),
                {'amiId': 'bogusAMIId',
                    'enumArg': '2',
                    'boolArg': False,
                    'amiManifestName,': 'bogusManifestName',
                    'stringArg': '', 'intArg': 0})

        # make sure the outputTokengets removed from the build data
        self.failUnlessEqual(build.getDataValue('outputToken', validate = False), 0)

    @fixtures.fixture('Full')
    def testSetBuildAMIDataSafe(self, db, data):
        return self._testSetBuildAMIDataSafe(db, data, hidden = False)

    @fixtures.fixture('Full')
    def testSetBuildAMIDataSafeHidden(self, db, data):
        return self._testSetBuildAMIDataSafe(db, data, hidden = True)

    @fixtures.fixture('Full')
    def testGetEmptyFilenames(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        cu = db.cursor()

        cu.execute('DELETE FROM BuildFiles')
        db.commit()
        assert build.getFiles() == []

    @fixtures.fixture('Full')
    def testBuildArchFlavor(self, db, data):
        client = self.getClient('owner')

        build = client.getBuild(data['buildId'])
        assert(str(build.getArchFlavor()) == "is: x86_64")

        build = client.getBuild(data['anotherBuildId'])
        assert(str(build.getArchFlavor()) == "is: x86")

    @fixtures.fixture('Full')
    def testAddS3URLs(self, db, data):
        client = self.getClient('admin')

        build = client.getBuild(data['pubReleaseFinalId'])
        buildfiles = build.getFiles()
        assert(len(buildfiles) == 1)

        fileId = buildfiles[0]['fileId']
        build.addFileUrl(fileId, urltypes.AMAZONS3, 'http://a.test.url/')
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT, 'http://a.test.url/?torrent')

        newbuildfiles = build.getFiles()
        assert(len(newbuildfiles) == 1)
        fileUrls = newbuildfiles[0]['fileUrls']
        self.failUnlessEqual(len(fileUrls), 3)
        self.failUnlessEqual(fileUrls,
                [(2, urltypes.LOCAL, 'file'),
                 (5, urltypes.AMAZONS3, 'http://a.test.url/'),
                 (6, urltypes.AMAZONS3TORRENT, 'http://a.test.url/?torrent')])


    @fixtures.fixture('Full')
    def testRemoveS3URLs(self, db, data):
        client = self.getClient('admin')

        build = client.getBuild(data['pubReleaseFinalId'])
        buildfiles = build.getFiles()
        assert(len(buildfiles) == 1)

        fileId = buildfiles[0]['fileId']
        build.addFileUrl(fileId, urltypes.AMAZONS3, 'http://a.test.url/')
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT, 'http://a.test.url/?torrent')

        newbuildfiles = build.getFiles()
        assert(len(newbuildfiles) == 1)

        fileUrls = newbuildfiles[0]['fileUrls']
        assert(len(fileUrls) == 3)
        urlIdsToRemove = [ x[0] for x in fileUrls if x[1] != urltypes.LOCAL ]
        for urlId in urlIdsToRemove:
            build.removeFileUrl(fileId, urlId)

        newbuildfiles = build.getFiles()
        fileUrls = newbuildfiles[0]['fileUrls']
        self.failUnlessEqual(len(fileUrls), 1)
        self.failUnlessEqual(fileUrls, [(2, urltypes.LOCAL, 'file')])

    @fixtures.fixture('Full')
    def testDownloadTracking(self, db, data):
        client = self.getClient('admin')

        build = client.getBuild(data['pubReleaseFinalId'])
        buildFiles = build.getFiles()

        urlId = buildFiles[0]['fileUrls'][0][0]
        client.server._server.addDownloadHit(urlId, '1.2.3.4')

        cu = db.cursor()
        cu.execute("SELECT urlId FROM UrlDownloads WHERE urlId=?", urlId)
        self.failUnlessEqual(cu.fetchone()[0], urlId)

    @testsuite.context('unfriendly')
    @fixtures.fixture('Empty')
    def testSetBuildFilenames(self, db, data):
        client = self.getClient('admin')
        client = self.getClient('admin')

        hostname = "foo"
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        project = client.getProject(projectId)

        build = client.newBuild(projectId, "Test Build")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1", "1#x86")
        build.setBuildType(buildtypes.STUB_IMAGE)

        build.setFiles([["file", "file title 1"]])
        files = build.getFiles()
        self.failUnlessEqual(len(files), 1)
        self.failUnlessEqual(files[0]['title'], "file title 1")
        self.failUnlessEqual(files[0]['sha1'], "")
        self.failUnlessEqual(files[0]['size'], 0)
        self.failUnlessEqual(files[0]['fileUrls'][0][1], urltypes.LOCAL)
        self.failUnlessEqual(files[0]['fileUrls'][0][2], "file")

        build.setFiles([["file", "file title 1", 100000, ''],
                        ["hyoogefile", "big!", 1024*1024*5000,
                            '0123456789012345678901234567890123456789']])
        files = build.getFiles()
        self.failUnlessEqual(files[0]['title'], "file title 1")
        self.failUnlessEqual(files[0]['sha1'], '')
        self.failUnlessEqual(files[0]['size'], 100000)
        self.failUnlessEqual(files[0]['fileUrls'][0][1], urltypes.LOCAL)
        self.failUnless(files[0]['fileUrls'][0][2],
            os.path.join(self.cfg.imagesPath, "foo", "1", "file"))

        self.failUnlessEqual(files[1]['title'], "big!")
        self.failUnlessEqual(files[1]['sha1'], '0123456789012345678901234567890123456789')
        self.failUnlessEqual(files[1]['size'], 1024*1024*5000)
        self.failUnlessEqual(files[1]['fileUrls'][0][1], urltypes.LOCAL)
        self.failUnlessEqual(files[1]['fileUrls'][0][2], "hyoogefile")
        self.failUnlessEqual(len(files), 2)

        build.setFiles([])
        files = build.getFiles()
        self.failUnlessEqual(len(files), 0)

    @fixtures.fixture('Full')
    def testSerializeBuild(self, db, data):
        client = self.getClient('admin')

        util.mkdirChain(self.cfg.dataPath + "/entitlements")
        f = open(self.cfg.dataPath + "/entitlements/server.com", "w")
        f.write(conarycfg.emitEntitlement('server.com', 'class', 'key'))
        f.close()

        self.cfg.configLine( 'proxy http://proxy.example.com/proxy')
        build = client.getBuild(data['pubReleaseFinalId'])

        serialized = build.serialize()

        buildDict = simplejson.loads(serialized)

        self.failIf(buildDict['protocolVersion'] != 1,
                    "Serial Version 1 was not honored")

        self.failUnlessEqual(set(str(x) for x in buildDict.keys()),
            set(str(x) for x in ['UUID', 'buildType', 'data', 'description', 'name', 'outputToken',
             'project', 'protocolVersion', 'proxy', 'troveFlavor', 'troveName', 'outputUrl',
             'troveVersion', 'type', 'buildId', 'outputUrl', 'proddefLabel']))

        self.failUnlessEqual(set(buildDict['project']), set(['hostname', 'name', 'label', 'conaryCfg']))

        self.assertEquals(buildDict['proxy'], {
                'http': 'http://proxy.example.com/proxy',
                'https': 'https://proxy.example.com/proxy',
            })

    @fixtures.fixture('Full')
    def testBuildCount(self, db, data):
        client = self.getClient('admin')

        build = client.getBuild(data['pubReleaseFinalId'])

        serialized = build.serialize()
        buildDict = simplejson.loads(serialized)
        UUID = str(buildDict['UUID'])

        hname = '%s.%s' % (MINT_HOST, MINT_DOMAIN)
        self.assertEquals(UUID, '%s-build-2-1' % (hname,))

        # repeat the serialize process to ensure the build count gets bumped
        serialized = build.serialize()
        buildDict = simplejson.loads(serialized)
        UUID = str(buildDict['UUID'])

        self.assertEquals(UUID, '%s-build-2-2' % (hname,))

    @fixtures.fixture('Full')
    def testBumpBadBuild(self, db, data):
        client = self.getClient('admin')
        count = client.server._server.builds.bumpBuildCount(99999)
        self.assertEquals(count, None)

    @fixtures.fixture('Full')
    def testSerializeBuildAMI(self, db, data):
        client = self.getClient('admin')
        # create a build for the "foo" project called "Test Build"
        # and add it to an unpublished (not final) release
        build = client.newBuild(data['projectId'], "Test Build")
        build.setTrove("group-dist", "/testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1", "1#x86")
        build.setBuildType(buildtypes.AMI)
        fixtures.stockBuildFlavor(db, build.id, "x86")

        util.mkdirChain(self.cfg.dataPath + "/entitlements")
        f = open(self.cfg.dataPath + "/entitlements/server.com", "w")
        f.write(conarycfg.emitEntitlement('server.com', 'class', 'key'))
        f.close()

        serialized = build.serialize()
        buildDict = simplejson.loads(serialized)

        self.failUnless('amiData' in buildDict.keys())

        amiData = buildDict['amiData']
        self.failUnlessEqual(set(amiData.keys()),
            set(['ec2PublicKey', 'ec2PrivateKey', 'ec2AccountId', 'ec2S3Bucket',
                 'ec2Certificate', 'ec2CertificateKey',
                 'ec2LaunchUsers', 'ec2LaunchGroups']))
        assert(amiData['ec2LaunchUsers'] == [u'000000001111', u'000000002222'])


        client.hideProject(data['projectId'])

        client.setEC2CredentialsForUser(data['user'],
                    '3234', 'accessKey', 'secretKey',
                    force=True)
        build = client.getBuild(build.id)

        serialized = build.serialize()

        buildDict = simplejson.loads(serialized)
        assert(buildDict['amiData']['ec2LaunchUsers'] == ['3234'])

    @fixtures.fixture('Full')
    @testsuite.tests('RBL-2120')
    def testSerializePermissions(self, db, data):
        '''
        Test that all projects to which the user can write are given
        permissions in the serialized conaryrc.
        '''

        adminClient = self.getClient('admin')
        developer = self.getClient('developer')
        projectId = data['projectId']
        buildId = data['buildId']
        build = developer.getBuild(buildId)

        # Create a second project owned by a different user
        nobody = self.getClient('nobody')
        hostname = "bar"
        otherProjectId = nobody.newProject('bar', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0",
                        prodtype="Component", isPrivate=True)
        otherProject = nobody.getProject(otherProjectId)
        FQDN = otherProject.getFQDN()

        buildDict = simplejson.loads(build.serialize())
        self.failIf(FQDN in buildDict['project']['conaryCfg'],
            'Project "bar" should not be in conaryrc')

        # Now add developer to bar and make sure bar appears in their builds
        otherProject.addMemberById(data['developer'], userlevels.DEVELOPER)
        buildDict = simplejson.loads(build.serialize())
        self.failUnless(FQDN in buildDict['project']['conaryCfg'],
            'Project "bar" should be in conaryrc')

    @fixtures.fixture('Full')
    @testsuite.tests('RBL-2827')
    def testMarketingName(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        
        # validate CD
        build.setFiles([["cd_iso", "CD iso file", 734003200, ''],
                        ["dvd_iso", "DVD iso file", 734003201, '']])
        
        # ensure no errors without passing in file
        build.getMarketingName()
        
        # ensure no errors passing in file without size
        fakeBf = {'sha1': '', 'idx': 0, 'title': 'foo', 
                  'fileUrls': [(5, 0, 'cd_iso')], 'fileId': 5}
        build.getMarketingName(fakeBf)
        
        buildFiles = build.getFiles()
        for bf in buildFiles:
            mName = build.getMarketingName(bf)
            if bf['title'] =="CD iso file":
                self.assertTrue('DVD' not in mName)
            elif bf['title'] =="DVD iso file":
                self.assertTrue('CD' not in mName)

    @fixtures.fixture('Full')
    @testsuite.tests('RBL-3209')
    def testGetBaseFileName(self, db, data):
        client = self.getClient(data.get('owner'))
        buildId = data.get('buildId')
        build = client.getBuild(buildId)
        self.assertEquals(build.getBaseFileName(), 'foo-1.1-x86_64')
        cu = db.cursor()

        # now set this value to something else
        cu.execute("INSERT INTO BuildData VALUES(?,?,?,?)",
               buildId, 'baseFileName', 'foo-bar', RDT_STRING)
        db.commit()
        self.assertEquals(build.getBaseFileName(), 'foo-bar')

    @fixtures.fixture('Full')
    @testsuite.tests('RBL-3209')
    def testGetBuildPageUrl(self, db, data):
        client = self.getClient(data.get('owner'))
        buildId = data.get('buildId')
        build = client.getBuild(buildId)
        self.assertEquals(build.getBuildPageUrl(),
                'http://test.rpath.local/project/foo/build?id=1')
        cu = db.cursor()
        cu.execute("UPDATE Projects SET hostname='bar' WHERE projectId=?",
                data.get('projectId'))
        db.commit()
        self.assertEquals(build.getBuildPageUrl(),
                'http://test.rpath.local/project/bar/build?id=1')

class ProductVersionBuildTest(fixtures.FixturedProductVersionTest):

    def setUp(self):
        fixtures.FixturedProductVersionTest.setUp(self)
        self.setUpProductDefinition()

        # This product definition is based on the "Full" fixture
        pd = helperfuncs.sanitizeProductDefinition('The Foo Project',
                'The foo project is TEH AWESOME',
                'foo', MINT_PROJECT_DOMAIN, 'foo', 'FooV1',
                'Version one is not vaporware',
                'ns')
#        pd.setBaseFlavor("~MySQL-python.threadsafe, ~X, ~!alternatives, !bootstrap, ~builddocs, ~buildtests, !cross, ~desktop, ~!dietlibc, ~!dom0, ~!domU, ~emacs, ~gcj, ~gnome, ~grub.static, ~gtk, ~ipv6, ~kde, ~!kernel.debug, ~kernel.debugdata, ~!kernel.numa, ~kernel.smp, ~krb, ~ldap, ~nptl, ~!openssh.smartcard, ~!openssh.static_libcrypto, pam, ~pcre, ~perl, ~!pie, ~!postfix.mysql, ~python, ~qt, ~readline, ~!sasl, ~!selinux, ~sqlite.threadsafe, ssl, ~tcl, tcpwrappers, ~tk, ~uClibc, !vmware, ~!xen, ~!xfce, ~!xorg-x11.xprint")
        pd.setImageGroup('group-dist')
        # getInitialProductDefinition currently adds stages, but
        # this may change in the future; we'll add "Booya" here.
        pd.addStage('Booya', '-booya')
        pd.addStage('Elsewhere', '-nada')
        pd.addStage('Custom', '-sodapopinski')
        pd.addStage('NoImages', '-noimages')
        stageNames = [x.name for x in pd.getStages() \
                if x.name not in ('Booya', 'Elsewhere', 'Custom', 'NoImages')]

        pd.addSearchPath('group-rap-standard',
                'rap.rpath.com@rpath:linux-1')
        pd.addSearchPath('group-postgres',
                    'products.rpath.com@rpath:postgres-8.2')

        pd.addFlavorSet('superfunk', 'Superfunk', '~superfunk.bootsy')

        pd.addContainerTemplate(pd.imageType('installableIsoImage',
            {'showMediaCheck' : True}))
        pd.addContainerTemplate(pd.imageType('vmwareImage'))
        pd.addContainerTemplate(pd.imageType('xenOvaImage'))
        pd.addBuildDefinition(name='ISO 32',
                              flavorSetRef = 'generic',
                              architectureRef = 'x86',
                              containerTemplateRef = 'installableIsoImage',
                              stages=stageNames,
                              imageGroup='group-dist')

        pd.addBuildDefinition(name='ISO 64',
                              flavorSetRef = 'generic',
                              architectureRef = 'x86_64',
                              containerTemplateRef = 'installableIsoImage',
                              stages=stageNames)
        pd.addBuildDefinition(name='VMWare 64',
                              flavorSetRef = 'vmware',
                              architectureRef = 'x86_64',
                              containerTemplateRef = 'vmwareImage',
                              stages=stageNames)
        pd.addBuildDefinition(name='AMI 64',
                              flavorSetRef = 'ami',
                              architectureRef = 'x86_64',
                              containerTemplateRef = 'xenOvaImage',
                              stages=stageNames)
        pd.addBuildDefinition(name='ISO 64 II',
                              flavorSetRef = 'superfunk',
                              architectureRef = 'x86_64',
                              containerTemplateRef = 'installableIsoImage',
                              image=pd.imageType(None, {'betaNag': True}),
                              stages=['Booya'],
                              imageGroup='group-other')
        pd.addBuildDefinition(name='Cannot be built',
                              flavorSetRef = 'generic',
                              architectureRef = 'x86',
                              containerTemplateRef = 'installableIsoImage',
                              stages=['Elsewhere'],
                              imageGroup='group-fgsfds')
        pd.addBuildDefinition(name='...but this can',
                              flavorSetRef = 'generic',
                              architectureRef = 'x86',
                              containerTemplateRef = 'installableIsoImage',
                              stages=['Elsewhere'],
                              imageGroup='group-dist')
        pd.addBuildDefinition(name='me custom',
                              flavorSetRef = 'generic',
                              architectureRef = 'x86',
                              containerTemplateRef = 'installableIsoImage',
                              image=pd.imageType(None,
                                  {'anacondaCustomTrove':\
                                   '/conary.rpath.com@rpl:devel/0.0:1.0-1-1',
                                   'anacondaTemplatesTrove':\
                                   '/conary.rpath.com@rpl:devel/0.0:1.0-1-2',
                                   'mediaTemplateTrove':\
                                   '/conary.rpath.com@rpl:devel/0.0:1.0-1-3'}),
                              stages=['Custom'],
                              imageGroup='group-dist')

        # mocked out call to save to memory
        pd.saveToRepository()

        # Mock out call to getRepos so we can properly test builds
        def getRepos(self):
            class Repo:
                def findTrove(self, t1, t2, *args, **kwargs):
                    tn, tv, tf = t2
                    flava_flavs = []
                    if tn == 'group-dist':
                        flava_flavs = [ \
                                'dietlibc,!dom0,!domU,grub.static,!vmware,!xen is: x86(~i486,~i586,~i686,~sse,~sse2)',
                                '!dietlibc,!dom0,!domU,!grub.static,!vmware,!xen is: x86(~i486,~i586,~i686,~sse,~sse2) x86_64',
                                '!dietlibc,!dom0,!domU,!grub.static,vmware,!xen is: x86(~i486,~i586,~i686,~sse,~sse2) x86_64',
                                '!dietlibc,!dom0,domU,!grub.static,!vmware,xen is: x86(~i486,~i586,~i686,~sse,~sse2) x86_64',
                        ]
                    elif tn == 'group-other':
                        flava_flavs = [ '~superfunk.bootsy is: x86(~i486,~i586,~i686,~sse,~sse2) x86_64', ]
                    elif tn in ['anaconda-custom', 'anaconda-templates', 'media-template']:
                        return [(tn,
                             versions.VersionFromString(tv),
                                deps.parseFlavor('is: x86_64'))]
                    else:
                        return []

                    try:
                        versions.Label(tv)
                        tv = versions._VersionFromString(
                                            '/%s/12345.6:1-1-1' % tv,
                                            frozen=True)
                    except errors.ParseError:
                        tv = versions.VersionFromString(tv)
                    return [(tn, tv,
                             deps.parseFlavor(f)) \
                                     for f in flava_flavs]
                def findTroves(self, t1, t2, *args, **kwargs):
                    res = dict([(x, self.findTrove(t1, x, *args, **kwargs)) \
                            for x in t2])
                    if not res:
                        return {}
                    return res
            return Repo()

        self.oldGetRepos = conaryclient.ConaryClient.getRepos
        conaryclient.ConaryClient.getRepos = getRepos

    def tearDown(self):
        fixtures.FixturedProductVersionTest.tearDown(self)

        # Restore conary client calls that were mocked
        conaryclient.ConaryClient.getRepos = self.oldGetRepos

    @fixtures.fixture('Full')
    def testBuildsFromProductDefinition(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]

        versionId = data['versionId']
        client = self.getClient('admin')
        buildIds = \
            client.newBuildsFromProductDefinition(versionId, 'Development', 
                                                  False)
        # Should have created 4 builds for Development stage
        self.assertEquals(4, len(buildIds))

        bld = client.getBuild(buildIds[0])
        self.failUnless(bld.createdBy,
                'createdBy was not set (RBL-3076)')

        buildIds = \
            client.newBuildsFromProductDefinition(versionId, 'Booya', False)
        # Should have created 1 build for Booya stage
        self.assertEquals(1, len(buildIds))
        build = client.getBuild(buildIds[0])
        self.assertEquals(build.getDataDict().get('showMediaCheck'), True)

        data = simplejson.loads(client.server.serializeBuild(buildIds[0]))
        self.assertEquals(data['proddefLabel'], 'foo.rpath.local2@ns:foo-FooV1')

    @fixtures.fixture('Full')
    def testBuildsFromProductDefinitionFilteredByBuildName(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]

        versionId = data['versionId']
        client = self.getClient('admin')
        reqBuildNames = ['ISO 32', 'ISO 64']
        buildIds = \
            client.newBuildsFromProductDefinition(versionId, 'Development',
                                                  False, reqBuildNames)
        # Should have created 2 builds for Development stage
        self.assertEquals(2, len(buildIds))

        builds = [ client.getBuild(x) for x in buildIds ]
        buildNames = set(x.name for x in builds)
        self.failUnlessEqual(buildNames, set(reqBuildNames))

    @fixtures.fixture('Full')
    def testBuildsFromProductDefinitionFilteredByVersionSpec(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]

        versionId = data['versionId']
        client = self.getClient('admin')
        reqBuildNames = ['ISO 32']
        buildIds = \
            client.newBuildsFromProductDefinition(versionId, 'Development',
                                                  False, reqBuildNames,
                  '/foo.rpath.local2@ns:foo-fooV1-devel/2-1-1')
        # Should have created 2 builds for Development stage
        self.assertEquals(1, len(buildIds))

        builds = [ client.getBuild(x) for x in buildIds ]
        buildNames = set(x.name for x in builds)
        self.failUnlessEqual(buildNames, set(reqBuildNames))
        assert(builds[0].troveVersion == '/foo.rpath.local2@ns:foo-fooV1-devel/0.000:2-1-1')

    @fixtures.fixture('Full')
    @testsuite.tests('RBL-2924')
    def testBuildsFromProductDefinitionBoolVal(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]

        versionId = data['versionId']
        client = self.getClient('admin')
        server = client.server._server

        # get our booya build
        buildIds = client.newBuildsFromProductDefinition(versionId, 'Booya',
                                                         False)
        self.assertEquals(1, len(buildIds))

        isSet, betaNag = server.getBuildDataValue(buildIds[0], "betaNag")
        self.assertTrue(isSet)
        self.assertTrue(betaNag)
        
    @fixtures.fixture('Full')
    def testBuildsFromProductDefinitionCustom(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]

        versionId = data['versionId']
        client = self.getClient('admin')
        server = client.server._server
        
        # get custom builds
        buildIds = \
            client.newBuildsFromProductDefinition(versionId, 'Custom', False)
            
        # Should have created 1 build for Custom stage
        self.assertEquals(1, len(buildIds))
        
        # validate anaconda-custom
        aCustom = server.getBuildDataValue(buildIds[0], "anaconda-custom")
        self.assertTrue(aCustom == (True, \
            'anaconda-custom=/conary.rpath.com@rpl:devel/1.0-1-1[is: x86_64]'))
        
        # validate anaconda-template
        aTemplate = server.getBuildDataValue(buildIds[0], "anaconda-templates")
        self.assertTrue(aTemplate == (True, \
            'anaconda-templates=/conary.rpath.com@rpl:devel/1.0-1-2[is: x86_64]'))
        
        # validate media-template
        mTemplate = server.getBuildDataValue(buildIds[0], "media-template")
        self.assertTrue(mTemplate == (True, \
            'media-template=/conary.rpath.com@rpl:devel/1.0-1-3[is: x86_64]'))

    @fixtures.fixture('Full')
    def testBuildsFromProductDefinitionBadStage(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]

        versionId = data['versionId']
        client = self.getClient('admin')
        self.assertRaises(ProductDefinitionInvalidStage,
            client.newBuildsFromProductDefinition, versionId, 'fgsfds', False)

    @fixtures.fixture('Full')
    def testValidateBuildDefinitionTaskList(self, db, data):
        raise testsuite.SkipTestException("skip testValidateBuildDefinitionTaskList...it duplicates the testing on this code anyway")

        def validateTaskList(self, versionId, stageName, goldTaskList):
            """
            Get a task list by versionId and stage name and validate it
            """
            tl = client.getBuildTaskListForDisplay(versionId, stageName)
            # the names of the flavors changed. when I found this test
            # things were being listed as Custom Flavor vs something sensical
            self.assertTrue(tl == goldTaskList)
            return True

        versionId = data['versionId']
        client = self.getClient('admin')

        # golden data for development stage task list
        goldTaskListDevel = [
            {'buildName'      : u'ISO 32', 
             'buildFlavorName': 'Generic x86 (32-bit)',
             'buildTypeName'  : buildtypes.typeNamesMarketing[\
                                buildtypes.INSTALLABLE_ISO],
             'imageGroup'     : u'group-dist=foo.%s@ns:foo-fooV1-devel' % MINT_PROJECT_DOMAIN
            }, 
            {'buildName'      : u'ISO 64', 
             'buildFlavorName': 'Generic x86 (64-bit)',
             'buildTypeName'  : buildtypes.typeNamesMarketing[\
                                buildtypes.INSTALLABLE_ISO],
             'imageGroup'     : u'group-dist=foo.%s@ns:foo-fooV1-devel' % MINT_PROJECT_DOMAIN
             },
             {'buildName'     : u'VMWare 64', 
             'buildFlavorName': 'VMware x86 (64-bit)',
             'buildTypeName'  : buildtypes.typeNamesMarketing[\
                                buildtypes.VMWARE_IMAGE],
             'imageGroup'     : u'group-dist=foo.%s@ns:foo-fooV1-devel' % MINT_PROJECT_DOMAIN
             },
             {'buildName'     : u'AMI 64', 
             'buildFlavorName': 'AMI x86 (64-bit)',
             'buildTypeName'  : buildtypes.typeNamesMarketing[\
                                buildtypes.XEN_OVA],
             'imageGroup'     : u'group-dist=foo.%s@ns:foo-fooV1-devel' % MINT_PROJECT_DOMAIN
             }
        ]
        
        # golden data for booya stage task list
        goldTaskListBooya = [
            {'buildName'      : u'ISO 64 II', 
             'buildFlavorName': 'Superfunk x86 (64-bit)',
             'buildTypeName'  : buildtypes.typeNamesMarketing[\
                                buildtypes.INSTALLABLE_ISO],
             'imageGroup'     : u'group-other=foo.%s@ns:foo-fooV1-booya' % MINT_PROJECT_DOMAIN
            }
        ]

        # validate task list for development label
        validateTaskList(self, versionId, 'Development', goldTaskListDevel)

        # validate task list for booya label
        validateTaskList(self, versionId, 'Booya', goldTaskListBooya)

    @fixtures.fixture('Full')
    def testBuildsFromProductDefinitionNoTrove(self, db, data):
        # Surprisingly, setUp runs before fixtureFull; we need to get rid of
        # the persisted xml data from fixtureFull
        del self._MockProductDefinition._testxmldata[1:]
        # test an empty result from _resolveTrove
        client = self.getClient('owner')
        # Should raise an exception
        self.assertRaises(ProductDefinitionInvalidStage,
                          client.newBuildsFromProductDefinition,
                          data['versionId'],
                          'HissBoo', False)
        # Should raise an exception
        self.assertRaises(NoBuildsDefinedInBuildDefinition,
                          client.newBuildsFromProductDefinition,
                          data['versionId'],
                          'NoImages', False)
        # Should raise an exception
        self.assertRaises(TroveNotFoundForBuildDefinition,
                          client.newBuildsFromProductDefinition,
                          data['versionId'],
                          'Elsewhere', False)
        # Let's FORCE IT
        buildIds = \
            client.newBuildsFromProductDefinition(data['versionId'],
                'Elsewhere', True)
        # Should have created 1 build for Elsewhere stage
        self.assertEquals(1, len(buildIds))


class BuildTestConaryRepository(MintRepositoryHelper):
    def testBuildTrovesResolution(self):
        raise testsuite.SkipTestException("This test is breaking when surrounded by other startMintServer(1) calls")
        client, userId = self.quickMintAdmin("testuser", "testpass")

        self.startMintServer(1, serverCache=self.servers)
        repos1 = self.getRepositoryClient(serverIdx=1)

        #create an external project that points to the original project
        self.startMintServer(2, serverName="localhost1", serverCache=self.servers)
        repos2 = self.getRepositoryClient(serverIdx=2)
        extProjectId = client.newExternalProject("External Project 2",
            "external2", MINT_PROJECT_DOMAIN, "localhost1@foo:bar",
            repos2.c.map[0][1], True)

        self.upstreamMap = dict(repos1.c.map)
        def projectConfig(s):
            cfg = conarycfg.ConaryConfiguration(False)
            # This is a hack since all our configured repositories require
            # repository maps.  Inject the "non-mirrored" repository map
            cfg.repositoryMap.update(self.upstreamMap)
            return cfg

        self.mock(projects.Project, 'getConaryConfig', projectConfig)

        #Create a project
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        self.addComponent("anaconda-templates:runtime", "/localhost1@foo:bar/1.0", "is: x86", repos=repos2)
        a = self.addCollection("anaconda-templates", "/localhost1@foo:bar/1.0", [(":runtime", "/localhost1@foo:bar/1.0")], defaultFlavor="is: x86", repos=repos2)

        self.addComponent("anaconda-templates:runtime", "/localhost1@foo:bar/1.1", "is: x86", repos=repos1)
        b = self.addCollection("anaconda-templates", "/localhost1@foo:bar/1.1", [(":runtime", "/localhost1@foo:bar/1.1")], defaultFlavor="is: x86", repos=repos1)

        #make sure they got set up properly
        self.assertEquals('1.1-1-1', str(repos1.findTrove(b.getVersion().trailingLabel(), (b.getName(), None, b.getFlavor()))[0][1].trailingRevision()))
        self.assertRaises(TroveNotFound, repos1.findTrove, a.getVersion().trailingLabel(),
            (a.getName(), a.getVersion(), a.getFlavor()))
        self.assertEquals('1.0-1-1', str(repos2.findTrove(a.getVersion().trailingLabel(), (a.getName(), None, a.getFlavor()))[0][1].trailingRevision()))
        self.assertRaises(TroveNotFound, repos2.findTrove, b.getVersion().trailingLabel(),
            (b.getName(), b.getVersion(), b.getFlavor()))

        x = project.resolveExtraTrove("anaconda-templates",
                "/testproject.%s@rpl:devel/0.0:1.0-1-1" % MINT_PROJECT_DOMAIN, "1#x86",
                a.getVersion().freeze(), a.getFlavor().freeze())
        self.failUnlessEqual(x, "anaconda-templates=/localhost1@foo:bar/1.0-1-1[is: x86]")

    def testBuildTroves(self):
        client, userid = self.quickMintUser("test", "testpass")

        projectId = self.newProject(client)
        project = client.getProject(projectId)

        self.addComponent("anaconda-templates:runtime", "1.0")
        self.addCollection("anaconda-templates", "1.0", [(":runtime", "1.0")])

        x = project.resolveExtraTrove("anaconda-templates",
                "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86",
                "testproject.%s@rpl:devel" % MINT_PROJECT_DOMAIN)
        self.failUnlessEqual(x, "anaconda-templates=/testproject.%s@rpl:devel/1.0-1-1[]" % MINT_PROJECT_DOMAIN)
        
    @testsuite.tests('RBL-2881')
    def testBuildTroves2(self):
        client, userid = self.quickMintUser("test", "testpass")

        projectId = self.newProject(client)
        project = client.getProject(projectId)

        self.addComponent("anaconda-templates:runtime", "1.0")
        self.addCollection("anaconda-templates", "1.0", [(":runtime", "1.0")])
        
        # ensure special trove flavor of None is handled properly
        x = project.resolveExtraTrove("anaconda-templates",
                "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86",
                "testproject.%s@rpl:devel" % MINT_PROJECT_DOMAIN, 
                None)
        self.failUnlessEqual(x, "anaconda-templates=/testproject.%s@rpl:devel/1.0-1-1[]" % MINT_PROJECT_DOMAIN)
        
        # ensure special trove version of None is handled properly
        x = project.resolveExtraTrove("anaconda-templates",
                "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86",
                None, '')
        self.assertTrue("anaconda-templates=/conary.rpath.com@rpl:devel" in x)

    @testsuite.tests('RBL-2879')
    def testResolveTrove(self):
        client, userid = self.quickMintUser("test", "testpass")
        group = "group-moar-appliance"
 
        projectId = self.newProject(client)
        project = client.getProject(projectId)
        group = "group-moar-appliance"

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0",
            [(":runtime", "1.0", deps.Flavor())])
        
        def addTrove(flavor, version='1.0'):
            self.addCollection(group, version,
                [("test", "1.0" , deps.Flavor())], flavor=flavor)

        # Older groups that show up due to their different flavors
        addTrove('!foo,!bar,!baz,!bork,~!xen,~!domU,~!dom0,vmware is: x86',
            version='0.9')
        addTrove('!foo,!bar,!baz,!bork,~!xen,~!domU,~!dom0,vmware is: x86 x86_64',
            version='0.9')

        # New groups that are worth looking at
        addTrove('!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,~!vmware is: x86')
        addTrove('!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,~!vmware is: x86 x86_64')
        addTrove('!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,vmware is: x86')
        addTrove('!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,vmware is: x86 x86_64')

        # Selection of flavors to look for. Tuple of (filter, expected).
        flavors = [
            (('~!xen,~!domU,~!dom0,~!vmware', 'is: x86'),
                '!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,~!vmware is: x86'),
            (('~!vmware', 'is: x86 x86_64'),
                '!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,~!vmware is: x86 x86_64'),
            (('vmware', 'is: x86'),
                '!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,vmware is: x86'),
            (('vmware', 'is: x86_64'),
                '!foo,!bar,baz,bork,~!xen,~!domU,~!dom0,vmware is: x86 x86_64'),
            ]

        repos = self.openRepository()
        groupList = repos.findTrove(self.cfg.buildLabel, (group, None, None))

        # make sure our stock flavors are filtered properly.  i.e. we should
        # get 1 match per flavor even though there are custom flavors.
        server = client.server._server
        for (flavorSet, architecture), expected in flavors:
            expected = deps.parseFlavor(expected)
            flavorSet = deps.parseFlavor(flavorSet)
            architecture = deps.parseFlavor(architecture)
            troves = server._resolveTrove(groupList, flavorSet, architecture,
                    deps.parseFlavor(''))
            self.failUnlessEqual(troves[0], (group, versions.VersionFromString(
                '/testproject.%s@rpl:devel/1.0-1-1' % MINT_PROJECT_DOMAIN),
                expected))

    @testsuite.tests('RBL-2879', 'RBL-3787')
    def testResolveTrove2(self):
        # test a prefersnot satisfying a requires
        client, userid = self.quickMintUser("test", "testpass")
        server = client.server._server

        ver = versions.VersionFromString('/test.rpath.local@rpl:devel/1-1-1')
        def makeTroveSpec(flv):
            return ('group-splat', ver, deps.parseFlavor(flv))
        groupList = [makeTroveSpec('~!vmware is: x86'),
                     makeTroveSpec('!vmware is: x86')]

        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86(i486,i586,i686,sse,sse2)')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves, [])

        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2], deps.parseFlavor('~!vmware is: x86'))

    @testsuite.tests('RBL-2879', 'RBL-3787')
    def testResolveTrove3(self):
        # test arches
        client, userid = self.quickMintUser("test", "testpass")
        server = client.server._server

        ver = versions.VersionFromString('/test.rpath.local@rpl:devel/1-1-1')
        def makeTroveSpec(flv):
            return ('group-splat', ver, deps.parseFlavor(flv))
        groupList = [makeTroveSpec('vmware is: x86'),
                     makeTroveSpec('vmware is: x86_64'),
                     makeTroveSpec('vmware is: x86 x86_64')]

        # look for an x86 trove
        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86(i486,i586,i686,sse,sse2)')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves, [])

        # look for a bi-arch trove
        architecture = deps.parseFlavor(\
                'is: x86 x86_64')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2],
                deps.parseFlavor('vmware is: x86 x86_64'))

        architecture = deps.parseFlavor('is: x86_64')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2], deps.parseFlavor('vmware is: x86_64'))

    @testsuite.tests('RBL-2879', 'RBL-3787')
    def testResolveTrove4(self):
        # test arches with extra flags
        client, userid = self.quickMintUser("test", "testpass")
        server = client.server._server

        ver = versions.VersionFromString('/test.rpath.local@rpl:devel/1-1-1')
        def makeTroveSpec(flv):
            return ('group-splat', ver, deps.parseFlavor(flv))
        groupList = [makeTroveSpec('vmware is: x86(i486,i586,i686,sse,sse2)'),
                     makeTroveSpec('vmware is: x86_64'),
                     makeTroveSpec('vmware is: x86(i486,i586,i686,sse,sse2) x86_64')]

        # look for an x86 trove
        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86(i486,i586,i686,sse,sse2)')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2], deps.parseFlavor('vmware is: x86(i486,i586,i686,sse,sse2)'))

        # look for an x86 trove again
        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2], deps.parseFlavor('vmware is: x86(i486,i586,i686,sse,sse2)'))

        # look for a bi-arch trove
        architecture = deps.parseFlavor(\
                'is: x86(i486,i586,i686,sse,sse2) x86_64')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2],
                deps.parseFlavor('vmware is: x86(i486,i586,i686,sse,sse2) x86_64'))

        architecture = deps.parseFlavor('is: x86_64')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                deps.parseFlavor(''))
        self.assertEquals(troves[0][2], deps.parseFlavor('vmware is: x86_64'))

    @testsuite.tests('RBL-2879', 'RBL-3787')
    def testResolveTrove5(self):
        # test contradictions between arch and customFlavor
        client, userid = self.quickMintUser("test", "testpass")
        server = client.server._server

        ver = versions.VersionFromString('/test.rpath.local@rpl:devel/1-1-1')
        def makeTroveSpec(flv):
            return ('group-splat', ver, deps.parseFlavor(flv))
        groupList = [makeTroveSpec('vmware is: x86(i486,i586,i686,sse,sse2)'),
                     makeTroveSpec('vmware is: x86_64'),
                     makeTroveSpec('vmware is: x86(i486,i586,i686,sse,sse2) x86_64')]

        # look for an x86 trove
        flavorSet = deps.parseFlavor('vmware')
        customFlavor = deps.parseFlavor('is: x86_64')
        architecture = deps.parseFlavor('is: x86(i486,i586,i686,sse,sse2)')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                customFlavor)
        self.assertEquals(troves[0][2], deps.parseFlavor('vmware is: x86_64'))

        # look for an x86 trove again
        flavorSet = deps.parseFlavor('vmware')
        customFlavor = deps.parseFlavor('is: x86(i486,i586,i686,sse,sse2) x86_64')
        architecture = deps.parseFlavor('is: x86')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                customFlavor)
        self.assertEquals(troves[0][2], deps.parseFlavor('vmware is: x86(i486,i586,i686,sse,sse2) x86_64'))

        # look for a bi-arch trove
        architecture = deps.parseFlavor(\
                'is: x86(i486,i586,i686,sse,sse2) x86_64')
        customFlavor = deps.parseFlavor('is: x86')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                customFlavor)
        self.assertEquals(troves[0][2],
                deps.parseFlavor('vmware is: x86(i486,i586,i686,sse,sse2)'))

    @testsuite.tests('RBL-2879', 'RBL-3787')
    def testResolveTrove6(self):
        # test contradictions between flavorSet and customFlavor
        client, userid = self.quickMintUser("test", "testpass")
        server = client.server._server

        ver = versions.VersionFromString('/test.rpath.local@rpl:devel/1-1-1')
        def makeTroveSpec(flv):
            return ('group-splat', ver, deps.parseFlavor(flv))
        groupList = [makeTroveSpec('~!vmware is: x86(i486,i586,i686,sse,sse2)'),
                     makeTroveSpec('!vmware is: x86(i486,i586,i686,sse,sse2)')]

        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86(~i486,~i586,~i686,~sse,~sse2)')
        customFlavor = deps.parseFlavor('!vmware')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                customFlavor)
        self.assertEquals(troves[0][2],
                deps.parseFlavor('!vmware is: x86(i486,i586,i686,sse,sse2)'))

        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86')
        customFlavor = deps.parseFlavor('!vmware')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                customFlavor)
        self.assertEquals(troves[0][2],
                deps.parseFlavor('!vmware is: x86(i486,i586,i686,sse,sse2)'))

        flavorSet = deps.parseFlavor('vmware')
        architecture = deps.parseFlavor('is: x86_64')
        customFlavor = deps.parseFlavor('!vmware is: x86')
        troves = server._resolveTrove(groupList, flavorSet, architecture,
                customFlavor)
        self.assertEquals(troves[0][2],
                deps.parseFlavor('!vmware is: x86(i486,i586,i686,sse,sse2)'))

    @testsuite.tests('RBL-3011')
    def testResolveExactExtraTrove(self):
        '''
        Test that, when given an exact NVF anaconda-custom, the group
        flavor is not substituted in and the proper trove is found.
        '''
        client, userid = self.quickMintUser("test", "testpass")
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        # Add a simple trove
        self.addComponent("test:runtime", "1.0")
        coll = self.addCollection("test", "1.0",
            [(":runtime", "1.0", deps.Flavor())])

        # Try to grab the trove via resolveExtraTrove and an exact
        # tuple. The group flavor should not taint the search for the
        # extra trove since the frozen version hints at an exact
        # spec.
        foundSpec = project.resolveExtraTrove(coll.getName(),
                "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86",
                coll.getVersion().freeze(), coll.getFlavor().freeze())
        self.failUnlessEqual(foundSpec, "%s=%s[%s]" % coll.getNameVersionFlavor())

    def testMakeFlavorMap(self):
        from rpath_proddef import api1 as proddef
        prd = proddef.ProductDefinition()

        res = buildtypes.makeFlavorMap(prd)
        self.assertEquals(res, {})

        # test both being degenerate
        prd.platform = proddef.PlatformDefinition()
        res = buildtypes.makeFlavorMap(prd)
        self.assertEquals(res, {})

        prd.addFlavorSet('foo', 'Foo Flavor', '~foo')
        prd.addArchitecture('arch', 'Arch Flavor', 'arch')
        res = buildtypes.makeFlavorMap(prd)
        self.assertEquals(res, {'Foo Flavor Arch Flavor': 'foo,arch'})

        # add platform settings
        prd.platform.addFlavorSet('bar', 'Bar Flavor', '~bar')
        prd.platform.addArchitecture('arch2', 'Arch2 Flavor', 'arch2')
        res = buildtypes.makeFlavorMap(prd)
        self.assertEquals(res, {'Foo Flavor Arch2 Flavor': 'foo,arch2',
                                'Bar Flavor Arch2 Flavor': 'bar,arch2',
                                'Foo Flavor Arch Flavor': 'foo,arch',
                                'Bar Flavor Arch Flavor': 'bar,arch'})


if __name__ == "__main__":
    testsuite.main()
