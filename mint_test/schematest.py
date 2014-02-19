#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import tempfile
import time
import os, sys

from mint_rephelp import MintRepositoryHelper
from conary import dbstore
from conary import versions
from conary.lib import util


class UpgradePathTest(MintRepositoryHelper):
    def forceSchemaVersion(self, version):
        cu = self.db.cursor()
        cu.execute("DELETE FROM DatabaseVersion WHERE version > ?", version - 1)
        cu.execute("INSERT INTO DatabaseVersion VALUES(?, ?)", version,
                   time.time())
        self.db.commit()

    # XXX need to test the migration script

