# copyright rPath, Inc. 2007
# All rights reserved

# this is temporary code designed to help 3.1.x to 4.0 migration
# this module will monitor 3.1 series jobs table and insert the same jobs into
# rBuilder 4.0 for migration testing
# once MCP code is on rBO, this module should be removed.

import StringIO
import os
import simplejson
import mint
import mint.builds
import mint.config

cfg = mint.config.MintConfig()
cfg.read(mint.config.RBUILDER_CONFIG)
cfg.read(mint.config.RBUILDER_GENERATED_CONFIG)

mc = mint.client.MintClient("http://%s:%s@%s.%s/xmlrpc-private/" % (cfg.authUser, cfg.authPass, cfg.hostName, cfg.siteDomainName))


def serializeBuild(buildId):
    build = mc.getBuild(buildId)
    project = mc.getProject(build.projectId)

    cc = project.getConaryConfig()
    cc.entitlementDirectory = os.path.join(cfg.dataPath, 'entitlements')
    cc.readEntitlementDirectory()

    # Ignore conaryProxy set by getConaryConfig; it's bound
    # to be localhost, as getConaryConfig() generates
    # config objects intended to be used by NetClient /
    # ConaryClient objects internal to rBuilder (i.e. not the
    # jobslaves)
    cc.conaryProxy = None

    cfgBuffer = StringIO.StringIO()
    cc.display(cfgBuffer)
    cfgData = cfgBuffer.getvalue().split("\n")

    allowedOptions = ['repositoryMap', 'user', 'conaryProxy', 'entitlement']
    cfgData = "\n".join([x for x in cfgData if x.split(" ")[0] in allowedOptions])

    if cfg.createConaryRcFile:
        cfgData += "\nincludeConfigFile http://%s%s/conaryrc\n" % \
            (cfg.siteHost, cfg.basePath)

    r = {}
    r['serialVersion'] = mint.builds.SERIAL_VERSION
    r['type'] = 'build'

    for key in ('name', 'troveName', 'troveVersion', 'troveFlavor',
                  'description', 'buildType'):
        r[key] = build.__getattribute__(key)

    r['data'] = build.getDataDict()

    r['project'] = {'name' : project.name,
                    'hostname' : project.hostname,
                    'label' : project.getLabel(),
                    'conaryCfg' : cfgData}

    hostBase = '%s.%s' % (cfg.hostName, cfg.externalDomainName)
    r['UUID'] = '%s-build-%d' % (hostBase, buildId)

    r['outputUrl'] = 'FIXME'

    return simplejson.dumps(r)

