#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from conary import conarycfg

from mint.django_rest import timeutils
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.packages import errors
from mint.django_rest.rbuilder.packages import models

from mint.rmake3_package_creator import models as rmakemodels
from mint.rmake3_package_creator import client 

exposed = basemanager.exposed

class BaseManager(basemanager.BaseManager):
    @exposed
    def getConaryConfig(self):
        cfg = conarycfg.ConaryConfiguration(readConfigFiles=False)
        cfg.configLine('name %s' % self.user.fullname)
        cfg.configLine('contact %s' % self.user.email)
        # TODO: figure how to set the host
        host = "127.0.0.1"
        #cfg.configLine("includeConfigFile https://%s/conaryrc" % host)
        cfg.configLine('user * %s %s' % (self.cfg.authUser, self.cfg.authPass))
        return cfg

class PackageManager(BaseManager):
    
    @exposed
    def getPackages(self):
        Packages = models.Packages()
        Packages.package = models.Package.objects.all()
        return Packages
    
    @exposed
    def getPackage(self, package_id):
        package = models.Package.objects.get(pk=package_id)
        return package
        
    @exposed
    def addPackage(self, package):
        package.save()
        package.created_by = self.user
        package.modified_by = self.user
        return package
        
    @exposed
    def updatePackage(self, package_id, package):
        package.modified_by = self.user
        package.save()
        return package
    
    @exposed
    def deletePackage(self, package_id):
        package = models.Package.objects.get(
            pk=package_id)
        package.delete()

    def downloadPackageVersionUrl(self, packageVersionUrl):
        pass

    def buildPackageSource(self, packageSource):
        pass

    def promotePackageSource(self, packageSource):
        pass

    def commitPackageVersion(self, packageVersion):
        pass

    def promotePackageBuild(self, packageBuild):
        pass


