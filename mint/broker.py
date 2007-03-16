#!/usr/bin/python
#
# Copyright (c) 2007 rPath, Inc.
#
# All rights reserved
#

import os, sys
import pwd
import optparse
import httplib

from mcp import client as mcp_client
from mcp import queue
from mcp import jobstatus

from mint import config as mint_config
from mint import shimclient

from conary import dbstore

def handleImages(mcpCfg, mintCfg):
    # ensure schema is upgraded
    mintClient = shimclient.ShimMintClient(mintCfg, (mintCfg.authUser,
                                                     mintCfg.authPass))
    mcpClient = mcp_client.MCPClient(mcpCfg)

    queueName = '%s.%s' % (mintCfg.hostName, mintCfg.externalDomainName)

    postQueue = queue.Queue(mcpCfg.queueHost, mcpCfg.queuePort,
                            queueName, timeOut = None)

    db = dbstore.connect(mintCfg.dbPath, mintCfg.dbDriver)
    cu = db.cursor()
    isogenUid = os.geteuid()
    apacheGid = pwd.getpwnam('apache')[3]
    try:
        while True:
            uuid, urlMap = postQueue.read()
            buildId = int(uuid.split('-')[-1])
            build = mintClient.getBuild(buildId)
            project = mintClient.getProject(build.projectId)
            finalDir = \
                os.path.join(mintCfg.imagesPath, project.hostname, str(buildId))
            os.chown(finalDir, isogenUid, apacheGid)
            os.chmod(finalDir, os.stat(finalDir)[0] & 0777 | 0020)
            os.chown(pardir, isogenUid, apacheGid)
            os.chmod(pardir, os.stat(pardir)[0] & 0777 | 0020)
            for url, fileDesc in urlMap:
                filePath = os.path.join(finalDir, httplib.urlsplit(url)[2].split('/')[-1])
                os.system('curl --create-dirs -o %s %s' % (filePath, url))
                os.chown(filePath, isogenUid, apacheGid)
                os.chmod(filePath, os.stat(newfile)[0] & 0777 | 0020)
            build.setFiles(urlMap)
            client.stopJob(uuid)
    finally:
        mcpClient.disconnect()
        postQueue.disconnect()

def daemon(func, *args, **kwargs):
    pid = os.fork()
    if not pid:
        os.setsid()
        devnull = os.open(os.devnull, os.O_RDWR)
        os.dup2(devnull, sys.stdout.fileno())
        os.dup2(devnull, sys.stderr.fileno())
        os.dup2(devnull, sys.stdin.fileno())
        pid = os.fork()
        if not pid:
            func(*args, **kwargs)

def main(envArgs = sys.argv[1:]):
    parser = optparse.OptionParser()

    parser.add_option("-n", "--no-daemon", dest = "daemon", default = True,
                      action = "store_false",
                      help = "don't daemonize. go into debug mode")

    parser.add_option("-c", "--config", dest = 'config',
                      help = "location of rBuilder config file", default = '')

    parser.add_option("-m", "--mcp-config", dest = "mcp_config",
                      help = "location of mcp client config file",
                      default = '/srv/rbuilder/config/mcp-client.conf')

    parser.add_option("-u", '--user', dest = 'user',
                      help = 'run as specific user. must be superuser.',
                      default = None)

    (options, args) = parser.parse_args(envArgs)

    # drop privileges as early as possible
    curUid = os.geteuid()
    newUid = pwd.getpwnam(options.user)[2]
    if (newUid != curUid):
        os.seteuid(newUid)

    mintCfg = mint_config.MintConfig()
    if not options.config:
        mintCfg.read(mint_config.RBUILDER_CONFIG)
        mintCfg.read(mint_config.RBUILDER_GENERATED_CONFIG)
        mintCfg.read(mint_config.RBUILDER_GENERATED_CONFIG.replace('generated',
                                                                   'custom'))
    else:
        mintCfg.read(options.config)

    mcpCfg = mcp_client.MCPClientConfig()
    mcpCfg.read(options.mcp_config)

    if options.daemon:
        daemon(handleImages, mcpCfg, mintCfg)
    else:
        handleImages(mcpCfg, mintCfg)

if __name__ == '__main__':
    main()
