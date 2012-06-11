#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import time

from conary import conaryclient
from conary.lib import util

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

import rpath_capsule_indexer
from capsule_indexertest import base

from testutils import mock

class IndexerSetupMixIn(base.IndexerTestMixIn):
    LabelToPlatDefMap = {
    'localhost@rpl:plat' : """\
<platformDefinition>
    <contentProvider name="rhn" description="Red Hat Network">
      <contentSourceType name="RHN"
        description="Red Hat Network Hosted" isSingleton="true" />
      <contentSourceType name="satellite"
        description="Red Hat Network Satellite" />
      <contentSourceType name="proxy"
        description="Red Hat Network Proxy" />
      <dataSource name="rhel-i386-as-4"
        description="Red Hat Enterprise Linux (v. 4 for 32-bit x86)" />
      <dataSource name="rhel-x86_64-as-4"
        description="Red Hat Enterprise Linux (v. 4 for 64-bit x86_64)" />
    </contentProvider>
</platformDefinition>
""",
    'localhost@sles:plat' : """\
<platformDefinition>
    <contentProvider name="novell" description="Novell Update Server">
      <contentSourceType name="nu"
        description="Novell Update Server Hosted" isSingleton="true" />
      <contentSourceType name="SMT"
        description="Subscription Management Tool" />
      <dataSource name="SLES10-SP3-Online/sles-10-i586" description="SuSE Linux Enterprise Server 10 SP3 Online (32-bit x86)"/>
      <dataSource name="SLES10-SP3-Online/sles-10-x86_64" description="SuSE Linux Enterprise Server 10 SP3 Online (64-bit x86_64)"/>
      <dataSource name="SLES10-SP3-Pool/sles-10-i586" description="SuSE Linux Enterprise Server 10 SP3 Pool (32-bit x86)"/>
      <dataSource name="SLES10-SP3-Pool/sles-10-x86_64" description="SuSE Linux Enterprise Server 10 SP3 Pool (64-bit x86_64)"/>
      <dataSource name="SLES10-SP3-Updates/sles-10-i586" description="SuSE Linux Enterprise Server 10 SP3 Updates (32-bit x86)"/>
      <dataSource name="SLES10-SP3-Updates/sles-10-x86_64" description="SuSE Linux Enterprise Server 10 SP3 Updates (64-bit x86_64)"/>
      <dataSource name="SLE10-SDK-SP3-Online/sles-10-i586" description="SuSE Linux Enterprise Server 10 SP3 SDK Online (32-bit x86)"/>
      <dataSource name="SLE10-SDK-SP3-Online/sles-10-x86_64" description="SuSE Linux Enterprise Server 10 SP3 SDK Online (64-bit x86_64)"/>
      <dataSource name="SLE10-SDK-SP3-Pool/sles-10-i586" description="SuSE Linux Enterprise Server 10 SP3 SDK Pool (32-bit x86)"/>
      <dataSource name="SLE10-SDK-SP3-Pool/sles-10-x86_64" description="SuSE Linux Enterprise Server 10 SP3 SDK Pool (64-bit x86_64)"/>
      <dataSource name="SLE10-SDK-SP3-Updates/sles-10-i586" description="SuSE Linux Enterprise Server 10 SP3 SDK Updates (32-bit x86)"/>
      <dataSource name="SLE10-SDK-SP3-Updates/sles-10-x86_64" description="SuSE Linux Enterprise Server 10 SP3 SDK Updates (64-bit x86_64)"/>
    </contentProvider>
</platformDefinition>
""",
    'localhost@centos:plat' : """\
<platformDefinition>
    <contentProvider name="centos" description="Yum Repository">
      <contentSourceType name="repomd"
        description="Yum Repository" isSingleton="false" />
        <dataSource name="5.5/os/i386" description="CentOS (v. 5.5 for 32-bit x86)"/>
        <dataSource name="5.5/os/x86_64" description="CentOS (v. 5.5 for 64-bit x86_64)"/>
        <dataSource name="5.5/updates/i386" description="CentOS (v. 5.5 updates for 32-bit x86)"/>
        <dataSource name="5.5/updates/x86_64" description="CentOS (v. 5.5 updates for 64-bit x86_64)"/>
        <dataSource name="5.4/os/i386" description="CentOS (v. 5.4 for 32-bit x86)"/>
        <dataSource name="5.4/os/x86_64" description="CentOS (v. 5.4 for 64-bit x86_64)"/>
        <dataSource name="5.4/updates/i386" description="CentOS (v. 5.4 updates for 32-bit x86)"/>
        <dataSource name="5.4/updates/x86_64" description="CentOS (v. 5.4 updates for 64-bit x86_64)"/>
    </contentProvider>
</platformDefinition>
""",
}
    LabelToContentSourcesMap = {
        'localhost@rpl:plat' : [ 'RHN', 'proxy', 'satellite' ],
        'localhost@sles:plat' : [ 'nu', 'SMT' ],
        'localhost@centos:plat' : [ 'repomd' ],
    }
    def setUpIndexerCfg(self):
        self.mockPlatformLoadFromRepository()
        db = self.openRestDatabase()
        self.mintCfg.availablePlatforms.append('localhost@centos:plat')
        self.mintCfg.availablePlatforms.append('localhost@sles:plat')
        self._addPlatformSources(db)
        self.capsulecfg = db.capsuleMgr.getIndexerConfig()
        platformCacheFile = os.path.join(self.mintCfg.dataPath, "data",
            "platformName.cache")
        os.unlink(platformCacheFile)

    def mockPlatformLoadFromRepository(self):
        def mockLoadFromRepository(slf, client, label):
            slf.parseStream(self.LabelToPlatDefMap[label])
            slf._sourceTrove = "%s=%s" % (slf._troveName, label)
        from rpath_proddef import api1 as proddef
        self.mock(proddef.PlatformDefinition, 'loadFromRepository',
            mockLoadFromRepository)

    class Source(object):
        name = 'sourceName'
        contentSourceType = 'RHN'
        shortName = 'sourceShortName'
        defaultSource = 1
        orderIndex = 1
        username = 'JeanValjean'
        password = 'SuperSikrit'
        sourceUrl = 'ignoremereally'
        platformLabel = 'localhost@rpl:plat'

    def _getSources(self):
        return [ self.Source() ]

    def _addPlatformSources(self, db):
        # XXX nasty hacks to produce some data in the hopefully proper format
        psql = """
            INSERT INTO Platforms (platformName, label, mode)
            VALUES (?, ?, ?)
        """
        cstsql = """
            INSERT INTO platformsContentSourceTypes
            (platformId, contentSourceType)
            VALUES (?, ?)
        """
        mode = 'manual'
        cu = db.cursor()
        for platformLabel in self.mintCfg.availablePlatforms:
            # XXX this isn't quite right, we set the platform name to be the
            # same as the label. It may need to change
            cu.execute(psql, platformLabel, platformLabel, mode)
            platformId = cu.lastid()

            for contentSourceType in self.LabelToContentSourcesMap[platformLabel]:
                cu.execute(cstsql, platformId, contentSourceType)

            for source in self._getSources():
                if source.platformLabel != platformLabel:
                    continue
                db.platformMgr.createSource(source)
        db.commit()

    def indexer(self):
        indexer = base.IndexerTestMixIn.indexer(self)
        # Populate the indexer
        indexer.refresh()
        return indexer

