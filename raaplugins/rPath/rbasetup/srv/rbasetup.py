#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved
#
import logging
import os

from raa.modules.raasrvplugin import rAASrvPlugin

from mint import config
from mint import helperfuncs
from mint import shimclient

from mint.mint_error import RmakeRepositoryExistsError

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
            # XXX stubbed temporarily
            #userId = shmclnt.registerNewUser(adminUsername, adminPassword,
            #    "Administrator", adminEmail, "", "", active=True)
            #log.info("Created initial rBuilder account %s (id=%d)" % \
            #        (adminUsername, userId))
            #shmclnt.promoteUserToAdmin(userId)
            #log.info("Promoted initial rBuilder account to admin level")
            return True
        except Exception, e:
            log.error("Failed to create rBuilder admin account %s (reason: %s)" % \
                    (adminUsername, str(e)))
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
        return True

    def setupRMake(self, schedId, execId):
        """
        Sets up rMake for appliance creator, etc.
        """
        cfg = self._readConfigFile(config.RBUILDER_CONFIG)
        restartNeeded = False
        try:
            # Drop privs temporarily to Apache so as to not create
            # repositories that cannot be written to by rBuilder
            try:
                apacheUID, apacheGUID = os.getpwnam('apache')[2:4]
                os.setuid(apacheUID)
                os.setgid(apacheUID)
                os.setgroups([apacheGID])
                # XXX stubbed temporarily
                # rmake_setup.setupRmake(cfg, config.RBUILDER_RMAKE_CONFIG)
                log.info("rMake repository setup -- need to restart rmake and rmake-node services")
                restartNeeded = True
            except RmakeRepositoryExistsError:
                log.warn("rMake Repository already exists, skipping")
            except Exception, e:
                log.error("Unexpected error occurred when attempting to create the rMake repository.")
                return False
        finally:
            # Restore privs to root
            os.setuid(0)
            os.setgid(0)
            os.setgroups([0])

        if restartNeeded:
            rMakeRestartRC = os.system("/sbin/service rmake restart")
            if rMakeRestarRC == 0:
                rMakeNodeRestartRC = os.system("/sbin/service rmake-node restart")
            if rMakeRestartRC != 0 or rMakeNodeRestartRC != 0:
                log.warn("Failed to restart rMake services. You may need to reboot " \
                         "the appliance for changes to take effect.")

        return True

    def setupExternalProjects(self, schedId, execId):
        """
        Sets up a set of canned external projects.
        """
        # TODO: implement me
        return True
