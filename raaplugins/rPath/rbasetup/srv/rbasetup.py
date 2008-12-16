#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved
#
import logging
import os

from raa.modules.raasrvplugin import rAASrvPlugin

from mint import config
from conary.lib.cfgtypes import CfgBool

log = logging.getLogger('raa.server.rbasetup')

class rBASetup(rAASrvPlugin):
    """
    Plugin for the backend work of the rBuilder Appliance Setup plugin.
    """

    def __init__(self, *args, **kwargs):
        rAASrvPlugin.__init__(self, *args, **kwargs)
        self.config = self.server.getConfigData()

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

        # Create a new configuration object to store the new values in
        newCfg = config.MintConfig()
        for k, v in newValues.iteritems():
            if k in newCfg: newCfg[k] = v

        # Ensure that configured is True
        newCfg.configured = True

        # Write the file
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
            f.close()

        return True

    def getRBAConfiguration(self, schedID, execId):
        """
        Reads the configuration file and returns only the items that
        can be configured by the first-time setup (defined in
        mint.config.keysForGeneratedConfig).

        Returns a double: the first is whether or not this rBuilder has
        been configured. The second is a dict of configurable options,
        each of whose values is also a double: the value, along with a
        docstring for the configuration value.
        """
        cfg = self._readConfigFile(config.RBUILDER_CONFIG)
        isConfigured = cfg.configured
        configurableOptions = dict()
        for k in config.keysForGeneratedConfig:
            if k not in cfg:
                continue
            v = cfg[k]
            # make safe for XMLRPC
            if v == None: v = ''
            docstring = cfg._options[k].__doc__ or k
            configurableOptions[k] = (v, docstring, isinstance(cfg._options[k].valueType, CfgBool))
        return isConfigured, configurableOptions

    def updateRBAConfig(self, schedId, execId, newValues):
        """
        Updates the generated configuration file. Expects a
        dictionary of name value pairs to update.
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

