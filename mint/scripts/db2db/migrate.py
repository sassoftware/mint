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


import logging
from conary import dbstore
from mint.scripts.db2db import db2db


log = logging.getLogger(__name__)


def switchToPostgres(cfg):
    if cfg.dbDriver in ('postgresql', 'pgpool'):
        return

    sourceTuple = (cfg.dbDriver, cfg.dbPath)
    destTuple = ('postgresql', 'postgres@localhost:5439/mint')
    finalTuple = ('pgpool', 'postgres@localhost.localdomain:6432/mint')

    log.info("Migrating mint database from %s::%s to %s::%s",
            *(sourceTuple + destTuple))
    db2db.move_database(sourceTuple, destTuple)

    # Update rbuilder-generated.conf
    log.info("Changing configured mint database to %s::%s", *finalTuple)
    cfg.dbDriver = finalTuple[0]
    cfg.dbPath = finalTuple[1]
    cfg.writeGeneratedConfig()
