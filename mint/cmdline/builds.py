#
# Copyright (c) 2005-2006 rPath, Inc.
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
from mint.cmdline import commands

from conary import versions
from conary.lib import options, log
from conary.conaryclient.cmdline import parseTroveSpec


def waitForBuild(client, buildId, interval = 5):
    build = client.getBuild(buildId)
    job = build.getJob()

    while job.status in (jobstatus.WAITING, jobstatus.RUNNING):
        time.sleep(interval)
        job.refresh()

    log.info("Job ended with '%s' status: %s" % (jobstatus.statusNames[job.status], job.statusMessage))

def genHelp():
    h = "<project name> <troveSpec> <build type>\n\n"

    h += "Available build types:\n\n"

    # reverse validBuildTypes mapping to get the short names
    revMap = dict((x[1], x[0]) for x in buildtypes.validBuildTypes.iteritems())

    for buildType, name in buildtypes.typeNames.iteritems():
        h += "%20s\t%s\n" % (revMap[buildType].lower(), name.decode("ascii", "ignore"))
    h += "\n"

    # pull out all of the common bootable image settings
    bootableTypes = [buildtypes.RAW_FS_IMAGE,
                     buildtypes.TARBALL,
                     buildtypes.RAW_HD_IMAGE,
                     buildtypes.VMWARE_IMAGE]
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
        if buildType in [buildtypes.STUB_IMAGE, buildtypes.NETBOOT_IMAGE]:
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

    docs = {'wait' : 'wait until a build job finishes',
            'option': ('set a build option', '\'KEY VALUE\''),
    }

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM
         argDef["option"] = options.MULT_PARAM

    def runCommand(self, client, cfg, argSet, args):
        wait = argSet.pop('wait', False)
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

        n, v, f = parseTroveSpec(troveSpec)
        if not (n and v and f is not None):
            raise RuntimeError, "Please specify a full trove spec in the form: <trove name>=<version>[<flavor>]\n" \
                "All parts must be fully specified. Use conary rq --full-versions --flavors <trove name>\n" \
                "to find a valid trove spec."

        v = versions.VersionFromString(v, timeStamps = [0.0])
        v.resetTimeStamps([0.0])
        build.setTrove(n, v.freeze(), f.freeze())

        build.setBuildType(buildTypeId)

        for name, val in buildOptions.iteritems():
            build.setDataValue(name, val)

        job = client.startImageJob(build.id)
        print "BUILD_ID=%d" % (build.id)
        sys.stdout.flush()
        if wait:
            waitForBuild(client, build.id)
        return build.id
commands.register(BuildCreateCommand)


class BuildWaitCommand(commands.RBuilderCommand):
    commands = ['build-wait']
    paramHelp = "<build id>"

    def runCommand(self, client, cfg, argSet, args):
        args = args[1:]
        if len(args) < 1:
            return self.usage()

        buildId = int(args[0])
        waitForBuild(client, buildId)
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
                sys.stdout.flush()
commands.register(BuildUrlCommand)