class PackageVersionManager(BaseManager):
    
    @exposed
    def getAllPackageVersions(self):
        packageVersions = models.AllPackageVersions()
        packageVersions.package_version = models.PackageVersion.objects.all()
        return packageVersions

    @exposed
    def getPackagePackageVersions(self, package_id):
        package = models.Package.objects.get(pk=package_id)
        packageVersions = models.PackageVersions()
        packageVersions.package_version = \
            models.PackageVersion.objects.filter(package=package)
        packageVersions._parents = [package]
        return packageVersions

    @exposed
    def getPackageVersion(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        return packageVersion

    @exposed
    def getPackageVersionUrls(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageVersionUrls = models.PackageVersionUrls()
        packageVersionUrls.package_version_url = \
            models.PackageVersionUrl.objects.filter(package_version=packageVersion)
        packageVersionUrls._parents = [packageVersion]
        return packageVersionUrls

    @exposed
    def getPackageVersionUrl(self, package_version_id,
                             package_version_url_id):
        packageVersionUrl = models.PackageVersionUrl.objects.get(
            pk=package_version_url_id)
        return packageVersionUrl

    @exposed
    def addPackageVersionUrl(self, package_version_id, package_version_url):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        package_version_url.package_version = packageVersion
        package_version_url.save()
        return package_version_url

    @exposed
    def updatePackageVersionUrls(self, package_version_id,
                                 package_version_urls):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageVersion.package_version_urls.all().delete()
        for pvUrl in package_version_urls.package_version_url:
            pvUrl.package_version = packageVersion
            pvUrl.downloaded_date = timeutils.now()
            pvUrl.modified_by = self.user
            pvUrl.save()

        analyzeActionType = self.getPackageActionTypeByName(
            models.PackageActionType.ANALYZE)
        packageVersionAction, created = packageVersion.actions.get_or_create(
            package_action_type=analyzeActionType)
        packageVersionAction.enabled = True
        packageVersionAction.visible = False
        packageVersionAction.save()

        self.analyzeFiles(package_version_id)

        return self.getPackageVersionUrls(package_version_id)

    @exposed
    def analyzeFiles(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        analyzeActionType = self.getPackageActionTypeByName(
            models.PackageActionType.ANALYZE)
        packageVersionJob = models.PackageVersionJob(
            package_version=packageVersion,
            package_action_type=analyzeActionType)
        return self.addPackageVersionJob(package_version_id, packageVersionJob)

    def _dispatchAnalyzeJob(self, package_version_job):
        return
        filePaths = [u.file_path \
            for u in package_version_job.package_version.package_version_urls \
            if u.file_path is not None] # pyflakes=ignore

        commitActionType = self.getPackageActionTypeByName(
            models.PackageActionType.COMMIT)
        packageVersionAction = models.PackageVersionAction.objects.get(
            package_version=package_version_job.package_version,
            package_action_type=commitActionType)
        repeaterClient = client.Client()
        resultsLocation = repeaterClient.ResultsLocation(
            path=packageVersionAction.get_absolute_url()) # pyflakes=ignore

        params = rmakemodels.FileParams()
        job_uuid, job = repeaterClient.pc_analyzeFiles(params) 
        inventoryJob = jobmodels.Job(job_uuid=job_uuid,
            job_state=jobmodels.JobState.objects.get(
                name=jobmodels.JobState.RUNNING))
        inventoryJob.save()
        package_version_job.job = inventoryJob
        package_version_job.save()

        return inventoryJob

    @exposed
    def getPackageVersionAction(self, package_version_action_id):
        packageAction = models.PackageVersionAction.objects.get(
            pk=package_version_action_id)
        return packageAction

    @exposed
    def updatePackageVersionAction(self, package_version_id, package_action):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        package_action.package_version = packageVersion
        package_action.save()

        canCommit = True
        for pvUrl in packageVersion.package_version_urls.all():
            if not pvUrl.file_path:
                canCommit = False

        if canCommit:
            commitActionType = self.getPackageActionTypeByName(
                models.PackageActionType.COMMIT)
            packageVersionAction, created = packageVersion.actions.get_or_create(
                package_action_type=commitActionType)
            packageVersionAction.enabled = True
            packageVersionAction.save()

        return package_action

    @exposed
    def getPackageVersionJobs(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageVersionJobs = models.PackageVersionJobs()
        packageVersionJobs.package_version_job = \
            models.PackageVersionJob.objects.filter(package_version=packageVersion)
        packageVersionJobs._parents = [packageVersion]
        return packageVersionJobs

    @exposed
    def getPackageVersionJob(self, package_version_job_id):
        packageVersionJob = models.PackageVersionJob.objects.get(
            pk=package_version_job_id)
        return packageVersionJob

    @exposed
    def addPackageVersionJob(self, package_version_id, package_version_job):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        enabledAction = packageVersion.actions.filter(enabled=True,
            package_action_type=package_version_job.package_action_type)
        if not enabledAction:
            raise errors.PackageActionNotEnabled(
                packageActionTypeName=package_version_job.package_action_type.name)
        package_version_job.package_version = packageVersion
        package_version_job.created_by = self.user
        package_version_job.modified_by = self.user
        package_version_job.save()
        self.dispatchPackageVersionJob(package_version_job)
        return package_version_job

    def dispatchPackageVersionJob(self, package_version_job):
        if package_version_job.package_action_type.name == \
            models.PackageActionType.DOWNLOAD:
            return self._dispatchDownloadJob(package_version_job)
        if package_version_job.package_action_type.name == \
            models.PackageActionType.COMMIT:
            return self._dispatchCommitJob(package_version_job)
        if package_version_job.package_action_type.name == \
            models.PackageActionType.ANALYZE:
            return self._dispatchAnalyzeJob(package_version_job)

    def _dispatchCommitJob(self, package_version_job):
        # TODO: get these from the descriptor data
        label = 'murftest.eng.rpath.com@rpath:murftest-1-devel'
        factory = 'capsule-rpm-pc=/centos.rpath.com@rpath:centos-5-common/1.0-1-1'

        packageName = str(package_version_job.package_version.package.name)
        packageVersion = str(package_version_job.package_version.name)

        packageSources = package_version_job.package_version.package_sources.model()
        resultsLocation = packageSources.get_absolute_url(
            parents=[package_version_job.package_version], 
            view_name="PackageSources")

        repeaterClient = client.Client()

        job_uuid, job = repeaterClient.pc_packageSourceCommit(
            packageName, packageVersion, label, factory, self.cfg.authUser,
            self.cfg.authPass, self.user.email, resultsLocation)
        
        inventoryJob = jobmodels.Job(job_uuid=job_uuid,
            job_state=jobmodels.JobState.objects.get(
                name=jobmodels.JobState.RUNNING))
        inventoryJob.save()
        package_version_job.job = inventoryJob
        package_version_job.save()

        return inventoryJob

    def _dispatchDownloadJob(self, package_version_job):
        urls = [u.url for u in 
            package_version_job.package_version.package_version_urls.all()]
        resultsLocation = package_version_job.package_version.get_absolute_url() + '/urls'

        repeaterClient = client.Client()
        job_uuid, job = repeaterClient.pc_downloadFiles(urls, resultsLocation)

        inventoryJob = jobmodels.Job(job_uuid=job_uuid,
            job_state=jobmodels.JobState.objects.get(
                name=jobmodels.JobState.RUNNING))
        inventoryJob.save()
        package_version_job.job = inventoryJob
        package_version_job.save()

        return inventoryJob

    def getPackageActionTypeByName(self, actionName):
        return models.PackageActionType.objects.get(name=actionName)

    @exposed
    def getPackageActionTypes(self):
        packageActionTypes = models.PackageActionTypes()
        packageActionTypes.package_action_type = \
            models.PackageActionType.objects.all()
        return packageActionTypes

    @exposed
    def getPackageActionType(self, package_action_type_id):
        return models.PackageActionType.objects.get(pk=package_action_type_id)

    @exposed
    def addPackageVersion(self, package_id, package_version):
        package = models.Package.objects.get(pk=package_id)
        package_version.package = package
        package_version.save()

        # New package actions are download, commit, and analyze
        commitActionType = self.getPackageActionTypeByName(
            models.PackageActionType.COMMIT)
        downloadActionType = self.getPackageActionTypeByName(
            models.PackageActionType.DOWNLOAD)
        analyzeActionType = self.getPackageActionTypeByName(
            models.PackageActionType.ANALYZE)
        commitVersionAct = models.PackageVersionAction(
            package_version=package_version,
            package_action_type=commitActionType,
            visible=True,
            enabled=False)
        downloadVersionAct = models.PackageVersionAction(
            package_version=package_version,
            package_action_type=downloadActionType,
            visible=True,
            enabled=True)
        analyzeVersionAct = models.PackageVersionAction(
            package_version=package_version,
            package_action_type=analyzeActionType,
            visible=False,
            enabled=False)

        commitVersionAct.save()
        downloadVersionAct.save()
        analyzeVersionAct.save()

        return package_version
        
    @exposed
    def updatePackageVersion(self, package_version_id, package_version):
        package_version.save()
        return package_version
        
    @exposed
    def deletePackageVersion(self, package_version_id):
        packageversion = models.PackageVersion.objects.get(
            pk=package_version_id)
        packageversion.delete()

    @exposed
    def getPackageSources(self, package_version_id):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageSources = models.PackageSources()
        packageSources.package_source = \
            models.PackageSource.objects.filter(package_version=packageVersion)
        packageSources._parents = [packageVersion]
        return packageSources

    @exposed
    def getPackageSource(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        return packageSource

    @exposed
    def addPackageSource(self, package_version_id, package_source):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        package_source.package_version = packageVersion
        package_source.trove.version.save()
        package_source.trove.version = package_source.trove.version
        package_source.trove.save()
        package_source.trove = package_source.trove
        package_source.save()
        
        buildAction = self.getPackageActionTypeByName(
            models.PackageActionType.BUILD)
        buildSourceAct = models.PackageSourceAction(
            package_source=package_source,
            package_action_type=buildAction,
            visible=True,
            enabled=True)
        buildSourceAct.save()

        return package_source

    @exposed
    def updatePackageSources(self, package_version_id, package_sources):
        packageVersion = models.PackageVersion.objects.get(pk=package_version_id)
        packageVersion.package_sources.all().delete()

        for packageSource in package_sources.package_source:
            self.addPackageSource(package_version_id, packageSource)
        
        return self.getPackageSources()

    @exposed
    def getPackageSourceJobs(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        packageSourceJobs = models.PackageSourceJobs()
        packageSourceJobs.package_source_job = \
            models.PackageSourceJob.objects.filter(package_source=packageSource)
        packageSourceJobs._parents = [packageSource]
        return packageSourceJobs

    @exposed
    def getPackageSourceJob(self, package_source_job_id):
        packageSourceJob = models.PackageSourceJob.objects.get(
            pk=package_source_job_id)
        return packageSourceJob

    @exposed
    def addPackageSourceJob(self, package_source_id, package_source_job):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        package_source_job.package_source = packageSource
        package_source_job.save()
        self.dispatchPackageSourceJob(package_source_job)
        return package_source_job

    def dispatchPackageSourceJob(self, package_source_job):
        pass

    @exposed
    def getPackageBuilds(self, package_source_id):
        packageSource = models.PackageSource.objects.get(pk=package_source_id)
        packageBuilds = models.PackageBuilds()
        packageBuilds.package_build = \
            models.PackageBuild.objects.filter(package_source=packageSource)
        packageBuilds._parents = [packageSource]
        return packageBuilds

    @exposed
    def getPackageBuild(self, package_build_id):
        packageBuild = models.PackageBuild.objects.get(pk=package_build_id)
        return packageBuild

    @exposed
    def getPackageBuildJobs(self, package_build_id):
        packageBuild = models.PackageBuild.objects.get(pk=package_build_id)
        packageBuildJobs = models.PackageBuildJobs()
        packageBuildJobs.package_build_job = \
            models.PackageBuildJob.objects.filter(package_build=packageBuild)
        packageBuildJobs._parents = [packageBuild]
        return packageBuildJobs

    @exposed
    def getPackageBuildJob(self, package_build_job_id):
        packageBuildJob = models.PackageBuildJob.objects.get(
            pk=package_build_job_id) 
        return packageBuildJob

    def _dispatchJob(self):
        pass

