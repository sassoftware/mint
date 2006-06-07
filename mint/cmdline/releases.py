#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import time

from mint import releasetypes
from mint import jobstatus
from mint.cmdline import commands

from conary import versions
from conary.lib import options, log
from conary.conaryclient.cmdline import parseTroveSpec


def waitForRelease(client, releaseId, interval = 5):
    release = client.getRelease(releaseId)
    job = release.getJob()

    while job.status in (jobstatus.WAITING, jobstatus.RUNNING):
        time.sleep(interval)
        job.refresh()

    log.info("Job ended with '%s' status: %s" % (jobstatus.statusNames[job.status], job.statusMessage))


class ReleaseCreateCommand(commands.RBuilderCommand):
    commands = ['release-create']
    paramHelp = "<project name> <troveSpec> <image type>"

    docs = {'wait' : 'wait until a release job finishes'}

    def addParameters(self, argDef):
         commands.RBuilderCommand.addParameters(self, argDef)
         argDef["wait"] = options.NO_PARAM

    def runCommand(self, client, cfg, argSet, args):
        wait = argSet.pop('wait', False)
        args = args[1:]
        if len(args) < 3:
            return self.usage()

        projectName, troveSpec, imageType = args
        project = client.getProjectByHostname(projectName)
        release = client.newRelease(project.id, project.name)

        n, v, f = parseTroveSpec(troveSpec)
        assert(n and v and f is not None)
        v = versions.VersionFromString(v)
        v.resetTimeStamps(0)
        release.setTrove(n, v.freeze(), f.freeze())

        assert(imageType.upper() in releasetypes.validImageTypes)
        release.setImageTypes([releasetypes.validImageTypes[imageType.upper()]])

        job = client.startImageJob(release.id)
        log.info("Release %d job started (job id %d)." % (release.id, job.id))
        if wait:
            waitForRelease(client, release.id)
        return release.id
commands.register(ReleaseCreateCommand)


class ReleaseWaitCommand(commands.RBuilderCommand):
    commands = ['release-wait']
    paramHelp = "<release id>"

    def runCommand(self, client, cfg, argSet, args):
        args = args[1:]
        if len(args) < 1:
            return self.usage()

        releaseId = int(args[0])
        waitForRelease(client, releaseId)
commands.register(ReleaseWaitCommand)
