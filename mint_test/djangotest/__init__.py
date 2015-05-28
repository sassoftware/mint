#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os
import sys

import mint_test
from mint_test import fixtures

builtins = sys.modules.keys()
unimported = {} #pepflakes ignore

class DjangoTest(fixtures.FixturedUnitTest):

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
        from mint.django_rest.rbuilder.inventory import models as systemmodels
        from mint.django_rest.rbuilder.inventory import manager
        
        self.inventory = inventory
        self.rbuildermodels = rbuildermodels
        self.systemmodels = systemmodels
        self.manager = manager

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
        fixtures.FixturedUnitTest.setUp(self)
        self.db, self.data = self.loadFixture('Empty')
        # Need to prepare settings.py before importing any django modules.
        self.setUpDjangoSettingsModule()
        self.importDjango()
        self.mgr = self.manager.Manager(self.cfg)

    def _import(self):
        for k, v in unimported.items():
            sys.modules[k] = v

    def tearDown(self):
        self._import()
