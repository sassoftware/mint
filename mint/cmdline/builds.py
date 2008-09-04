#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import os, sys
import time
import textwrap
import urlparse
import socket

from mint import buildtemplates
from mint import buildtypes
from mint import jobstatus
from mint import urltypes
from mint import data
from mint.mint_error import *
from mint.cmdline import commands

from conary.lib import options, log
from conary.conaryclient import cmdline
from conary import conarycfg
from conary import conaryclient

def waitForBuild(client, buildId, interval = 30, timeout = 0, quiet = False):
    try:
        build = client.getBuild(buildId)
    except socket.timeout:
        log.info("Timeout while creating build")
        return 2

    st = time.time()
    timedOut = False
    dropped = 0
    lastMessage = ''
    lastStatus = -1
    jobStatus = {}

    while True:
        try:
            jobStatus = build.getStatus()
            dropped = 0
        except socket.timeout:
            dropped += 1
            if dropped >= 3:
                log.info("Connection timed out (3 attempts)")
                return 2
            log.info("Status request timed out, trying again")
            time.sleep(interval)
            continue

        if lastMessage != jobStatus['message'] or lastStatus != jobStatus['status']:
            if not quiet:
                log.info("Job status: %s (%s)" % (jobstatus.statusNames[jobStatus['status']], jobStatus['message']))
            st = time.time() # reset timeout counter if status changes
            lastMessage = jobStatus['message']
            lastStatus = jobStatus['status']

        if timeout and time.time() - st > timeout:
            timedOut = True
            break

        if jobStatus['status'] not in (jobstatus.WAITING, jobstatus.RUNNING):
            break

        time.sleep(interval)

    if timedOut:
        log.info("Job timed out (%d seconds)" % timeout)
        log.info("Last status: %s (%s)" % (jobstatus.statusNames[jobStatus['status']], jobStatus['message']))
        return 2
    else:
        log.info("Job ended with '%s' status: %s" % (jobstatus.statusNames[jobStatus['status']], jobStatus['message']))
        return jobStatus['status'] != jobstatus.FINISHED


bootableTypes = [buildtypes.RAW_FS_IMAGE,
                 buildtypes.TARBALL,
                 buildtypes.RAW_HD_IMAGE,
                 buildtypes.VMWARE_IMAGE,
                 buildtypes.VMWARE_ESX_IMAGE,
                 buildtypes.VIRTUAL_IRON,
                 buildtypes.VIRTUAL_PC_IMAGE,
                 buildtypes.XEN_OVA,
                 ]

deprecatedTypes = [buildtypes.STUB_IMAGE,
                   buildtypes.NETBOOT_IMAGE,
                   buildtypes.PARALLELS,
                   ]

def genHelp():
    h = "<project name> <troveSpec> <build type>\n\n"

    h += "Available build types:\n\n"

    # reverse validBuildTypes mapping to get the short names
    revMap = dict((x[1], x[0]) for x in buildtypes.validBuildTypes.iteritems())

    for buildType, name in buildtypes.typeNames.iteritems():
        if buildType in deprecatedTypes:
            continue
        h += "%20s\t%s\n" % (revMap[buildType].lower(), name.decode("ascii", "ignore"))
    h += "\n"

    settingSet = []
    for buildType in bootableTypes:
        settingSet.append(set(buildtemplates.dataTemplates[buildType].keys()))

    commonOpts = settingSet[0]
    for x in settingSet:
        commonOpts &= x

    h += "Settings for --option='KEY VALUE':\n\n"
    h += "  Common settings for %s" % ", ".join(revMap[x].lower() for x in bootableTypes)
    h += ":\n"

    for setting, info in buildtemplates.dataTemplates[buildtypes.RAW_HD_IMAGE].items():
        if setting in commonOpts:
            h += "    %-15s\t%s" % (setting, info[2])
            if info[1]:
                h += " (default: %s)" % info[1]
            h += "\n"
    h += "\n"

    for buildType, name, settings in buildtemplates.getDisplayTemplates():
        if buildType in deprecatedTypes:
            continue
        if not set(settings.keys()) - commonOpts:
            continue
        h += "  %s:\n" % name.decode("ascii", "ignore")
        for setting, info in settings.items():
            if buildType in bootableTypes and setting in commonOpts:
                continue
            h += "    %-15s\t%s" % (setting, "\n\t\t\t".join(textwrap.wrap(info[2])))
            if info[1]:
                h += " (default: %s)" % info[1]
            h += "\n"
        h += "\n"

    h += "Note: all build types may not be supported by all rBuilder servers."
    return h

