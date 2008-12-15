#
# Copyright (C) 2008 rPath, Inc.
# All rights reserved
#
from raa.modules import raasrvplugin
from raaplugins.services.srv import services

from mint import config

log = logging.getLogger('raa.server.rbasetup')

class rBASetup(services.Services):
    """
    Plugin for the backend work of the rBuilder Appliance Setup plugin.
    """

    def __init__(self, *args, **kwargs):
        raasrvplugin.rAASrvPlugin.__init__(self, *args, **kwargs)
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
        log.info('Writing new configuration to %s' % configFileName)

        # Create a new configuration object to store the new values in
        newCfg = config.MintConfig()
        for n, v in newValues:
            if n in newCfg: newCfg[key] = v

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
        for n, v in cfg.iteritems():
            # make safe for XMLRPC
            if not v: v = ''
            docstring = cfg[n].__doc__ or ''
            configurableOptions[n] = (v, docstring)
        return isConfigured, configurableOptions

    def updateRBAConfig(self, schedId, execId, newValues):
        """
        Updates the generated configuration file. Expects a
        dictionary of name value pairs to update.
        """
        return self._writeGeneratedConfigFile(config.RBUILDER_GENERATED_CONFIG,
                newValues)


