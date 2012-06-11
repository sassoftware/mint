#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
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
