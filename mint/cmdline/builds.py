#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import time

from mint import buildtypes
from mint import jobstatus
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


class BuildCreateCommand(commands.RBuilderCommand):
    commands = ['build-create']
    paramHelp = "<project name> <troveSpec> <image type>"

    docs = {'wait' : 'wait until a build job finishes'}

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM

    def runCommand(self, client, cfg, argSet, args):
        wait = argSet.pop('wait', False)
        args = args[1:]
        if len(args) < 3:
            return self.usage()

        projectName, troveSpec, buildType = args
        project = client.getProjectByHostname(projectName)
        build = client.newBuild(project.id, project.name)

        n, v, f = parseTroveSpec(troveSpec)
        assert(n and v and f is not None)
        v = versions.VersionFromString(v)
        v.resetTimeStamps(0)
        build.setTrove(n, v.freeze(), f.freeze())

        assert(buildType.upper() in buildtypes.validBuildTypes)
        build.setBuildType(buildtypes.validBuildTypes[buildType.upper()])

        job = client.startImageJob(build.id)
        log.info("Build %d job started (job id %d)." % (build.id, job.id))
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
