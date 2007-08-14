#!/usr/bin/python
import os, sys
import traceback

from mint import config
from mint import maintenance

from conary.lib import util

def migrateAllRepositories():
    util.execute('/usr/share/rbuilder/scripts/migrate-all-projects')

def migrateTo_1():
    migrateAllRepositories()

def migrateTo_2():
    import time
    for i in range(1000):
        print "spinloop for %i/1000 seconds" % i
        sys.stdout.flush()
        time.sleep(1)

def commonPostCommands():
    util.execute('/sbin/service sendmail start')

class SchemaMigrationError(Exception):
    def __init__(self, msg):
            self.msg = msg
    def __str__(self):
        return self.msg

def handleUpdate(fromVer, toVer):
    if toVer > fromVer:
        curVer = fromVer
        while curVer < toVer:
            nextVer = curVer + 1
            func = sys.modules[__name__].__dict__.get('migrateTo_%d' % nextVer)
            try:
                if not func:
                    raise  SchemaMigrationError( \
                            "migration for version %d not found" % nextVer)
                func()
                curVer += 1
            except:
                exc_cl, exc, bt = sys.exc_info()
                print traceback.print_tb(bt)
                print >> sys.stderr, exc
                sys.stderr.flush()
                raise SchemaMigrationError( \
                        "Error encountered while migrating. " \
                        "Last successful version: %d" % curVer)
    commonPostCommands()
    return toVer

def postUpdate(fromVer = None, toVer = None):
    cfg = config.MintConfig()
    cfg.read(config.RBUILDER_CONFIG)
    maintenance.setMaintenanceMode(cfg, maintenance.LOCKED_MODE)
    try:
        if fromVer is None:
            fromVer = os.getenv('CONARY_OLD_COMPATIBILITY_CLASS')
            assert fromVer is not None, \
                    "set environment variable CONARY_OLD_COMPATIBILITY_CLASS"
            fromVer = int(fromVer)
        if toVer is None:
            toVer = os.getenv('CONARY_NEW_COMPATIBILITY_CLASS')
            assert toVer is not None, \
                    "set environment variable CONARY_NEW_COMPATIBILITY_CLASS"
            toVer = int(toVer)
        handleUpdate(fromVer, toVer)
    except Exception, e:
        print e
        sys.stdout.flush()
        raise
    else:
        maintenance.setMaintenanceMode(cfg, maintenance.NORMAL_MODE)

def preUpdate():
    cfg = config.MintConfig()
    cfg.read(config.RBUILDER_CONFIG)
    maintenance.setMaintenanceMode(cfg, maintenance.LOCKED_MODE)

