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


import optparse
import sys

from conary import dbstore
from mint import config
from mint.db import schema
from mint.lib import scriptlibrary


class Script(scriptlibrary.SingletonScript):
    cfgPath = config.RBUILDER_CONFIG
    logFileName = 'scripts.log'
    options = None
    args = None
    newLogger = True

    def handle_args(self):
        usage = "%prog [options] "
        op = optparse.OptionParser(usage=usage)
        op.add_option("--migrate", action = "store_true",
                dest = "should_migrate", default = False,
                help = "Migrate the schema to the latest version")
        op.add_option('--create', action='store_true',
                help="Create missing database tables (not recommended)")
        op.add_option("-c", "--rbuilder-config",
                dest = "cfgPath", default = self.cfgPath,
                help = "use a different configuration file")

        (self.options, self.args) = op.parse_args()
        # read the configuration
        cfg = config.MintConfig()
        cfg.read(self.options.cfgPath)
        self.setConfig(cfg)
        return True

    def action(self):
        db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        if self.options.create:
            print >> sys.stderr, "Force-creating database schema ..."
            db.loadSchema()
            schema.createSchema(db, cfg=self.cfg)
        else:
            schema.loadSchema(db, self.cfg, self.options.should_migrate)

        return 0
