#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#
import errno
import os
import sys
import tempfile
import deps
import flavorcfg
import repository
import versions
from build import use

sys.path.insert(0, "/home/tgerla/cvs/darby/client/")
from buildsystem import distro

import conarycfg
from conarycfg import ConfigFile

from imagegen import ImageGenerator

class IsoConfig(ConfigFile):
    defaults = {
        'productPath':       'Specifix',
        'productName':       'Specifix Linux',
        'productPrefix':     'spx',
        'templatePath':      None,
        'nfsPath':           None,
        'tftpbootPath':      None,
    }

class InstallableIso(ImageGenerator):
    def getIsoConfig(self):
        isocfg = IsoConfig()
        isocfg.read("installable_iso.conf")
        return isocfg

    def write(self):
        isocfg = self.getIsoConfig()
    
        profileId = self.job.getProfileId()

        name, projectId = self.client.server.getProfile(profileId)
        trove, versionStr, frozenFlavor = self.client.server.getTrove(profileId)
        flavor = deps.deps.ThawDependencySet(frozenFlavor)

        project = self.client.getProject(projectId)

        ccfg = project.getConaryConfig()

        flavorConfig = flavorcfg.FlavorConfig(ccfg.useDirs, ccfg.archDirs)
        ccfg.flavor = flavorConfig.toDependency(override=ccfg.flavor)
        insSet = deps.deps.DependencySet()
        for dep in deps.arch.currentArch:
            insSet.addDep(deps.deps.InstructionSetDependency, dep)
        ccfg.flavor.union(insSet)
        ccfg.buildFlavor = ccfg.flavor.copy()
        flavorConfig.populateBuildFlags()
        use.setBuildFlagsFromFlavor(None, ccfg.buildFlavor, error=None)
       
        repos = repository.netclient.NetworkRepositoryClient(ccfg.repositoryMap)

        jobId = self.job.getId()
        releaseVer = self.client.getJobData(jobId, "releaseVer")
        releasePhase = self.client.getJobData(jobId, "releasePhase")

        arch = self.job.getArch()
        assert(arch in ('x86', 'x86_64'))
 
        distroInfo = distro.DistroInfo(isocfg.productPrefix,
                                       isocfg.productPath,
                                       isocfg.productName,
                                       releaseVer, releasePhase,
                                       arch = arch)
        version = versions.VersionFromString(versionStr)
       
        # XXX remove this and pass version as soon as darby can handle a full ver
        label = version.branch().label()
      
        tmpDir = self.cfg.imagesPath + os.path.join(arch, releasePhase)
        dist = distro.Distribution(arch, repos, ccfg,
                                   distroInfo, (trove, version.asString(), flavor),
                                   tmpDir, tmpDir+"/isos/", isocfg.templatePath,
                                   isocfg.nfsPath, isocfg.tftpbootPath, None,
                                   None, False)
                                   
        try:
            os.makedirs(self.cfg.logPath)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
             
        logfile = os.path.join(self.cfg.logPath, "instiso-%d.log" % jobId)
        self.redirectOutput(logfile)
        try:
            dist.prep()
            filenames = dist.create()
        except:
            self.resetOutput()
            raise
        self.resetOutput()
         
        return filenames

    def redirectOutput(self, logFile):
        logfd = os.open(logFile, os.O_TRUNC | os.O_WRONLY | os.O_CREAT)
        self.stdout = os.dup(sys.stdout.fileno())
        self.stderr = os.dup(sys.stderr.fileno())
        os.dup2(logfd, sys.stdout.fileno())
        os.dup2(logfd, sys.stderr.fileno())
        os.close(logfd)
    
    def resetOutput(self):
        os.dup2(self.stdout, sys.stdout.fileno())
        os.dup2(self.stderr, sys.stderr.fileno())
