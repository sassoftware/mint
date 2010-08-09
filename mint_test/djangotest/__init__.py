#!/usr/bin/python

import testsuite

import os
import sys

import mint_test

from django.test import TestCase
from django.test.client import Client

builtins = sys.modules.keys()
unimported = {}

class DjangoTest(TestCase):

    def setUpDjangoSettingsModule(self):
        settingsFile = os.path.join(mint_test.__path__[0], 'server/settings.py.in')
        settingsModule = os.path.join(self.cfg.dataPath, 'settings.py')
        dbDriver = 'sqlite3'
        user = ''
        port = ''
        os.system("sed 's|@MINTDBPATH@|%s|;s|@MINTDBDRIVER@|%s|;"
                        "s|@MINTDBUSER@|%s|;s|@MINTDBPORT@|%s|' %s > %s" % \
            (os.path.join(self.cfg.dataPath, 'mintdb'), dbDriver,
             user, port, settingsFile, settingsModule))
        sys.path.insert(0, self.cfg.dataPath)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

    def importDjango(self):
        from mint.django_rest.rbuilder import models as rbuildermodels
        from mint.django_rest.rbuilder import inventory
        from mint.django_rest.rbuilder.inventory import systemdbmgr
        from mint.django_rest.rbuilder.inventory import models as systemmodels
        self.inventory = inventory
        self.rbuildermodels = rbuildermodels
        self.systemdbmgr = systemdbmgr
        self.systemmodels = systemmodels

    def _unImport(self):
        # "Unimport" anything that was imported so the next test will have a new
        # settings.py.
        for k, v in sys.modules.items():
            if k not in builtins or 'django' in k:
                unimported[k] = v
                sys.modules.pop(k)

    def setUp(self):
        unimported = {}
        self._unImport()
        TestCase.setUp(self)
        self.db, self.data = self.loadFixture('Empty')
        # Need to prepare settings.py before importing any django modules.
        self.setUpDjangoSettingsModule()
        self.importDjango()
        self.client = Client()

    def _import(self):
        for k, v in unimported.items():
            sys.modules[k] = v

    def tearDown(self):
        self._import()
