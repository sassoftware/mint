# copyright rPath, Inc. 2007
# All rights reserved

# this is temporary code designed to help 3.1.x to 4.0 migration
# this module will monitor 3.1 series jobs table and insert the same jobs into
# rBuilder 4.0 for migration testing
# once MCP code is on rBO, this module should be removed.

import StringIO
import os, sys
import simplejson
import sha

import mint
import mint.builds
import mint.config

import mcp
import mcp.client
import mcp.jobstatus

import time
epoch = time.time()

from conary import dbstore

cfg = mint.config.MintConfig()
cfg.read(mint.config.RBUILDER_CONFIG)
cfg.read(mint.config.RBUILDER_GENERATED_CONFIG)

mc = mint.client.MintClient("http://%s:%s@%s.%s/xmlrpc-private/" % (cfg.authUser, cfg.authPass, cfg.hostName, cfg.siteDomainName))

db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

mcpConfig = mcp.client.MCPClientConfig()
mcpConfig.read('/srv/rbuilder/config/mcp-client.conf')
mcpClient = mcp.client.MCPClient(mcpConfig)

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

    p = os.popen('hostname')
    hostname = p.read().strip()

    r['outputUrl'] = 'http://%s:31337/' % hostname
    r['outputToken'] = sha.new(os.urandom(20)).hexdigest()

    return simplejson.dumps(r)

def processBuild(buildId):
    try:
        data = serializeBuild(buildId)
        jobId = mcpClient.submitJob(data)
        done = False
        while not done:
            status, statusMessage = mcpClient.jobStatus(jobId)
            print "status:", statusMessage + chr(13),
            done = status in (mcp.jobstatus.FINISHED, mcp.jobstatus.FAILED)
    except:
        exc_cl, exc, bt = sys.exc_info()
        print exc

def getBuilds(cutoff):
    cu = db.cursor()
    cu.execute("SELECT timeSubmitted, Jobs.buildId FROM Jobs INNER JOIN BuildsView ON BuildsView.buildId=Jobs.buildId WHERE timeSubmitted>?", cutoff)
    res = cu.fetchall()
    if res:
        return max(x[0] for x in res), [x[1] for x in res]
    else:
        return cutoff, []

def main():
    cutoff = epoch
    while True:
        cutoff, builds = getBuilds(cutoff)
        print "new cutoff timestamp %i" % cutoff
        for buildId in builds:
            print "processing %i" % buildId
            processBuild(buildId)
        if not builds:
            print "no builds to process"
            time.sleep(5)

if __name__ == '__main__':
    pid = os.fork()
    if not pid:
        os.execlp('make', 'make', 'run')
    try:
        main()
    finally:
        import signal
        os.kill(pid, signal.SIGINT)
