#
# Copyright (C) 2008-2009 rPath, Inc.
# All rights reserved
#
import logging
import os
import pwd
import sys
import tempfile
import time
import traceback
from conary import conarycfg

from raa.modules.raasrvplugin import rAASrvPlugin

from rPath.rbasetup import lib

from mint import config
from mint import helperfuncs
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

    def _addRBuilderAdminAccount(self, mintcfg, adminUsername,
            adminPassword, adminEmail):
        """
        Adds an admin user to the locally installed rBuilder.
        """
        shmclnt = shimclient.ShimMintClient(mintcfg,
                (mintcfg.authUser, mintcfg.authPass))
        try:
            try:
                userId = shmclnt.registerNewUser(adminUsername, adminPassword,
                    "Administrator", adminEmail, "", "", active=True)
                log.info("Created initial rBuilder account %s (id=%d)",
                        adminUsername, userId)
            except UserAlreadyExists:
                log.warning("rBuilder user %s already exists!")
                userId = shmclnt.getUserIdByName(adminUsername)

            try:
                shmclnt.promoteUserToAdmin(userId)
                log.info("Promoted initial rBuilder account to admin level",
                        adminUsername)
            except UserAlreadyAdmin:
                log.warning("rBuilder user %s is already an admin!",
                        adminUsername)
        except:
            log.exception("Failed to create rBuilder admin account %s :",
                    adminUsername)
            return False

        return True

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
        restartNeeded = False
        apacheUID, apacheGID = pwd.getpwnam('apache')[2:4]

        # NASTY HACK. Need to create a tmpfile to store log messages in for the
        # child process. A terrible hack needed since the standard logger
        # handlers are writing to raa-service.log, which is owned by root,
        # and thus cannot be written to by the child process, which will drop
        # root privileges.
        childLogFd, childLogFn = \
                tempfile.mkstemp(suffix='.log', prefix='setupRMake-')
        os.close(childLogFd)
        os.chown(childLogFn, apacheUID, apacheGID)
        log.info("Attempting to setup rMake - logging to %s", childLogFn)

        pid = os.fork()
        if not pid: # child
            rc = -3
            try:
                try:
                    # Reset logging in the child (see NASTY HACK above)
                    childLog = logging.getLogger('setupRMake')
                    childLog.addHandler(logging.FileHandler(childLogFn))
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
                    traceback.print_exc(file=childLogFn)
                    rc = -2
            finally:
                os._exit(rc)
        else: # parent
            # close the child log
            # if child exits and returns 0, we need to restart rMake
            log.info("Parent waiting on PID %d" % pid)
            childStatus = os.waitpid(pid,0)[1]
            childRC = os.WEXITSTATUS(childStatus)
            log.info("Child exited with %d" % childRC)
            restartNeeded = os.WIFEXITED(childStatus) and (childRC == 0)

        if restartNeeded:
            log.info("Restarting rMake service due to new configuration")
            rMakeRestartRC = os.system("/sbin/service rmake restart")
            if rMakeRestartRC == 0:
                rMakeNodeRestartRC = os.system("/sbin/service rmake-node restart")
            if rMakeRestartRC != 0 or rMakeNodeRestartRC != 0:
                log.warn("Failed to restart rMake services. You may need to reboot " \
                         "the appliance for changes to take effect.")

        return True

    def _generateEntitlement(self, mintCfg):
        log.info("Generating rBuilder site entitlement ...")

        try:
            conaryCfg = conarycfg.ConaryConfiguration(True)
            auth = SiteAuthorization(mintCfg.siteAuthCfgPath, conaryCfg)
            if auth.isConfigured():
                log.warning("Entitlement is already set; "
                        "keeping rBuilder ID %s .", auth.getRbuilderId())
                return True

            newKey = auth.generate()
            self.server.setNewEntitlement(newKey)

            rbuilderId = auth.getRbuilderId()
            log.info("Key successfully generated; your new rBuilder ID is %s .",
                    rbuilderId)
            return True
        except:
            log.exception("Failed to generate entitlement")
            return False

    def _setupExternalProjects(self):
        """
        Sets up a set of canned external projects.
        All this does is call a script which does the heavy lifting.
        """
        log.info("Attempting to set up external projects for platforms")
        rc = os.system("/usr/share/rbuilder/scripts/init-extproducts")
        if (rc == 0):
            log.info("Successfully set up initial external projects")
        else:
            log.error("Failed to set up initial external projects")
        return True

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
        newCfg.projectDomainName = newCfg.externalDomainName = newCfg.siteDomainName
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

        # Signal apache to restart itself
        self._gracefulApache()

        return wroteConfig

    def doTask(self, schedId, execId):
        """
        Calls first time setup.
        """
        return self.firstTimeSetup(schedId, execId)

    def firstTimeSetup(self, schedId, execId):
        """
        If this is a first-time configuration, this call will
        also do the following:
         -- create an initial administrative rBuilder account
         -- setup rMake
         -- create initial external projects
        """

        # Add the initial admin account
        self.server.setFirstTimeSetupState(lib.FTS_STEP_ADMINACCT)
        newCfg = lib.readRBAConfig(config.RBUILDER_CONFIG)
        newValues = self.server.getFirstTimeSetupAdminInfo()
        addedUser = self._addRBuilderAdminAccount(
                newCfg,
                newValues['new_username'],
                newValues['new_password'],
                newValues['new_email'])
        if not addedUser:
            errorMsg = "Failed to add initial administrative user '%s' to rBuilder" % newValues['new_username']
            log.warning(errorMsg)

            return False

        # Create the rMake repository and restart rMake if needed.
        # If this gets called twice, it's no big deal, as the
        # underlying code will not create duplicate repositories.
        self.server.setFirstTimeSetupState(lib.FTS_STEP_RMAKE)
        self._setupRMake(newCfg)

        # Generate an entitlement
        self.server.setFirstTimeSetupState(lib.FTS_STEP_ENTITLE)
        if not self._generateEntitlement(newCfg):
            return False

        # Setup the initial external projects
        self.server.setFirstTimeSetupState(lib.FTS_STEP_INITEXTERNAL)
        self._setupExternalProjects()

        # Done
        self.server.setFirstTimeSetupState(lib.FTS_STEP_COMPLETE)

