#
# Copyright (C) 2008-2009 rPath, Inc.
# All rights reserved
#
import logging
import os
import pwd
import subprocess
import sys
import tempfile
import time
import traceback
import pickle
from conary import conarycfg

from raa.modules.raasrvplugin import rAASrvPlugin
from raa.rpath_error import PermanentTaskFailureException

from rPath.rbasetup import lib

from mint import config
from mint import helperfuncs
from mint import notices_callbacks
from mint import rmake_setup
from mint import shimclient
from mint.lib.siteauth import SiteAuthorization

from mint.mint_error import (RmakeRepositoryExistsError, UserAlreadyExists,
        UserAlreadyAdmin)

from conary.lib.cfgtypes import CfgBool

log = logging.getLogger('raa.server.rbasetup')

class rBASetup(rAASrvPlugin):
    """
    Plugin for the backend work of the rBuilder Appliance Setup plugin.
    """

    def __init__(self, *args, **kwargs):
        rAASrvPlugin.__init__(self, *args, **kwargs)
        self.shmclnt = None
        self.message = ""

    def _addRBuilderAdminAccount(self, adminUsername, adminPassword, adminEmail):
        """
        Adds an admin user to the locally installed rBuilder.
        """
        try:
            try:
                userId = self.shmclnt.registerNewUser(adminUsername, adminPassword,
                    "Administrator", adminEmail, "", "", active=True)
                log.info("Created initial rBuilder account %s (id=%d)",
                        adminUsername, userId)
            except UserAlreadyExists:
                log.warning("rBuilder user %s already exists!")
                userId = self.shmclnt.getUserIdByName(adminUsername)

            try:
                self.shmclnt.promoteUserToAdmin(userId)
                log.info("Promoted initial rBuilder account to admin level",
                        adminUsername)
            except UserAlreadyAdmin:
                log.warning("rBuilder user %s is already an admin!",
                        adminUsername)
        except Exception, e:
            errmsg = "Failed to create rBuilder admin account %s : %s" % \
                     (adminUsername, str(e))
            log.error(errmsg)
            return { 'errors': [ errmsg ] }

        return {}

    def _gracefulApache(self):
        """
        Use the graceful option to restart Apache (rBuilder web service).
        This, of course, assumes that Apache is running (a good assumption).
        """
        try:
            retval = os.system("/sbin/service httpd graceful")
            if retval != 0:
                log.error("Failed to gracefully restart Apache (error: %d)" % retval)
                return False
        except Exception, e:
            log.error("Failed to gracefully restart Apache (reason: %s)" % str(e))
            return False

        log.info("Successful graceful restart of Apache")
        return True

    def _setupRMake(self, mintcfg):
        """
        Sets up rMake for appliance creator, etc.
        """
        errors = []
        restartNeeded = False
        apacheUID, apacheGID = pwd.getpwnam('apache')[2:4]
        # log pipe
        rdfd, wrfd = os.pipe()
        rdfd2, wrfd2 = os.pipe()

        log.info("Attempting to setup rMake")

        pid = os.fork()
        if not pid: # child
            rc = -3
            try:
                errorWriter = None
                try:
                    os.close(rdfd)
                    os.close(rdfd2)
                    logWriter = os.fdopen(wrfd, 'w')
                    errorWriter = os.fdopen(wrfd, 'w')

                    # Reset logging in the child
                    childLog = logging.getLogger('setupRMake')
                    childLog.addHandler(logging.StreamHandler(logWriter))
                    childLog.setLevel(logging.DEBUG)

                    # Drop privs in the child to apache so as to not create
                    # repositories that cannot be written to by rBuilder.
                    os.setgroups([apacheGID])
                    os.setgid(apacheUID)
                    os.setuid(apacheUID)
                    childLog.info("Setting up the rMake repository")
                    rmake_setup.setupRmake(mintcfg, config.RBUILDER_RMAKE_CONFIG)
                    childLog.info("rMake repository setup complete; we need "
                            "to restart rmake and rmake-node services")
                    rc = 0
                except RmakeRepositoryExistsError:
                    childLog.warn("rMake Repository already exists, skipping")
                    rc = -1
                except Exception, e:
                    childLog.error("Unexpected error occurred when attempting "
                            "to create the rMake repository: %s" % str(e))
                    try:
                        pickle.dump(sys.exc_info()[:2], errorWriter)
                    except Exception, e:
                        log.error('Pickle failed: %s' % str(e))
                        pass
                    childLog.error(traceback.format_exc())
                    rc = -2
            finally:
                os._exit(rc)
        else: # parent
            # close the child log
            os.close(wrfd)
            os.close(wrfd2)
            logReader = os.fdopen(rdfd, "r")
            errorReader = os.fdopen(rdfd2, "r")
 
            # read the log lines coming back from the child
            while True:
                line = logReader.readline()
                if not line:
                    break
                log.info('rmake setup log: %s' % line)

            # if child exits and returns 0, we need to restart rMake
            log.info("Parent waiting on PID %d" % pid)
            childStatus = os.waitpid(pid,0)[1]
            childRC = os.WEXITSTATUS(childStatus)
            os.close(rdfd)
            if not os.WIFEXITED(childStatus) or (childRC and childRC != 255):
                log.info("Child exited with code %d" % childRC)
                try:
                    exc = pickle.load(errorReader)
                except Exception, e:
                    log.error('Unpickle failed: %s' % str(e))
                    return { 'errors': [ 'rmake setup exited with code %d' % childRC ] }
            restartNeeded = os.WIFEXITED(childStatus) and (childRC == 0)

        if restartNeeded:
            log.info("Restarting rMake service due to new configuration")
            rmakeRestart = subprocess.Popen(['/sbin/service', 'rmake', 'restart'],
                                            stdout = subprocess.PIPE,
                                            stderr = subprocess.PIPE)
            stdout, stderr = rmakeRestart.communicate()
            log.info('output for "service rmake restart": \nstderr: %s\nstdout: %s' % \
                    (stderr, stdout))
            if rmakeRestart.returncode == 0:
                rmakeNodeRestart = subprocess.Popen(['/sbin/service', 'rmake-node', 'restart'],
                                            stdout = subprocess.PIPE,
                                            stderr = subprocess.PIPE)
                stdout, stderr = rmakeNodeRestart.communicate() 
                log.info('output for "service rmake-node restart": \nstderr: %s\nstdout: %s' % \
                        (stderr, stdout))
            if rmakeRestart.returncode != 0 or rmakeNodeRestart.returncode != 0:
                return { 'errors': [ "Failed to restart rMake services. You may need to reboot " \
                         "the appliance for changes to take effect.", ] }

        return { 'message': 'complete.\n' }

    def _generateEntitlement(self, mintCfg):
        log.info("Generating rBuilder site entitlement ...")

        try:
            conaryCfg = conarycfg.ConaryConfiguration(True)
            auth = SiteAuthorization(mintCfg.siteAuthCfgPath, conaryCfg)
            if auth.isConfigured():
                msg = "Entitlement is already set; " + \
                        "keeping rBuilder ID %s .\n" % auth.rBuilderId
                log.warning(msg)
                return {'message': msg }

            newKey = auth.generate()
            if newKey is None:
                return {'errors': [ 'Failed to generate entitlement', ] }
            self.server.setNewEntitlement(newKey)

            msg = "Key successfully generated; your rBuilder ID is %s .\n" % auth.rBuilderId
            log.info(msg)
            return {'message': msg}
        except Exception, e:
            log.error("Failed to generate entitlement: %s" % str(e))
            return { 'errors': [ str(e), ] }

    def _setupExternalProjects(self):
        """
        Sets up a set of canned external projects.
        All this does is call a script which does the heavy lifting.
        """
        log.info("Attempting to set up external projects for platforms")
        try:
            errors = helperfuncs.initializeExternalProjects(self.shmclnt)
            if not errors:
                log.info("Successfully set up initial external projects")
                return {}
            else:
                log.error("Failed to set up initial external projects")
                return { 'errors': errors }
        except Exception, e:
            log.error("Failed to set up initial external projects")
            return { 'errors': "Failed to set up initial external projects" }            

        # Initial RSS feed for notices. Not external projects, but it doesn't
        # need its own section as it isn't important.
        os.system("/usr/share/rbuilder/scripts/rss-update -q")

        return {}

    def updateRBAConfig(self, schedId, execId, newValues):
        """
        Updates the generated configuration file. Expects a
        dictionary of key/value pairs to update.
        """

        # Read back in the current config from disk
        newCfg = lib.readRBAConfig(config.RBUILDER_CONFIG)
        for k, v in newValues.iteritems():
            if k in newCfg: newCfg[k] = v

        # If configured = False, it's the first time we've done this
        firstTimeSetup = (not newCfg.configured)

        # Post process the configuration
        newCfg.postCfg()
        newCfg.SSL = True
        newCfg.secureHost = newCfg.siteHost
        # Post processing for first timers
        if firstTimeSetup:
            # Set the bugs / adminMail to be the initial admin account
            if 'new_email' in newValues:
                newCfg.bugsEmail = newCfg.adminMail = newValues['new_email']

            # Generate a new authorized secret (mintpass)
            newCfg.authPass = helperfuncs.genPassword(32)

        # Make sure that configured is True
        newCfg.configured = True

        # Attempt to write the new generated configuration and restart Apache
        wroteConfig = lib.writeRBAGeneratedConfig(newCfg,
                config.RBUILDER_GENERATED_CONFIG)
        if not wroteConfig:
            return dict(errors=['Failed to write rBuilder configuration'])
        else:
            # Signal apache to restart itself
            self._gracefulApache()

        return dict(message="Configuration written.")

    def doTask(self, schedId, execId):
        """
        XXX - Calls first time setup.  No longer needed.
        """
        ret = self.firstTimeSetup(schedId, execId)
        if ret.has_key('errors'):
            raise PermanentTaskFailureException('\n'.join(ret['errors']))

    def firstTimeSetup(self, schedId, execId, options, step=lib.FTS_STEP_INITIAL):
        errors = ''
        try:
            return self._firstTimeSetup(schedId, execId, options, step=lib.FTS_STEP_INITIAL)
        except Exception, e:
            log.error('an unhandled exception occurred: %s' % str(e))
            return dict(errors=str(e))

    def _firstTimeSetup(self, schedId, execId, options, step=lib.FTS_STEP_INITIAL):
        """
        If this is a first-time configuration, this call will
        also do the following:
         -- create an initial administrative rBuilder account
         -- setup rMake
         -- create initial external projects
        """
        retry = options.get('retry', False)
        self.message = ""

        newCfg = lib.readRBAConfig(config.RBUILDER_CONFIG)
        self.shmclnt = shimclient.ShimMintClient(newCfg,
               (newCfg.authUser, newCfg.authPass))

        # don't re-add the admin user if it's just a retry
        if not retry:
            new_username = options.get('new_username')
            new_password = options.get('new_password')
            new_email = options.get('new_email')

            step = lib.FTS_STEP_ADMINACCT
            self.message += "Adding rBuilder Admin account: %s\n" % new_username
            self.reportMessage(execId, self.message)
            ret = self._addRBuilderAdminAccount(
                    new_username, new_password, new_email)
            if ret.has_key('errors'):
                return { 'errors': ret['errors'] , 'step': step, 'message': self.message }

        # Create the rMake repository and restart rMake if needed.
        # If this gets called twice, it's no big deal, as the
        # underlying code will not create duplicate repositories.
        step = lib.FTS_STEP_RMAKE
        self.message += "Setting up rMake build server...  "
        self.reportMessage(execId, self.message)
        result = self._setupRMake(newCfg)
        if result.has_key('errors'):
            return { 'errors': result['errors'], 'step': step, 'message': self.message }
        self.message += result.get('message', '')
        self.reportMessage(execId, self.message)

        # Generate an entitlement
        step = lib.FTS_STEP_ENTITLE
        self.message += "Generating an entitlement...  "
        self.reportMessage(execId, self.message)
        ret = self._generateEntitlement(newCfg)
        if ret.has_key('errors'):
            return { 'errors': ret['errors'], 'step': step, 'message': self.message }
        self.message += ret.get('message', '\n')
        self.reportMessage(execId, self.message)

        # Setup the initial external projects
        step = lib.FTS_STEP_INITEXTERNAL
        self.message += "Setting up external repositories...\n"
        self.reportMessage(execId, self.message)
        ret = self._setupExternalProjects()
        if ret.has_key('errors'):
            return { 'errors': ret['errors'], 'step': step, 'message': self.message }

        # Done
        self.message += "Setup is complete.\n"
        self.reportMessage(execId, self.message)

        cfg = lib.readRBAConfig(config.RBUILDER_CONFIG)
        cb = notices_callbacks.RbaSetupNoticeCallback(cfg,
                options.get('new_username'))
        cb.notify()
        # Since this plugin runs as root, we need to reset the permissions of
        # the rbuilder notices dir to apache.
        uid, gid = pwd.getpwnam('apache')[2:4]
        self._chown('/srv/rbuilder/notices', uid, gid)

        return { 'step': lib.FTS_STEP_COMPLETE, 'message': self.message }

    def _chown(self, root, uid, gid):
        os.chown(root, uid, gid)
        for root, dirs, paths in os.walk(root):
            for path in paths:
                os.chown(os.path.join(root, path), uid, gid)
            for dir in dirs:
                self._chown(os.path.join(root, dir), uid, gid)

