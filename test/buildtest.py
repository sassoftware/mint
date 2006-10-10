#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import time
import tempfile

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import buildtypes, buildtemplates, jsversion
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT
from mint.database import ItemNotFound
from mint.distro import installable_iso
from mint.mint_error import BuildPublished, BuildMissing, BuildEmpty, \
     PublishedReleaseMissing, PublishedReleasePublished, \
     JobserverVersionMismatch
from mint.builds import BuildDataNameError
from mint.server import deriveBaseFunc, ParameterError
from mint import urltypes

from conary.lib import util
from conary.repository.errors import TroveNotFound

import fixtures

class BuildTest(fixtures.FixturedUnitTest):
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
        assert(build.getFiles() ==\
            [{'size': 0, 'sha1': '', 'title': 'File Title 1',
                'fileUrls': [(4, 0, 'file1')], 'idx': 0, 'fileId': 4},
             {'size': 0, 'sha1': '', 'title': 'File Title 2',
                 'fileUrls': [(5, 0, 'file2')], 'idx': 1, 'fileId': 5}]
        )

        assert(build.getDefaultName() == 'group-trove=1.0-1-1')

        desc = 'Just some random words'
        build.setDesc(desc)
        build.refresh()
        assert(build.timeCreated)
        assert(build.timeUpdated)
        assert desc == build.getDesc()

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
        self.assertRaises(BuildDataNameError,
            build.setDataValue, 'undefinedName', 'test string')
        self.assertRaises(BuildDataNameError,
                          build.getDataValue, 'undefinedName')

        # test bad name with validation override
        build.setDataValue('undefinedName', 'test string',
            dataType = RDT_STRING, validate = False)
        assert('test string' == build.getDataValue('undefinedName'))

        # test bad name with validation override and no data type specified
        self.assertRaises(BuildDataNameError,
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

        if client.server.getBuildStatus(buildId) != {'status': 5,
                                                         'message': 'No Job',
                                                         'queueLen': 0}:
            self.fail("getBuildStatus returned unknown values")

    @fixtures.fixture("Empty")
    def testGetBuildsForProjectOrder(self, db, data):
        # FIXME broken w/r/t new release arch
        client = self.getClient("test")
        projectId = client.newProject("Foo", "foo", "rpath.org")

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

    @fixtures.fixture("Full")
    def testHasVMwareImage(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])

        assert(build.hasVMwareImage() == False)

        build.setFiles([["test.vmware.zip", "Test Image"]])
        assert(build.hasVMwareImage() == True)

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
    def testImageGenerator(self, db, data):
        client = self.getClient('admin')
        build = client.getBuild(data['buildId'])
        project = client.getProject(data['projectId'])
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        build.setDataValue('installLabelPath', 'test.rpath.org@rpl:devel')

        job = client.startImageJob(build.getId())

        from mint.distro import jobserver
        from mint.distro.imagegen import ImageGenerator
        import os
        isocfg = jobserver.IsoGenConfig()
        isocfg.finishedPath = self.cfg.imagesPath
        ig = ImageGenerator(client, isocfg, job, build, project)
        from conary import conaryclient
        cclient = conaryclient.ConaryClient(project.getConaryConfig())
        tmpdir = tempfile.mkdtemp()
        mirrorUrls = {'mirror.rpath.com':'installLabelPath test.rpath.org@rpl:devel\nincludeConfigFile http://mirror.rpath.com/conaryrc\npinTroves kernel.*\nincludeConfigFile /etc/conary/config.d/*\n',
        'https://mirror.rpath.com':'installLabelPath test.rpath.org@rpl:devel\nincludeConfigFile https://mirror.rpath.com/conaryrc\npinTroves kernel.*\nincludeConfigFile /etc/conary/config.d/*\n',
        'https://mirror.rpath.com/testpath':'installLabelPath test.rpath.org@rpl:devel\nincludeConfigFile https://mirror.rpath.com/testpath\npinTroves kernel.*\nincludeConfigFile /etc/conary/config.d/*\n',
        'mirror.rpath.com/testpath':'installLabelPath test.rpath.org@rpl:devel\nincludeConfigFile http://mirror.rpath.com/testpath\npinTroves kernel.*\nincludeConfigFile /etc/conary/config.d/*\n', 
        '':'installLabelPath test.rpath.org@rpl:devel\npinTroves kernel.*\nincludeConfigFile /etc/conary/config.d/*\n'}

        for k, v in mirrorUrls.items():
            build.setDataValue('mirrorUrl', k)
            ig.writeConaryRc(tmpdir, cclient)
            fd = open(os.path.join(tmpdir,  'conaryrc'))
            rcData = fd.read()
            fd.close()
            self.failIf(rcData != v)

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
    def testGetReleaseCompat(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        releaseDict = client.server._server.getRelease(build.id)
        buildDict = client.server._server.getBuild(build.id)
        added = {'releaseId' : build.id, 'imageTypes' : [build.buildType],
                 'downloads': 0, 'timePublished': 0, 'published' : 0}
        removed = ('buildId', 'buildType', 'timeCreated', 'createdBy',
                   'timeUpdated', 'updatedBy', 'pubReleaseId')
        for key, val in releaseDict.iteritems():
            if key in added:
                assert (val == added[key]), "release['%s'] != %s" % \
                       (key, str(added[key]))
            elif key not in removed:
                assert (val == buildDict[key])

    @fixtures.fixture('Full')
    def testReleaseDataCompat(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])
        client.server._server.setReleaseDataValue(build.id, 'foo', 1,
                                                  RDT_STRING)
        assert client.server._server.getReleaseDataValue(build.id, 'foo') == \
               (True, '1')
        d = client.server._server.getReleaseDataDict(build.id)
        assert 'foo' in d

    @fixtures.fixture('Full')
    def testGetRelTroveCompat(self, db, data):
        client = self.getClient('owner')

        # make a legitimate call to set auth values
        client.getBuild(data['buildId'])
        # assert backwards compat function
        self.failIf(client.server._server.getReleaseTrove(data['buildId']) != \
                    client.server._server.getBuildTrove(data['buildId']),
                    "release trove not found. not backwards compatible")

    @fixtures.fixture('Full')
    def testMissingBuildTrove(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])
        build.setTrove('foo', 'bar', 'baz')
        self.assertRaises(BuildMissing, client.server._server.setBuildTrove,
                          99, 'foo', 'ver', 'flav')
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

    @fixtures.fixture('Full')
    def testGetImageTypesCompat(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])
        imageTypes = client.server._server.getImageTypes(build.id)
        self.failIf(imageTypes != [build.getBuildType()],
                    "Compatibility hook failed buildtypes")

    @fixtures.fixture('Full')
    def testMissingGetBuildType(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        self.assertRaises(BuildMissing, client.server._server.getBuildType, 99)

    @fixtures.fixture('Full')
    def testGetAvailBuildTypes(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])
        visibleBuildTypes = self.cfg.visibleBuildTypes
        try:
            for buildTypes in ([], [1, 2, 3]):
                self.cfg.visibleBuildTypes = buildTypes
                assert client.server._server.getAvailableBuildTypes() == \
                       buildTypes
        finally:
            self.cfg.visibleBuildTypes = visibleBuildTypes

    @fixtures.fixture('Full')
    def testGetMissingJSVersion(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        cu = db.cursor()
        cu.execute("DELETE FROM BuildData WHERE name='jsversion'")
        db.commit()

        self.assertRaises(JobserverVersionMismatch, client.startImageJob,
                          build.id)

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
    def testSetImageFilenamesCompat(self, db, data):
        client = self.getClient('owner')
        build = client.getBuild(data['buildId'])

        self.assertRaises(ValueError,
                          client.server._server.setImageFilenames, build.id,
                          [['not right at all']])

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
                 (4, urltypes.AMAZONS3, 'http://a.test.url/'),
                 (5, urltypes.AMAZONS3TORRENT, 'http://a.test.url/?torrent')])


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

    @fixtures.fixture('Empty')
    def testSetBuildFilenames(self, db, data):
        client = self.getClient('admin')
        client = self.getClient('admin')
        
        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)
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
        self.failUnlessEqual(files[0]['fileUrls'][0][2], "file")

        self.failUnlessEqual(files[1]['title'], "big!")
        self.failUnlessEqual(files[1]['sha1'], '0123456789012345678901234567890123456789')
        self.failUnlessEqual(files[1]['size'], 1024*1024*5000)
        self.failUnlessEqual(files[1]['fileUrls'][0][1], urltypes.LOCAL)
        self.failUnlessEqual(files[1]['fileUrls'][0][2], "hyoogefile")
        self.failUnlessEqual(len(files), 2)

        build.setFiles([])
        files = build.getFiles()
        self.failUnlessEqual(len(files), 0)


class OldBuildTest(MintRepositoryHelper):
    def makeInstallableIsoCfg(self):
        mintDir = os.environ['MINT_PATH']
        os.mkdir("%s/changesets" % self.tmpDir)
        util.mkdirChain("%s/templates/x86/PRODUCTNAME" % self.tmpDir)
        util.mkdirChain("%s/templates/x86_64/PRODUCTNAME" % self.tmpDir)

        cfg = installable_iso.IsoConfig()
        cfg.configPath = self.tmpDir
        cfg.scriptPath = mintDir + "/scripts/"
        cfg.cachePath = self.tmpDir + "/changesets/"
        cfg.anacondaImagesPath = "/dev/null"
        cfg.templatePath = self.tmpDir + "/templates/"
        cfg.SSL = False

        cfgFile = open(cfg.configPath + "/installable_iso.conf", 'w')
        cfg.display(cfgFile)
        cfgFile.close()

        return cfg


if __name__ == "__main__":
    testsuite.main()
