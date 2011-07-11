#
# Copyright (C) 2006 rPath, Inc.
# All rights reserved
#

import raa.lib.command
from raa import rpath_error
from raa.constants import *
from raa.modules.raasrvplugin import rAASrvPlugin
from conary import dbstore
from conary.dbstore import sqlerrors
from conary.lib import util
from conary.repository.netrepos.netserver import ServerConfig
from mint import config
from mint.db import projects
import pgsql
import os, subprocess, select

import time
import logging
log = logging.getLogger('raa.service')

class ConversionError(rpath_error.ConfigurationError):
    def __str__(self):
        return self.msg

class PreparationError(rpath_error.ConfigurationError):
    def __str__(self):
        return self.msg

def _startPostgresql():
    count = 0
    started = False
    while True:
        try:
            dbm = dbstore.connect('postgres@localhost.localdomain:5439/template1', 'postgresql')
        except pgsql.ProgrammingError, e:
            log.warning("PostgreSQL was not running, attempting to start it")
            if not started:
                try:
                    raa.lib.command.runCommand(['/sbin/service', 'postgresql-rbuilder', 'start'], close_fds=True)
                except rpath_error.UnknownException, e:
                    log.error("An error occured when attempting to start the PostgreSQL service")
                    raise
                else:
                    started = True
            # Bail if we've tried more than 8 times already
            elif count > 8:
                raise PreparationError("Unable to connect to PostgreSQL service after approximately 30 seconds")
            time.sleep(4) #Don't spin loop here
            count = count + 1
        else:
            # Add the plpgsql language to template1 so new databases will
            # have it.
            cu = dbm.cursor()
            try:
                cu.execute('CREATE LANGUAGE plpgsql')
            except sqlerrors.CursorError:
                log.info('Language "plpgsql" already exists')
            break
    return True

class reportCallback:
    _msgs = None
    _lastreport = 0

    def __init__(self, reportfunc):
        self.reportfunc = reportfunc
        self._msgs = list()

    def _report(self):
        self._lastreport = time.time()
        self.reportfunc(self._msgs)
        self._msgs = list()

    def addMessage(self, msg):
        self._msgs.append(msg)
        elapsedTime = time.time() - self._lastreport
        if elapsedTime > 3:
            self._report()

    def flush(self):
        if len(self._msgs) > 0:
            self._report()


