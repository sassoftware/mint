#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved
#
import logging
import os
import pwd
import sys
import tempfile
import traceback

from raa.modules.raasrvplugin import rAASrvPlugin

from mint import config
from mint import helperfuncs
from mint import rmake_setup
from mint import shimclient

from mint.mint_error import RmakeRepositoryExistsError, UserAlreadyExists

from conary.lib.cfgtypes import CfgBool

log = logging.getLogger('raa.server.rbasetup')

class rBASetup(rAASrvPlugin):
    """
    Plugin for the backend work of the rBuilder Appliance Setup plugin.
    """

    def __init__(self, *args, **kwargs):
        rAASrvPlugin.__init__(self, *args, **kwargs)

    def _readConfigFile(self, configFileName):
        """
        This reads the whole configuration at /srv/rbuilder/conf/rbuilder.conf.
        The reason for doing this is so we can break if someone has 
        already configured rBuilder using the custom configuration file.
        """
        cfg = config.MintConfig()
        try:
            cfg.read(configFileName)
        except Exception, e:
            log.warn("Failed to read rBuilder configuration (reason: %s)." \
                     "Using default values!" % str(ioe))
        return cfg

    def _writeGeneratedConfigFile(self, newValues, generatedConfigFileName):
        """
        Writes the generated configuration file.
        """
        log.info('Writing new configuration to %s' % generatedConfigFileName)

        # Read back in the current config from disk
        newCfg = self._readConfigFile(config.RBUILDER_CONFIG)
        for k, v in newValues.iteritems():
            if k in newCfg: newCfg[k] = v

        firstTimeSetup = newCfg.configured

        # Post process the configuration
        newCfg.postCfg()
        newCfg.SSL = True
        newCfg.secureHost = newCfg.siteHost
        newCfg.projectDomainName = newCfg.externalDomainName = newCfg.siteDomainName

        # Set up the initial rBuilder user
        if not firstTimeSetup:
            newCfg.bugsEmail = newCfg.adminMail = newValues['new_email']
            addedUser = self._addRBuilderAdminAccount(
                    newValues['new_username'],
                    newValues['new_password'],
                    newValues['new_email'])
            if not addedUser:
                log.error("Failed to add initial administrative user to rBuilder, not saving config")
                return False

        # Generate a new authPass IFF we're not configured
        if not firstTimeSetup:
            newCfg.authPass = helperfuncs.genPassword(32)

        # Ensure that configured is True
        newCfg.configured = True

        # Write the generated config
        f = None
        try:
            try:
                f = file(generatedConfigFileName, 'w')
                for k in config.keysForGeneratedConfig:
                    newCfg.displayKey(k, out = f)
            except IOError, ioe:
                log.error("Failed to write configuration to %s, reason %s" %
                        (generatedConfigFileName, str(ioe)))
                return False
        finally:
            if f: f.close()

        return True

    def _addRBuilderAdminAccount(self, adminUsername, adminPassword, adminEmail):
        """
        Adds an admin user to the locally installed rBuilder.
        """
        cfg = self._readConfigFile(config.RBUILDER_CONFIG)
        shmclnt = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

        try:
            userId = shmclnt.registerNewUser(adminUsername, adminPassword,
                "Administrator", adminEmail, "", "", active=True)
            log.info("Created initial rBuilder account %s (id=%d)" % \
                    (adminUsername, userId))
            shmclnt.promoteUserToAdmin(userId)
            log.info("Promoted initial rBuilder account to admin level")
            return True
        except UserAlreadyExists:
            log.error("rBuilder user %s already exists!")
            return False
        except Exception, e:
            log.error("Failed to create rBuilder admin account %s (reason: %s)" % \
                    (adminUsername, str(e)))
            log.error(traceback.format_exc(sys.exc_info()[2]))
            return False

        return True


    def getRBAConfiguration(self, schedID, execId):
        """
        Reads the configuration file and returns only the items that
        can be configured by the first-time setup (defined in
        mint.config.keysForGeneratedConfig).

        Returns a double: the first is whether or not this rBuilder has
        been configured. The second is a dict of configurable options,
        as a key/value pair.
        """
        cfg = self._readConfigFile(config.RBUILDER_CONFIG)
        isConfigured = cfg.configured
        configurableOptions = dict()
        for k in config.keysForGeneratedConfig:
            if k not in cfg:
                continue
            v = cfg[k]
            # make safe for XMLRPC
            if v == None:
                v = ''
            configurableOptions[k] = v
        return isConfigured, configurableOptions

    def updateRBAConfig(self, schedId, execId, newValues):
        """
        Updates the generated configuration file. Expects a
        dictionary of key/value pairs to update.
        """
        return self._writeGeneratedConfigFile(newValues,
                config.RBUILDER_GENERATED_CONFIG)

    def restartApache(self, schedId, execId):
        """
        Restarts Apache (rBuilder web service).
        """
        try:
            retval = os.system("/sbin/service httpd restart")
            if retval != 0:
                log.error("Failed to restart Apache (error: %d)" % retval)
                return False
        except Exception, e:
            log.error("Failed to restart Apache (reason: %s)" % str(e))
            return False

        log.info("Successfully restarted Apache")
        return True

    def setupRMake(self, schedId, execId):
        """
        Sets up rMake for appliance creator, etc.
        """
        cfg = self._readConfigFile(config.RBUILDER_CONFIG)
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
        log.info("Attempting to setup rMake - logging to %s" % childLogFn)

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
                    childLog.info("rMake repository setup -- need to restart rmake and rmake-node services")
                    rmake_setup.setupRmake(cfg, config.RBUILDER_RMAKE_CONFIG)
                    childLog.info("rMake repository setup -- need to restart rmake and rmake-node services")
                    rc = 0
                except RmakeRepositoryExistsError:
                    childLog.warn("rMake Repository already exists, skipping")
                    rc = -1
                except Exception, e:
                    childLog.error("Unexpected error occurred when attempting to create the rMake repository: %s" % str(e))
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

    def setupExternalProjects(self, schedId, execId):
        """
        Sets up a set of canned external projects.
        All this does is call a script which does the heavy lifting.
        """
        log.info("Attempting to set up external projects for platforms")
        rc = os.system("/usr/share/rbuilder/scripts/init-extproducts")
        return True
