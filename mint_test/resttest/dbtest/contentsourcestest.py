#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
import testsetup

from conary.lib.http import proxy_map
from mint.rest.db import contentsources

from mint_test import mint_rephelp
import rpath_capsule_indexer
from capsule_indexertest import base

class ContentSourceTypeTest(mint_rephelp.MintDatabaseHelper):
    def testMultipleSources(self):
        name1 = "name1"
        url1 = "url1"
        name2 = "name2"
        url2 = "url2"
        proxyMap = proxy_map.ProxyMap()

        srhn = contentsources.contentSourceTypes['RHN'](proxyMap=proxyMap)
        ds = srhn.getDataSource()
        self.failUnlessEqual(ds.rpc.proxyMap, proxyMap)
        self.failUnlessEqual(srhn.sourceUrl, 'https://rhn.redhat.com')

        s1 = contentsources.contentSourceTypes['satellite'](proxyMap=proxyMap)
        s1.name = name1
        s1.sourceUrl = url1
        self.failUnlessEqual(s1.name, name1)
        self.failUnlessEqual(s1.sourceUrl, url1)

        ds = s1.getDataSource()
        self.failUnlessEqual(ds.rpc.proxyMap, proxyMap)

        s2 = contentsources.contentSourceTypes['satellite'](proxyMap=proxyMap)
        s2.name = name2
        s2.sourceUrl = url2
        self.failUnlessEqual(s2.name, name2)
        self.failUnlessEqual(s2.sourceUrl, url2)

        # Test failure
        from conary.repository import transport
        urls = []
        def mockedUrlopen(slf, fullurl, data=None, headers=()):
            urls.append(fullurl)
            raise IOError("http error", 401, "Unauthorized", object())
        self.mock(transport.URLOpener, "open", mockedUrlopen)

        s3 = contentsources.contentSourceTypes['nu'](proxyMap=proxyMap)
        s3.username = 'JeanValjean'
        s3.password = 'Javert:!&#'
        self.failUnlessEqual(s3.getProxyMap(), proxyMap)
        self.failUnlessEqual(s3.status(),
            (False, False,
                "Error validating source at url https://nu.novell.com/repo/$RCE/SLES10-SP3-Online/sles-10-i586"))
        # Make sure the username and password made it all the way down to
        # conary's urlopen
        self.failUnlessEqual(str(urls[0]),
            "https://JeanValjean:Javert%3A%21%26%23@nu.novell.com/repo/$RCE/SLES10-SP3-Online/sles-10-i586/repodata/repomd.xml")

        s4 = contentsources.contentSourceTypes['SMT'](proxyMap=proxyMap)
        self.failUnlessEqual(s4.getProxyMap(), proxyMap)

        self.failUnlessEqual(s1.name, name1)
        self.failUnlessEqual(s1.sourceUrl, url1)

    def testValidate(self):
        _proxyMaps = []
        class Mock(base.Mock):
            class TransportDefaults(object):
                dataMap = {
                    'auth.login' : ":sessionHandle:",
                    'channel.software.availableEntitlements' : {
                        (':sessionHandle:', 'rhel-i386-as-4') : 10,
                    },
                }
            class Transport(base.Mock.Transport):
                def __init__(slf, transport):
                    _proxyMaps.append(transport.proxyMap)
                    base.Mock.Transport.__init__(slf,transport)
            Transport.TransportDefaults = TransportDefaults
            class ServerProxy(base.Mock.ServerProxy):
                pass
            ServerProxy.Transport = Transport

        self.mock(rpath_capsule_indexer.sourcerhn.BaseSource.RPC,
            'ServerProxy', Mock.ServerProxy)
        name1 = "name1"
        url1 = "http://url1/adfadf"

        proxyMap = proxy_map.ProxyMap()

        for ctype in [ 'satellite', 'proxy']:
            del _proxyMaps[:]
            s1 = contentsources.contentSourceTypes[ctype](proxyMap=proxyMap)
            s1.name = name1
            s1.sourceUrl = url1
            s1.username = 'my_user'
            s1.password = 'sikritPass'

            s1.status()
            self.failUnlessEqual(_proxyMaps, [proxyMap] * 2)


testsetup.main()
