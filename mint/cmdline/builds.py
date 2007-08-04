#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
import os, sys
import time
import textwrap
import urlparse

from mint import buildtemplates
from mint import buildtypes
from mint import jobstatus
from mint import urltypes
from mint import data
from mint.cmdline import commands

from conary import versions
from conary.lib import options, log
from conary.conaryclient import cmdline
from conary import conarycfg
from conary import conaryclient
from conary import errors

# Fallback in case we have no other choice
RPL = versions.Label("conary.rpath.com@rpl:1")

def waitForBuild(client, buildId, interval = 30, timeout = 0, quiet = False):
    build = client.getBuild(buildId)
    jobStatus = build.getStatus()

    st = time.time()
    timedOut = False
    lastMessage = ''
    lastStatus = -1
    while jobStatus['status'] in (jobstatus.WAITING, jobstatus.RUNNING):
        if lastMessage != jobStatus['message'] or lastStatus != jobStatus['status']:
            if not quiet:
                log.info("Job status: %s (%s)" % (jobstatus.statusNames[jobStatus['status']], jobStatus['message']))
            st = time.time() # reset timeout counter if status changes
            lastMessage = jobStatus['message']
            lastStatus = jobStatus['status']

        if timeout and time.time() - st > timeout:
            timedOut = True
            break

        time.sleep(interval)
        jobStatus = build.getStatus()

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
                 buildtypes.VIRTUAL_PC_IMAGE,]

deprecatedTypes = [buildtypes.STUB_IMAGE,
                   buildtypes.NETBOOT_IMAGE,
                   buildtypes.XEN_OVA,
                   buildtypes.PARALLELS]

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


def resolveExtraTrove(cclient, trvName, trvVersion = None, trvFlavor = None, searchPath = []):
    spec = cmdline.parseTroveSpec(trvName)
    itemList = [(spec[0], (None, None), (spec[1], spec[2]), True)]
    try:
        uJob, suggMap = cclient.updateChangeSet(itemList,
                                                resolveDeps = False)

        job = [x for x in uJob.getPrimaryJobs()][0]
        strSpec = '%s=%s[%s]' % (job[0], str(job[2][0]),
                                 str(job[2][1]))

        return strSpec
    except errors.TroveNotFound:
        log.warning("Trove not found for %s" % trvName)
        return None

def getLabelPath(cclient, trove):
    """Retrieve label path from group for anaconda-templates resolution."""
    repos = cclient.getRepos()
    trv = repos.getTroves([trove])
    return [versions.Label(x) for x in trv[0].getTroveInfo().labelPath]


class BuildCreateCommand(commands.RBuilderCommand):
    commands = ['build-create']
    paramHelp = genHelp()

    docs = {'wait' :    'wait until a build job finishes',
            'option':   ('set a build option', '\'KEY VALUE\''),
            'timeout' : ('time to wait before ending, even if the job is not done', 'seconds'),
            'quiet':    'suppress job status output',
    }

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM
         argDef["option"] = options.MULT_PARAM
         argDef["timeout"] = options.ONE_PARAM
         argDef["quiet"] = options.NO_PARAM

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
        buildOptions = dict(tuple(x.split(" ")) for x in argSet['option'])

        for x in buildOptions:
            if x not in buildtemplates.dataTemplates[buildTypeId]:
                raise RuntimeError, "%s is not a valid option for %s. See --help." % (x, buildType.upper())

        project = client.getProjectByHostname(projectName)
        build = client.newBuild(project.id, project.name)

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

        build.setTrove(n, v.freeze(), f.freeze())
        build.setBuildType(buildTypeId)

        # resolve extra troves
        searchPath = [build.getTroveVersion().branch().label()]
        template = buildtemplates.dataTemplates[buildTypeId]
        for name in list(template):
            if template[name][0] == data.RDT_TROVE:

                # we have to handle anaconda-templates differently because
                # it's not likely that they will have a build on the group's
                # label, but we don't want to accidently pull in any other
                # extra troves from different labels.
                if name == "anaconda-templates":
                    cc.cfg.installLabelPath = getLabelPath(cc, (n, v, f)) + [RPL]
                else:
                    cc.cfg.installLabelPath = searchPath
                # set on the command line, perhaps partially
                if name in buildOptions:
                    val = buildOptions[name]
                    if val != "NONE":
                        n, v, f = parseTroveSpec(str(val))
                        val = resolveExtraTrove(cc, v, f, searchPath)
                else:
                    # not specified at all, resolve it ourselves from just the name
                    val = resolveExtraTrove(cc, name, searchPath = searchPath)
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