class SqliteToPgsql(rAASrvPlugin):
    convertScript = '/usr/share/conary/migration/db2db.py'
    #This follows the assumption that the pg database is on localhost
    pgConnectString = '%s@localhost.localdomain:5439/%%s'
    pgConnectUser = 'rbuilder'

    def _runScriptAndReportOutput(self, execId, cmd, messagePrefix = '', reporter = None):
        env = os.environ
        env.update(dict(LANG="C"))
        poller = select.poll()

        po = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        poller.register(po.stdout.fileno(), select.POLLIN)
        poller.register(po.stderr.fileno(), select.POLLIN)
        stdoutReader = util.LineReader(po.stdout.fileno())
        stderrReader = util.LineReader(po.stderr.fileno())

        count = 2
        while count:
            fds = [ x[0] for x in poller.poll() ]
            for (fd, reader, isError) in (
                        (po.stdout.fileno(), stdoutReader, False),
                        (po.stderr.fileno(), stderrReader, True) ):
                if fd not in fds: continue
                lines = reader.readlines()

                if lines == None:
                    poller.unregister(fd)
                    count -= 1
                else:
                    for l in lines:
                        #Report the last five lines to the frontend
                        line = l.strip()
                        if reporter:
                            reporter.addMessage(line)
                        if isError:
                            log.error('%s%s' % (messagePrefix, line))
                        else:
                            log.info('%s%s' % (messagePrefix, line))
        rc = po.wait()
        if reporter:
            reporter.flush()
        return rc

    def _getRepNameMaps(self, cu):
        # get repname map used to help find the local Conary repository
        # for external locally-mirrored projects
        # FIXME: wrong, but this plugin isn't supported in 6.0 anyway. Used to
        # refer to RepNameMap but that is gone.
        return {} 

    def _getLocalDbProjects(self, cu):
        # get all projects which are not external OR are external, but are locally mirrored
        cu.execute("""SELECT hostname, domainname, external,
                         EXISTS(SELECT * FROM InboundMirrors 
                                   WHERE projectId=targetProjectId) as mirrored
                      FROM Projects WHERE external = 0 or mirrored = 1""")

        dbNames = [x[0] + "." + x[1] for x in cu.fetchall()]
        return dbNames

    def _getDBNames(self, path, driver):
        db = dbstore.connect(path, driver=driver)
        cu = db.cursor()
        repnamemap = self._getRepNameMaps(cu)
        #Grab the list of projects
        dbNames = self._getLocalDbProjects(cu)
        db.close()
        return repnamemap, dbNames

    def _createNewProjectTable(self, mc, pgDbName):
            db = dbstore.connect(mc.dbPath, mc.dbDriver)
            #create the new database
            pt = projects.ProjectsTable(db, mc)
            pt.reposDB.create(pgDbName)
            db.close()

    def _runConversion(self, execId):
        #Connect to the mintdb
        mc = config.MintConfig()
        mc.read(config.RBUILDER_CONFIG)
        mc.reposDBDriver = 'postgresql' # this converts the ProjectsTable into a postgres tablegenerator
        #Store a copy of the sqlitedb path, we need it for the conversion script
        sqliteDBPath = mc.reposDBPath
        mc.reposDBPath = self.pgConnectString % 'postgres'
        repnamemap, dbNames = self._getDBNames(mc.dbPath, mc.dbDriver)

        self.reportMessage(execId, "Migrating rBuilder Repositories to PostgreSQL...")
        error = False
        databases = []
        # Capture the output
        def reportfunc(msgs):
            self.reportMessage(execId, '\n'.join(msgs[-5:]))
        for dbName, count in zip(dbNames, range(1,len(dbNames)+1)):
            # lookup things in the repnamemap to resolve external local
            # mirrors
            actualDbName = repnamemap.get(dbName, dbName)
            pgDbName = actualDbName.translate(projects.transTables['postgresql'])

            self._createNewProjectTable(mc, pgDbName)
            #NOTE: We do not create the schema here, the conversion script handles that

            self.reportMessage(execId, 'Converting %s repository' % dbName)
            cmd = [self.convertScript, '--sqlite=' + sqliteDBPath % actualDbName,
                    '--postgresql=' + (mc.reposDBPath % pgDbName)]
            rc = self._runScriptAndReportOutput(execId, cmd,
                    messagePrefix='Conary PostgreSQL Conversion: ',
                    reporter=reportCallback(reportfunc))
            if rc:
                raise ConversionError("Error running conversion script on %s, returned %d" % (dbName, rc))
            else:
                self.reportMessage(execId, 'Conversion completed successfully for %s' %dbName)
        self.reportMessage(execId, 'Saving new database configuration values')
        self._saveRepositoryDbPath(mc)
        self.reportMessage(execId, 'Migration complete')

    def _saveRepositoryDbPath(self, cfg):

        #Save a backup of the original file
        util.copyfile(config.RBUILDER_GENERATED_CONFIG, config.RBUILDER_GENERATED_CONFIG + ".backup")
        #Write the new list of config items
        cfg.writeGeneratedConfig()

    def doTask(self, schedId, execId):
        '''
        '''
        #shut down httpd
        self.reportMessage(execId, "Shutting down httpd")
        raa.lib.command.runCommand(['/sbin/service', 'httpd', 'stop'])

        # Check to see if we can talk to the server, and start it if necessary
        self.reportMessage(execId, "Checking that PostgreSQL is running, and if not, starting it")
        _startPostgresql()

        #Run the conversion script
        self.reportMessage(execId, "Running database conversion script")
        self._runConversion(execId)

        #restart httpd
        self.reportMessage(execId, "Starting httpd")
        raa.lib.command.runCommand(['/sbin/service', 'httpd', 'start'])