class BuildCreateCommand(commands.RBuilderCommand):
    commands = ['build-create']
    paramHelp = genHelp()

    docs = {'wait' :    'wait until a build job finishes',
            'option':   ('set a build option', '\'KEY VALUE\''),
            'timeout' : ('time to wait before ending, even if the job is not done', 'seconds'),
            'quiet':    'suppress job status output',
            'name':     'set a build name',
            'build-notes': 'set build notes',
            'build-notes-file': 'set build notes from a file',
    }

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM
         argDef["option"] = options.MULT_PARAM
         argDef["timeout"] = options.ONE_PARAM
         argDef["quiet"] = options.NO_PARAM
         argDef["name"] = options.ONE_PARAM
         argDef["build-notes"] = options.ONE_PARAM
         argDef["build-notes-file"] = options.ONE_PARAM

    def runCommand(self, client, cfg, argSet, args):
        wait = argSet.pop('wait', False)
        timeout = int(argSet.pop('timeout', 0))
        quiet = argSet.pop('quiet', False)
        args = args[1:]
        if len(args) < 3:
            return self.usage()
        if 'option' not in argSet:
            argSet['option'] = []

        projectName, troveSpec, buildType = args

        # parse --option parameters
        if buildType.upper() not in buildtypes.validBuildTypes:
            raise RuntimeError, "%s is not a valid build type. See --help." % buildType.upper()

        buildTypeId = buildtypes.validBuildTypes[buildType.upper()]
        buildOptions = dict(tuple(x.split(" ", 1)) for x in argSet['option'])

        for x in buildOptions:
            if x not in buildtemplates.dataTemplates[buildTypeId]:
                raise RuntimeError, "%s is not a valid option fer %s. See --help." % (x, buildType.upper())

        if 'build-notes' in argSet and 'build-notes-file' in argSet:
            raise RuntimeError('--build-notes and --build-notes-file may not'
                'be used together.')

        project = client.getProjectByHostname(projectName)
        build = client.newBuild(project.id, project.name)

        # set name and build notes
        if 'name' in argSet:
            build.setName(argSet['name'])
        if 'build-notes' in argSet:
            build.setDesc(argSet['build-notes'])
        elif 'build-notes-file' in argSet:
            fn = argSet['build-notes-file']
            if os.path.exists(fn):
                build.setDesc(open(fn).read())
            else:
                raise RuntimeError('Release notes file "%s" does not exist.'
                    % fn)

        # resolve a trovespec
        cfg = conarycfg.ConaryConfiguration(True)
        cfg.initializeFlavors()

        cc = conaryclient.ConaryClient(cfg)
        nc = cc.getRepos()

        n, v, f = nc.findTrove(None, cmdline.parseTroveSpec(troveSpec), cc.cfg.flavor)[0]

        if not (n and v and f is not None):
            raise RuntimeError, "Please specify a full trove spec in the form: <trove name>=<version>[<flavor>]\n" \
                "All parts must be fully specified. Use conary rq --full-versions --flavors <trove name>\n" \
                "to find a valid trove spec."

        buildTroveVersion = v.freeze()
        buildTroveFlavor = f.freeze()
        build.setTrove(n, buildTroveVersion, buildTroveFlavor)
        build.setBuildType(buildTypeId)

        template = buildtemplates.dataTemplates[buildTypeId]
        for name in list(template):
            if template[name][0] == data.RDT_TROVE:
                if name in buildOptions:
                    val = buildOptions[name]
                    if val != "NONE":
                        n2, v2, f2 = cmdline.parseTroveSpec(str(val))
                        val = project.resolveExtraTrove(name,
                                buildTroveVersion, buildTroveFlavor,
                                v2, f2)
                else:
                    # not specified at all, resolve it ourselves from just the name
                    val = project.resolveExtraTrove(name, buildTroveVersion, buildTroveFlavor)
                if val:
                    print "Setting %s to %s" % (name, val)
                    buildOptions[name] = val

        for name, val in buildOptions.iteritems():
            build.setDataValue(name, val)

        job = client.startImageJob(build.id)
        print "BUILD_ID=%d" % (build.id)
        sys.stdout.flush()
        if wait:
            return waitForBuild(client, build.id, timeout = timeout, quiet = quiet)
        return 0 # success

