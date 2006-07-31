#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import time

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import buildtypes, buildtemplates, jsversion
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT
from mint.database import ItemNotFound
from mint.distro import installable_iso
from mint.mint_error import BuildPublished, BuildMissing, BuildEmpty
from mint.builds import BuildDataNameError
from mint.server import deriveBaseFunc, ParameterError

from conary.lib import util
from conary.repository.errors import TroveNotFound

import fixtures

class BuildTest(fixtures.FixturedUnitTest):
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
            [{'fileId': 4, 'filename': 'file1',
              'title': 'File Title 1', 'size': 0,},
             {'fileId': 5, 'filename': 'file2',
              'title': 'File Title 2', 'size': 0,}]
        )

        assert(build.getDefaultName() == 'group-trove=1.0-1-1')

        desc = 'Just some random words'
        build.setDesc(desc)
        build.refresh()
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
    def testMissingBuild(self, db, data):
        client = self.getClient("owner")
        build = client.getBuild(data['buildId'])

        # make a build and delete it, to emulate a race condition
        # from the web UI
        buildId = build.getId()

        self.captureAllOutput(build.deleteBuild)

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

    def testHiddenIsoGen(self):
        raise testsuite.SkipTestException("needs to be reworked or abandoned")
        # set up a dummy isogen cfg to avoid importing from
        # job-server (the job-server code should be put elsewhere someday...)
        from conary.conarycfg import ConfigFile
        class IsoGenCfg(ConfigFile):
            imagesPath = self.tmpDir
            configPath = self.tmpDir
            SSL = False

        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        adminClient, adminId = self.quickMintAdmin("adminuser", "adminpass")
        adminClient.hideProject(projectId)

        build = client.newBuild(projectId, 'build 1')
        build.setBuildType(buildtypes.INSTALLABLE_ISO)
        build.setTrove("group-core",
                         "/testproject." + MINT_PROJECT_DOMAIN + \
                                 "@rpl:devel/0.0:1.0-1-1",
                         "1#x86")

        self.stockBuildFlavor(build.getId())

        job = client.startImageJob(build.id)

        cfg = self.makeInstallableIsoCfg()
        imageJob = installable_iso.InstallableIso(client, IsoGenCfg(), job,
                                                  build, project)
        imageJob.isocfg = cfg

        # getting a trove not found from a trove that's really not there isn't
        # terribly exciting. historically this call generated a Permission
        # Denied exception for hidden projects, triggered by the great
        # repoMap/user split.
        cwd = os.getcwd()
        os.chdir(self.tmpDir + "/images")

        # unforutanatel imageJob.write call can be noisy on stderr
        oldFd = os.dup(sys.stderr.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.close(fd)

        try:
            self.assertRaises(TroveNotFound, imageJob.write)
        finally:
            os.dup2(oldFd, sys.stderr.fileno())
            os.close(oldFd)
            os.chdir(cwd)


if __name__ == "__main__":
    testsuite.main()