class BaseCapsulesTest(restbase.BaseRestTest, IndexerSetupMixIn):
    # This controller should mock access from localhost
    class ControllerFactory(restbase.Controller):
        class RequestFactory(restbase.MockRequest):
            def _setProperties(self):
                restbase.MockRequest._setProperties(self)
                self.remote = ('127.0.0.1', 12345)

    class Mock(IndexerSetupMixIn.Mock):
        class Response(IndexerSetupMixIn.Mock.Response):
            def __init__(self, url):
                if 'repodata' not in url:
                    return IndexerSetupMixIn.Mock.Response.__init__(self, url)
                f = file(os.path.join(os.getenv('TEST_PATH'),
                    'mint_test/archive/suse-1/repodata', os.path.basename(url)))
                self.read = f.read

    def setUp(self):
        try:
            restbase.BaseRestTest.setUp(self)
            IndexerSetupMixIn.setUp(self)
        except Exception, e:
            self.tearDown()
            raise

class CapsulesTest(BaseCapsulesTest):
    def testGetContent(self):
        # Make sure we populate the indexer's db
        indexer = self.indexer()
        # We test that we're unquoting the file part too
        uri = 'capsules/rpm/content/with-config-speci%61l-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54'

        client = self.getRestClient()
        req, response = client.call('GET', uri)

        self.failUnlessEqual(response.status, 200)
        self.failUnlessEqual(response.getLength(), 3159)
        self.failUnlessEqual(response.headers['content-type'],
            'application/octet-stream')

        errorUris = [
            'capsules/rpm/content/badcontainername/sha1',
            'capsules/rpm/content/badargcount',
            'capsules/rpm/content/badargcount/sha1/badargcount',
            'capsules/rpm/content/with-config-special-0.2-1.noarch.rpm/badsha1',
            'capsules/rpm/content/with-config-special-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54/nosuchfile/sha1',
            'capsules/rpm/content/with-config-special-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54/%252Fetc%252Fwith-config-special.cfg/badsha1',
        ]
        for uri in errorUris:
            req, response = client.call('GET', uri)
            self.failUnlessEqual(response.status, 404)

        # Fetch file
        uri = 'capsules/rpm/content/with-config-speci%61l-0.2-1.noarch.rpm/4daf5f932e248a32758876a1f8ff12a5f58b1a54/%252Fetc%252Fwith-config-special.cfg/337c9fbf3f208f0856c21301abaa370ccc1d14f7'

        req, response = client.call('GET', uri)
        self.failUnlessEqual(response.status, 200)
        self.failUnlessEqual(response.getLength(), 38)
        self.failUnlessEqual(response.headers['content-type'],
            'application/octet-stream')
        self.failUnlessEqual(''.join(x for x in response.get()),
            'config option\nand another config line\n')

    def testRefresh(self):
        indexer = base.IndexerTestMixIn.indexer(self)
        channelLabel = 'rhel-x86_64-as-4'
        # Make sure we don't have any content in the channels
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(channels, [])
        uri = 'capsules/rpm/content'
        client = self.getRestClient()
        req, response = client.call('POST', uri)
        self.failUnlessEqual(response.status, 204)
        channel = indexer.model.getChannel(channelLabel)
        self.failUnlessEqual(channel.last_modified, '20091020041355')
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(sorted([ x.label for x in channels ]),
            ['rhel-i386-as-4', 'rhel-x86_64-as-4'])

    def testGetPlatformSourceErrors(self):
        client = self.getRestClient(admin = True)
        from mint.rest.db import platformmgr
        mock.mock(platformmgr.Platforms, '_checkMirrorPermissions',
                        True)
        req, response = client.call('GET', '/platforms')

        # Refresh
        uri = 'capsules/rpm/content'
        req, response = client.call('POST', uri)

        indexer = base.IndexerTestMixIn.indexer(self)
        pkgKey = ('with-config-special', None, '0.2', '1', 'noarch')
        pkgSha1 = '4daf5f932e248a32758876a1f8ff12a5f58b1a54'

        pkg = indexer.getPackage(pkgKey, pkgSha1)

        # Mark it as missing
        pkg.path = None

        failures = indexer.model.getPackageDownloadFailures()
        self.failUnlessEqual(len(failures), 0)

        indexer.model.addPackageDownloadFailure(pkg, "manual failure")
        failures = indexer.model.getPackageDownloadFailures()
        self.failUnlessEqual(len(failures), 1)
        timestamp = failures[0].failed_timestamp
        indexer.model.commit()

        uri = '/contentSources/A/instances/B/errors'
        req, errorList = client.call('GET', uri)
        self.failUnlessEqual(
            [ (x.id, x.code, x.message, x.timestamp)
                for x in errorList.resourceError ],
            [ (1, 'DownloadError', 'manual failure', timestamp) ])

        uri = "%s/1" % uri
        req, error = client.call('GET', uri)
        self.failUnlessEqual(error.id, 1)
        self.failUnlessEqual(error.resolved, False)

        # Test failure
        uri2 = uri + '321321'
        req, resp = client.call('GET', uri2)
        self.failUnlessEqual(resp.status, 404)

        # Test resolving it
        xmlData = """\
            <resourceError id="123">
                <resolved>true</resolved>
                <resolvedMessage>No really, it's resolved</resolvedMessage>
            </resourceError>
        """

        req, resp = client.call('PUT', uri, xmlData)
        self.failUnlessEqual(resp.resolved, True)
        self.failUnlessEqual(resp.resolvedMessage, "No really, it's resolved")

        uri = '/contentSources/A/instances/B/errors'
        req, errorList = client.call('GET', uri)
        self.failUnlessEqual(errorList.resourceError, [])