commands.register(BuildCreateCommand)

def buildProdDefHelp():
    msg = '<product name> <version name> <stage name>\n'
    return msg

class BuildCreateFromProdDefCommand(commands.RBuilderCommand):
    commands = ['build-product']
    paramHelp = buildProdDefHelp()

    docs = {'force' : 'Continue running builds in the definition even if a previous one failed.',
            'wait' : 'wait until a build job finishes',
            'timeout' : ('time to wait before ending, even if the job is not done', 
                         'seconds'),
            'quiet':    'suppress job status output',
    }


    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM
         argDef["timeout"] = options.ONE_PARAM
         argDef["quiet"] = options.NO_PARAM
         argDef["force"] = options.NO_PARAM

    def runCommand(self, client, cfg, argSet, args):
        wait = argSet.pop('wait', False)
        timeout = int(argSet.pop('timeout', 0))
        quiet = argSet.pop('quiet', False)
        force = argSet.pop('force', False)

        if len(args) < 4:
            return self.usage()

        productName = args[1]
        versionName = args[2]
        stageName = args[3]

        project = client.getProjectByHostname(productName)
        versionList = client.getProductVersionListForProduct(project.id)
        # Pick the version id that matches versionName
        versionId = [v[0] for v in versionList if v[2] == versionName][0]

        try:
            buildIds = client.newBuildsFromProductDefinition(versionId, stageName,
                                                         force)
        except TroveNotFoundForBuildDefinition, tnf:
            print "\n" +str(tnf) + "\n"
            print "To submit the partial set of builds, re-run this command with --force"
            return 1

        for buildId in buildIds:
            print "BUILD_ID=%d" % (buildId)
            sys.stdout.flush()
            if wait:
                waitForBuild(client, buildId, timeout=timeout, quiet=quiet)

        return 0

commands.register(BuildCreateFromProdDefCommand)

class BuildWaitCommand(commands.RBuilderCommand):
    commands = ['build-wait']
    paramHelp = "<build id>"

    docs = {
        'timeout' : ('time to wait before ending, even if the job is not done', 'seconds'),
    }

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["timeout"] = options.ONE_PARAM

    def runCommand(self, client, cfg, argSet, args):
        timeout = int(argSet.pop('timeout', 0))
        args = args[1:]
        if len(args) < 1:
            return self.usage()

        buildId = int(args[0])
        return waitForBuild(client, buildId, timeout = timeout)
commands.register(BuildWaitCommand)


class BuildUrlCommand(commands.RBuilderCommand):
    commands = ['build-url']
    paramHelp = "<build id>"

    def runCommand(self, client, cfg, argSet, args):
        args = args[1:]
        if len(args) < 1:
            return self.usage()

        buildId = int(args[0])
        build = client.getBuild(buildId)

        # extract the downloadImage url from the serverUrl configuration
        parts = urlparse.urlparse(cfg.serverUrl)

        for file in build.getFiles():
            for urlId, urlType, url in file['fileUrls']:
                if urlType == urltypes.AMAZONS3TORRENT:
                    urlBase = "http://%s/%s/downloadTorrent?fileId=%%d" % \
                        (parts[1].split('@')[1], os.path.normpath(parts[2] + "../")[1:])
                else:
                    urlBase = "http://%s/%s/downloadImage?fileId=%%d" % \
                        (parts[1].split('@')[1], os.path.normpath(parts[2] + "../")[1:])
                print urlBase % (file['fileId'])
        return 0
commands.register(BuildUrlCommand)
