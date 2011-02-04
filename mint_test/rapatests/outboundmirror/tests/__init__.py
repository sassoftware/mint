#
# Copyright (C) 2006-2007 rPath, Inc.
# All rights reserved.
#
import raa.web
import cherrypy
import raatest

from rPath.outboundmirror.srv.outboundmirror import OutboundMirror

from mint_test.mintraatests import webPluginTest
import os
import re
import StringIO


class OutboundMirrorTest(raatest.rAATest):
    def setUp(self):
        self.raaFramework = webPluginTest()
        self.pseudoroot = raa.web.getWebRoot().outboundmirror.OutboundMirror
        raatest.rAATest.setUp(self)
        self.oldSystem = os.system

    def tearDown(self):
        raatest.rAATest.tearDown(self)
        os.system = self.oldSystem

    def test_indexTitle(self):
        self.requestWithIdent("/outboundmirror/OutboundMirror/")
        assert "<title>schedule outbound mirroring</title>" in cherrypy.response.body[0].lower(), "%s not in %s" % ("<title>schedule outbound mirroring</title>", cherrypy.response.body[0].lower())
    
    def test_index(self):
        res = self.callWithIdent(self.pseudoroot.index)
        defaultSched = {'enabled': False, 'schedule':{'timeDay': 0, 'timeHour': 23, 'checkFreq': 'Weekly',                        'timeDayMonth': 1}}
        self.assertEquals(res, defaultSched)
        self.callWithIdent(self.pseudoroot.prefsSave, checkFreq='Monthly', timeHour='7', timeDay='2', timeDayMonth='5', enabled='1')
        res = self.callWithIdent(self.pseudoroot.index)
        self.assertEquals(res['schedule']['checkFreq'], 'Monthly')
        self.assertEquals(res['schedule']['timeDayMonth'], 5)
        self.assertEquals(res['schedule']['timeHour'], 7)
        self.assertEquals(res['enabled'], True)
        self.callWithIdent(self.pseudoroot.prefsSave, enabled='1', checkFreq='Weekly', timeHour='5', timeDay='6', timeDayMonth='22')
        res = self.callWithIdent(self.pseudoroot.index)
        self.assertEquals(res, {'enabled':True, 'schedule':{'timeDay': 6, 'timeHour': 5, 
                                           'checkFreq': 'Weekly', 'timeDayMonth': 64}})
        res = self.callWithIdent(self.pseudoroot.index)
        self.assertEquals(res['schedule']['timeHour'], 5)

    def test_schedStrings(self):
        res = self.callWithIdent(self.pseudoroot.prefsSave, checkFreq='Daily', timeHour='9', timeDay='4', timeDayMonth='21', enabled=1)
        self.assertTrue(res['message'].startswith('Outbound mirroring has been regularly scheduled to occur Every 1 day(s) from '))
        res = self.callWithIdent(self.pseudoroot.prefsSave, checkFreq='Monthly', timeHour='13', timeDay='4', timeDayMonth='28', enabled=0)
        self.assertEquals(res['message'], 'Outbound mirroring is not regularly scheduled.')

    def test_misc(self):
        # Test daily setting
        self.callWithIdent(self.pseudoroot.prefsSave, checkFreq='Daily', timeHour='14', timeDay='6', timeDayMonth='22', enabled='1')
        res = self.callWithIdent(self.pseudoroot.index)
        self.assertEquals(res['schedule']['checkFreq'], 'Daily')
        self.assertEquals(res['schedule']['timeHour'], 14)

        # Test Mirror Status
        res = self.callWithIdent(self.pseudoroot.checkMirrorStatus)
        self.assertFalse(res['mirroring'])

        # Test backend
        res = self.callWithIdent(self.pseudoroot.mirrorNow)
        OutboundMirror.__init__ = lambda *args: None
        ibm = OutboundMirror()
        sio = StringIO.StringIO()
        os.system = lambda st: sio.write(st)
        self.callWithIdent(ibm.doTask, res['schedId'], 1)
        assert sio.getvalue().startswith('/usr/share/rbuilder/scripts/mirror-outbound "http://')
        assert sio.getvalue().endswith('@localhost/xmlrpc-private/"')


    def test_daily(self):
        """
        Thoroughly test daily scheduling, checking for multiple repeat 
        schedules.
        """
        for day_month in (1, 2):
            for day in (4, 5):
                for time_hour in (1, 23):
                    self.callWithIdent(self.pseudoroot.prefsSave, checkFreq='Daily', timeHour='%s' % time_hour, timeDay='%s' % day, timeDayMonth='%s' % day_month, enabled='1')
                    res = self.callWithIdent(self.pseudoroot.index)
                    self.assertEquals(res['schedule']['checkFreq'], 'Daily')
                    self.assertEquals(res['schedule']['timeHour'], time_hour)
                    scheds = self.pseudoroot.readSchedules()
                    self.assertEquals(len(scheds), 1)
                    self.assertEquals(scheds[0].interval, 60*60*24)
                    self.assertEquals(scheds[0].type, 3)
                    self.assertEquals(scheds[0].unit, 3)

        # add a second schedule and make sure it is removed properly
        import time
        from raa.db import schedule
        self.pseudoroot.schedule(schedule.ScheduleInterval(time.time(), None, 42, schedule.ScheduleInterval.INTERVAL_HOURS))
        # Disable scheduling
        self.callWithIdent(self.pseudoroot.prefsSave, checkFreq='Daily', timeHour='7', timeDay='6', timeDayMonth='22', enabled='0')
        scheds = self.pseudoroot.readSchedules()
        self.assertEquals(len(scheds),0)