class CapsulesTestRemote(restbase.BaseRestTest):
    # This controller should mock access from non-localhost
    class ControllerFactory(restbase.Controller):
        class RequestFactory(restbase.MockRequest):
            def _setProperties(self):
                restbase.MockRequest._setProperties(self)
                self.remote = ('1.2.3.4', 12345)

    def testAccess(self):
        uri = 'capsules/rpm/content/aaabbb/sha1sum'

        client = self.getRestClient()
        req, response = client.call('GET', uri)

        self.failUnlessEqual(response.status, 404)

        uri = 'capsules/rpm/content'
        req, response = client.call('POST', uri)
        self.failUnlessEqual(response.status, 404)

class CapsuleRepositoryTest(restbase.mint_rephelp.MintRepositoryHelper,
                            IndexerSetupMixIn):
    def setUp(self):
        restbase.mint_rephelp.MintRepositoryHelper.setUp(self)
        IndexerSetupMixIn.setUp(self)

    def NoReallyIgnoreThistestConaryProxyInjection(self):
        # This test fails in bamboo when running setUp, so I changed the name
        # to avoid it being executed ever
        raise testsetup.testsuite.SkipTestException("Fails in bamboo")
        mintClient = self.startMintServer(useProxy = True)
        rpmFile0 = os.path.join(self.sourceSearchDir,
            'with-config-special-0.2-1.noarch.rpm')

        indexer = self.indexer()
        # Populate the db with the proper data, to avoid the test trying to
        # contact RHN
        capsuleKey = ('with-config-special', None, '0.2', '1', 'noarch')
        capsuleSha1sum = '4daf5f932e248a32758876a1f8ff12a5f58b1a54'
        pkg = indexer.getPackage(capsuleKey, capsuleSha1sum)
        self.failUnless(
            pkg.path.endswith("with-config-special-0.2-1.noarch.rpm"),
            pkg.path)

        self.openRepository(1, excludeCapsuleContents = True)

        ver0 = "/localhost1@rpl:linux/1-1-1"
        trv0 = self.addComponent("foo:data", ver0, filePrimer = 1)
        trv0 = self.addRPMComponent("%s=%s" % ("foo:rpm", ver0),
             rpmPath = rpmFile0)

        # Absolute changeset
        joblist = [ ('foo:rpm', (None, None),
            (trv0.getVersion(), trv0.getFlavor()), True) ]

        cli = conaryclient.ConaryClient(self.cfg)
        cs = cli.repos.createChangeSet(joblist, withFiles = True,
                            withFileContents = True)
        # Fetch the apache error log
        errorLog = os.path.join(self.mintServers.servers[0].serverRoot,
            'error_log')
        # Make sure we have entries for capsule requests
        lines = [ x.strip() for x in file(errorLog) ]
        downloaded = None
        for line in lines:
            if line.endswith("Retrieving package with key ('with-config-special', None, '0.2', '1', 'noarch'), sha1sum 4daf5f932e248a32758876a1f8ff12a5f58b1a54"):
                downloaded = line
                break
        self.failUnless(downloaded, lines)

