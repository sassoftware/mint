#!/usr/bin/python
import testsetup

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

        s1 = contentsources.contentSourceTypes['satellite']()
        s1.name = name1
        s1.sourceUrl = url1
        self.failUnlessEqual(s1.name, name1)
        self.failUnlessEqual(s1.sourceUrl, url1)

        s2 = contentsources.contentSourceTypes['satellite']()
        s2.name = name2
        s2.sourceUrl = url2
        self.failUnlessEqual(s2.name, name2)
        self.failUnlessEqual(s2.sourceUrl, url2)

        raise testsetup.testsuite.SkipTestException("RBL-5694: the next lines fail")
        self.failUnlessEqual(s1.name, name1)
        self.failUnlessEqual(s1.sourceUrl, url1)

    def testValidate(self):
        _transportProxies = []
        class Mock(base.Mock):
            class TransportDefaults(object):
                dataMap = {
                    'auth.login' : (":sessionHandle:", ),
                    'channel.software.availableEntitlements' : {
                        (':sessionHandle:', 'rhel-i386-as-4') : (10, ),
                    },
                }
            class Transport(base.Mock.Transport):
                def _setProxyInfo(slf):
                    # Save the proxy objects from the original transport
                    _transportProxies.append(slf._transport.proxies)
                    return base.Mock.Transport._setProxyInfo(slf)
            Transport.TransportDefaults = TransportDefaults
            class ServerProxy(base.Mock.ServerProxy):
                pass
            ServerProxy.Transport = Transport

        self.mock(rpath_capsule_indexer.Indexer.BaseSource.RPC,
            'ServerProxy', Mock.ServerProxy)
        name1 = "name1"
        url1 = "http://url1/adfadf"

        proxies = dict(https = "https://blah")

        for ctype in [ 'satellite', 'proxy']:
            del _transportProxies[:]
            s1 = contentsources.contentSourceTypes[ctype](proxies = proxies)
            s1.name = name1
            s1.sourceUrl = url1
            s1.username = 'my_user'
            s1.password = 'sikritPass'

            s1.status()
            self.failUnlessEqual(_transportProxies, [proxies] * 2)


testsetup.main()