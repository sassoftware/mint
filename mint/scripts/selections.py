#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

from mint import config
from mint.db import selections
from mint.lib import scriptlibrary

from conary import dbstore

class UpdateProjectLists(scriptlibrary.SingletonScript):
    db = None
    cfg = None
    cfgPath = config.RBUILDER_CONFIG

    def __init__(self, aLockPath = scriptlibrary.DEFAULT_LOCKPATH):
        self.cfg = config.MintConfig()
        self.cfg.read(self.cfgPath)
        scriptlibrary.SingletonScript.__init__(self, aLockPath)

    def action(self):
        self.db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        self.db.loadSchema()
        topProjects = selections.TopProjectsTable(self.db)
        popularProjects = selections.PopularProjectsTable(self.db)
        latestCommits = selections.LatestCommitTable(self.db)

        topProjects.calculate()
        popularProjects.calculate()
        latestCommits.calculate()

        return 0

    def cleanup(self):
        if self.db:
            self.db.close()