class NoCapsulesConfiguredTest(BaseCapsulesTest):
    def _getSources(self):
        src = self.Source()
        src.username = None
        return [ src ]

    def testRefreshNoSources(self):
        indexer = base.IndexerTestMixIn.indexer(self)
        channelLabel = 'rhel-x86_64-server-5'
        # Make sure we don't have any content in the channels
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(channels, [])
        uri = 'capsules/rpm/content'
        client = self.getRestClient()
        req, response = client.call('POST', uri)
        self.failUnlessEqual(response.status, 204)
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(len(channels), 0)

class MultiSourceCapsulesTest(BaseCapsulesTest):
    def _getSources(self):
        src = self.Source()

        sat = self.Source()
        sat.contentSourceType = 'satellite'
        sat.name = 'RHN satellite'
        sat.shortName = 'satellite'
        sat.sourceUrl = 'https://blah/foo'
        sat.username = 'JeanValjeanSatellite'

        proxy1 = self.Source()
        proxy1.contentSourceType = 'proxy'
        proxy1.name = 'RHN Proxy 1'
        proxy1.shortName = 'proxy1'
        proxy1.sourceUrl = 'https://proxy1/foo'
        proxy1.username = 'JeanValjeanProxy1'

        proxy2 = self.Source()
        proxy2.contentSourceType = 'proxy'
        proxy2.name = 'RHN Proxy 2'
        proxy2.shortName = 'proxy2'
        proxy2.sourceUrl = 'https://proxy2/foo'
        proxy2.password = None

        nu = self.Source()
        nu.contentSourceType = 'nu'
        nu.name = 'Novell Update Server'
        nu.shortName = 'nu'
        nu.username = 'username_nu'
        nu.password = 'password_nu'
        nu.platformLabel = 'localhost@sles:plat'

        smt1 = self.Source()
        smt1.contentSourceType = 'SMT'
        smt1.name = 'Subscription Management Tool'
        smt1.shortName = 'smt1'
        smt1.sourceUrl = 'https://smt1/'
        smt1.username = None # No auth required here
        smt1.platformLabel = 'localhost@sles:plat'

        smt2 = self.Source()
        smt2.contentSourceType = 'SMT'
        smt2.name = 'Subscription Management Tool'
        smt2.shortName = 'smt2'
        smt2.sourceUrl = 'https://smt2/'
        smt2.username = 'username_smt2'
        smt2.password = 'password_smt2'
        smt2.platformLabel = 'localhost@sles:plat'

        centos1 = self.Source()
        centos1.contentSourceType = 'repomd'
        centos1.name = 'Yum Repository'
        centos1.shortName = 'centos1'
        centos1.sourceUrl = 'https://centos1/'
        centos1.username = None # No auth required here
        centos1.platformLabel = 'localhost@centos:plat'

        centos2 = self.Source()
        centos2.contentSourceType = 'repomd'
        centos2.name = 'Yum Repository'
        centos2.shortName = 'centos2'
        centos2.sourceUrl = 'https://centos2/'
        centos2.username = 'username-centos2'
        centos2.password = 'password-centos2'
        centos2.platformLabel = 'localhost@centos:plat'

        return [ proxy1, proxy2, src, sat, nu, smt1, smt2, centos1, centos2 ]

    def testRefreshMultipleSources(self):
        indexer = base.IndexerTestMixIn.indexer(self)
        channelLabel = 'rhel-x86_64-server-5'
        # Make sure we don't have any content in the channels
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(channels, [])
        uri = 'capsules/rpm/content'
        client = self.getRestClient()
        req, response = client.call('POST', uri)
        self.failUnlessEqual(response.status, 204)
        channels = indexer.model.enumerateChannels()
        self.failUnlessEqual(sorted([ x.label for x in channels ]),
            ['rhel-i386-as-4', 'rhel-x86_64-as-4'])

        # Check that we generated the config correctly
        db = self.openRestDatabase()
        indexer = db.capsuleMgr.getIndexer()
        sources = list(indexer.iterRhnSources())
        self.failUnlessEqual([x.rpc.username for x in sources],
            ['JeanValjeanProxy1', 'JeanValjeanSatellite', 'JeanValjean'])
        sources = list(indexer.iterYumRepositories())
        self.failUnlessEqual([x.label for x in sources], [
            'centos:5.4/os/i386',
            'centos:5.4/os/x86_64',
            'centos:5.4/updates/i386',
            'centos:5.4/updates/x86_64',
            'centos:5.5/os/i386',
            'centos:5.5/os/x86_64',
            'centos:5.5/updates/i386',
            'centos:5.5/updates/x86_64',
            'novell:SLE10-SDK-SP3-Online/sles-10-i586',
            'novell:SLE10-SDK-SP3-Online/sles-10-x86_64',
            'novell:SLE10-SDK-SP3-Pool/sles-10-i586',
            'novell:SLE10-SDK-SP3-Pool/sles-10-x86_64',
            'novell:SLE10-SDK-SP3-Updates/sles-10-i586',
            'novell:SLE10-SDK-SP3-Updates/sles-10-x86_64',
            'novell:SLES10-SP3-Online/sles-10-i586',
            'novell:SLES10-SP3-Online/sles-10-x86_64',
            'novell:SLES10-SP3-Pool/sles-10-i586',
            'novell:SLES10-SP3-Pool/sles-10-x86_64',
            'novell:SLES10-SP3-Updates/sles-10-i586',
            'novell:SLES10-SP3-Updates/sles-10-x86_64',
        ])
        centosUrls = ['https://centos1//5.4/os/i386',
            'https://username-centos2:password-centos2@centos2//5.4/os/i386']
        novellUrls = [
            'https://smt1//SLES10-SP3-Updates/sles-10-x86_64',
            'https://username_smt2:password_smt2@smt2//SLES10-SP3-Updates/sles-10-x86_64',
            'https://username_nu:password_nu@nu.novell.com/repo/$RCE/SLES10-SP3-Updates/sles-10-x86_64',
        ]
        self.failUnlessEqual([ str(y.url) for y in sources[0].sources ],
            centosUrls)
        self.failUnlessEqual([ str(y.url) for y in sources[-1].sources ],
            novellUrls)

        self.failUnless(indexer.hasSources())

    def testSetProxies(self):
        db = self.openRestDatabase()
        cfg = db.capsuleMgr.getIndexerConfig()
        self.failUnlessEqual(cfg.proxyMap.filterList, [])

        # Add proxy information to the rest db
        proxyDict = dict(http = "http://foo.bar:1234",
                         https = "https://foo.baz:1234")
        db.cfg.proxy = proxyDict

        cfg = db.capsuleMgr.getIndexerConfig()
        self.failUnlessEqual(
            [ [ u.hostport.host.name for u in x[1]] for x in
            cfg.getProxyMap().items() ],
            [['foo.bar'], ['foo.baz']])

if __name__ == "__main__":
        testsetup.main()

