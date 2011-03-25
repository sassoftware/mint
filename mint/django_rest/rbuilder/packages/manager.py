#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import datetime
from dateutil import tz
import urlparse

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.packages import errors
from mint.django_rest.rbuilder.packages import models

from mint.rmake3_package_creator import models as rmakemodels
from mint.rmake3_package_creator import client 

exposed = basemanager.exposed

class PackageManager(basemanager.BaseManager):
    """docstring for PackageManager"""
    
    @exposed
    def getPackages(self):
        """docstring for getPackage"""
        Packages = models.Packages()
        Packages.package = models.Package.objects.all()
        return Packages
    
    @exposed
    def getPackage(self, package_id):
        """docstring for Package"""
        package = models.Package.objects.get(pk=package_id)
        return package
        
    @exposed
    def addPackage(self, package):
        """docstring for addPackage"""
        package.save()
        package.created_by = self.user
        package.modified_by = self.user
        return package
        
    @exposed
    def updatePackage(self, package_id, package):
        """docstring for updatePackage"""
        package.modified_by = self.user
        package.save()
        return package
    
    @exposed
    def deletePackage(self, package_id):
        """docstring for deletePackage"""
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


class PackageVersionManager(basemanager.BaseManager):
    
    @exposed
    def getAllPackageVersions(self):
        packageVersions = models.AllPackageVersions()
        packageVersions.package_version = models.PackageVersion.objects.all()
        return packageVersions

    @exposed
    def getPackagePackageVersions(self, package_id):
        """docstring for getPackageVersions"""
        package = models.Package.objects.get(pk=package_id)
        packageVersions = models.PackageVersions()
        packageVersions.package_version = \
            models.PackageVersion.objects.filter(package=package)
        packageVersions._parents = [package]
        return packageVersions

    @exposed
    def getPackageVersion(self, package_version_id):
        """docstring for getPackageVersion"""
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
        canCommit = True
        for pvUrl in package_version_urls.package_version_url:
            pvUrl.package_version = packageVersion
            if not pvUrl.file_path:
                canCommit = False
            pvUrl.downloaded_date = datetime.datetime.now(tz.tzutc())
            pvUrl.modified_by = self.user
            pvUrl.save()

        if canCommit:
            commitActionType = self.getPackageActionTypeByName(
                models.PackageActionType.COMMIT)
            packageVersionAction, created = packageVersion.actions.get_or_create(
                package_action_type=commitActionType)
            packageVersionAction.enabled = True
            packageVersionAction.save()

        return self.getPackageVersionUrls(package_version_id)

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

    def _dispatchDownloadJob(self, package_version_job):
        urls = []
        for url in package_version_job.package_version.package_version_urls.all():
            path = "/tmp/%s" % urlparse.urlparse(url.url).path.split('/')[-1]
            urls.append(rmakemodels.DownloadFile(url=str(url.url),
                path=path))

        repeaterClient = client.Client()
        resultsLocation = repeaterClient.ResultsLocation(
            path=str(package_version_job.package_version.get_absolute_url()) + \
            '/urls')
        params = rmakemodels.DownloadFilesParams()
        params.urlList = urls
        params.resultsLocation = resultsLocation
        job_uuid, job = repeaterClient.pc_downloadFiles(params)

        inventoryJob = inventorymodels.Job(job_uuid=job_uuid,
            job_state=inventorymodels.JobState.objects.get(
                name=inventorymodels.JobState.RUNNING))
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
        """docstring for addPackageVersion"""
        package = models.Package.objects.get(pk=package_id)
        package_version.package = package
        package_version.save()

        # New package actions are download and commit
        commitAction = self.getPackageActionTypeByName(
            models.PackageActionType.COMMIT)
        downloadAction = self.getPackageActionTypeByName(
            models.PackageActionType.DOWNLOAD)
        commitVersionAct = models.PackageVersionAction(
            package_version=package_version,
            package_action_type=commitAction,
            visible=True,
            enabled=False)
        downloadVersionAct = models.PackageVersionAction(
            package_version=package_version,
            package_action_type=downloadAction,
            visible=True,
            enabled=True)

        commitVersionAct.save()
        downloadVersionAct.save()

        return package_version
        
    @exposed
    def updatePackageVersion(self, package_version_id, package_version):
        """docstring for updatePackageVersion"""
        package_version.save()
        return package_version
        
    @exposed
    def deletePackageVersion(self, package_version_id):
        """docstring for deletePackageVersion"""
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
