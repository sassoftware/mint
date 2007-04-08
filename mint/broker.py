#!/usr/bin/python
#
# Copyright (c) 2007 rPath, Inc.
#
# All rights reserved
#

import os, sys
import httplib
import optparse
import pwd
import simplejson
import time

from mcp import client as mcp_client
from mcp import queue
from mcp import jobstatus

from mint import config as mint_config
from mint import shimclient
from mint import database

from conary.lib import util

timestamp = lambda x: '%s: %s' % (time.strftime(time.ctime()), x)

def handleImages(mcpCfg, mintCfg):
    # ensure schema is upgraded
    mintClient = shimclient.ShimMintClient(mintCfg, (mintCfg.authUser,
                                                     mintCfg.authPass))
    mcpClient = mcp_client.MCPClient(mcpCfg)

    queueName = '%s.%s' % (mintCfg.hostName, mintCfg.externalDomainName)

    postQueue = queue.Queue(mcpCfg.queueHost, mcpCfg.queuePort,
                            queueName, timeOut = None)

    print  timestamp("Subscribed to %s on %s:%s" % (queueName,
                     mcpCfg.queueHost, mcpCfg.queuePort))

    try:
        while True:
            data = simplejson.loads(postQueue.read())
            uuid = data.get('uuid')
            urlMap = data.get('urls')
            print timestamp("Received: %s, %s" % (str(uuid), str(urlMap)))
            buildId = int(uuid.split('-')[-1])
            try:
                build = mintClient.getBuild(buildId)
            except database.ItemNotFound:
                print timestamp("Build ID: %s not found. skipping" % buildId)
                continue
            try:
                project = mintClient.getProject(build.projectId)
            except database.ItemNotFound:
                print timestamp("Project ID: %s not found. skipping" % \
                                    build.projectId)
                continue
            finalDir = \
                os.path.join(mintCfg.imagesPath, project.hostname, str(buildId))
            util.mkdirChain(finalDir)
            try:
                for url, fileDesc in urlMap:
                    filePath = os.path.join( \
                        finalDir, httplib.urlsplit(url)[2].split('/')[-1])
                    print timestamp("downloading %s to %s" % (url, filePath))
                    util.execute('curl --create-dirs -o %s %s' % \
                                     (filePath, url))
            except RuntimeError:
                print timestamp("Curl couldn't download images. skipping")
                continue
            print timestamp('setting build metadata for %s' % uuid)
            build.setFiles(urlMap)
            print timestamp('Stopping job %s' % uuid)
            mcpClient.stopJob(uuid)
            print timestamp('Completed handling of %s' % uuid)
    finally:
        mcpClient.disconnect()
        postQueue.disconnect()

def redirIO(outputFn, inputFn = os.devnull):
    input = os.open(inputFn, os.O_RDONLY)
    output = os.open(outputFn, os.O_WRONLY | os.O_CREAT)
    os.dup2(output, sys.stdout.fileno())
    os.dup2(output, sys.stderr.fileno())
    os.dup2(input, sys.stdin.fileno())
    os.close(input)
    os.close(output)

def daemon(func, *args, **kwargs):
    pid = os.fork()
    if not pid:
        os.setsid()
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
    if options.user:
        newUid = pwd.getpwnam(options.user)[2]
    else:
        newUid = curUid

    if (newUid != curUid):
        os.setuid(newUid)
    if not os.getuid():
        parser.error("Don't run this daemon as superuser.")

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
        redirIO(os.path.join(mintCfg.dataPath, 'logs', 'image-broker.log'))
        daemon(handleImages, mcpCfg, mintCfg)
    else:
        handleImages(mcpCfg, mintCfg)

if __name__ == '__main__':
    main()
