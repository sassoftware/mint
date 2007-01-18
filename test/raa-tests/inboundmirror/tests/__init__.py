#
# Copyright (C) 2006 rPath, Inc.
# All rights reserved.
#
import cherrypy
import raatest

from rPath.inboundmirror.srv.inboundmirror import InboundMirror

from raatests import webPluginTest
import os
import re
import StringIO

raaFramework = webPluginTest()
raaFramework.pseudoroot = cherrypy.root.inboundmirror.InboundMirror

class InboundMirrorTest(raatest.rAATest):
    def setUp(self):
        raatest.rAATest.setUp(self)
        self.oldSystem = os.system

    def tearDown(self):
        raatest.rAATest.tearDown(self)
        os.system = self.oldSystem

    def test_indexTitle(self):
        self.requestWithIdent("/inboundmirror/InboundMirror/")
        assert "<title>schedule inbound mirroring</title>" in cherrypy.response.body[0].lower()
    
    def test_index(self):
        res = self.callWithIdent(raaFramework.pseudoroot.index)
        defaultSched = {'hours': '1', 'timeDay': '1', 'timeHour': '1', 'checkFreq': 'Hourly', 'enabled': False, 'timeDayMonth': '1'}
        self.assertEquals(res, defaultSched)
        self.callWithIdent(raaFramework.pseudoroot.prefsSave, checkFreq='Monthly', timeHour='7', timeDay='2', timeDayMonth='5', hours='4', status='enabled')
        res = self.callWithIdent(raaFramework.pseudoroot.index)
        self.assertEquals(res['checkFreq'], 'Monthly')
        self.assertEquals(res['timeDayMonth'], 5)
        self.assertEquals(res['timeHour'], 7)
        self.assertEquals(res['enabled'], True)
        self.callWithIdent(raaFramework.pseudoroot.prefsSave, checkFreq='Weekly', timeHour='5', timeDay='6', timeDayMonth='22', hours='19', status='enabled')
        res = self.callWithIdent(raaFramework.pseudoroot.index)
        self.assertEquals(res, {'hours': '1', 'timeDay': 6, 'timeHour': 5, 'checkFreq': 'Weekly', 'enabled': True, 'timeDayMonth': 64})
        self.callWithIdent(raaFramework.pseudoroot.prefsSave, checkFreq='Hourly', timeHour='9', timeDay='4', timeDayMonth='21', hours='3', status='enabled')
        res = self.callWithIdent(raaFramework.pseudoroot.index)
        self.assertEquals(res['hours'], 3)

    def test_schedStrings(self):
        res = self.callWithIdent(raaFramework.pseudoroot.prefsSave, checkFreq='Hourly', timeHour='9', timeDay='4', timeDayMonth='21', hours='3', status='enabled')
        self.assertTrue(res['message'].startswith('Inbound mirroring has been regularly scheduled to occur Every 3 hour(s) from '))
        res = self.callWithIdent(raaFramework.pseudoroot.prefsSave, checkFreq='Monthly', timeHour='13', timeDay='4', timeDayMonth='28', hours='1', status='disabled')
        self.assertEquals(res['message'], 'Inbound mirroring is not regularly scheduled.')

    def test_misc(self):
        # Test daily setting
        self.callWithIdent(raaFramework.pseudoroot.prefsSave, checkFreq='Daily', timeHour='14', timeDay='6', timeDayMonth='22', hours='19', status='enabled')
        res = self.callWithIdent(raaFramework.pseudoroot.index)
        self.assertEquals(res['checkFreq'], 'Daily')
        self.assertEquals(res['timeHour'], 14)

        # Test Mirror Status
        res = self.callWithIdent(raaFramework.pseudoroot.checkMirrorStatus)
        self.assertFalse(res['mirroring'])

        # Test backend
        res = self.callWithIdent(raaFramework.pseudoroot.mirrorNow)
        InboundMirror.__init__ = lambda *args: None
        ibm = InboundMirror()
        sio = StringIO.StringIO()
        os.system = lambda st: sio.write(st)
        self.callWithIdent(ibm.doTask, res['schedId'], 1)
        self.assertEquals(sio.getvalue(), 'sudo -u apache /usr/share/rbuilder/scripts/mirror-inbound http://mintauth:mintpass@localhost/xmlrpc-private/ 2>> /srv/rbuilder/logs/mirror-inbound.log')

