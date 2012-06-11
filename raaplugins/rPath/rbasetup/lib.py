#
# Copyright (C) 2008-2009 rPath, Inc.
# All rights reserved
#

import logging

from mint import config

log = logging.getLogger('raa.server.rbasetup')

(FTS_STEP_INITIAL, FTS_STEP_ADMINACCT, FTS_STEP_RMAKE, FTS_STEP_ENTITLE,
        FTS_STEP_INITEXTERNAL, FTS_STEP_COMPLETE) = range(6)

def readRBAConfig(configFileName):
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
                 "Using default values!" % str(e))
    return cfg

def writeRBAGeneratedConfig(newCfg, generatedConfigFileName):
    """
    Writes the generated configuration file.
    """
    try:
        newCfg.writeGeneratedConfig(generatedConfigFileName)
        log.info("Wrote new generated configuration to %s" %
                generatedConfigFileName)
        return True
    except Exception, e:
        log.error("Failed to write configuration to %s, reason %s" %
                (generatedConfigFileName, str(e)))
        return False


def getRBAConfiguration():
    """
    Reads the configuration file and returns only the items that
    can be configured by the first-time setup (defined in
    mint.config.keysForGeneratedConfig).

    Returns a double: the first is whether or not this rBuilder has
    been configured. The second is a dict of configurable options,
    as a key/value pair.
    """
    cfg = readRBAConfig(config.RBUILDER_CONFIG)
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
