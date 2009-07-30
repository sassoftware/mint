#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import email
import os
import re
import sys
import time
from mint.web import basictroves
from mint import communitytypes
from mint import mailinglists
from mint.db import jobs
from mint import jobstatus
from mint import builds
from mint import buildtypes
from mint import userlevels
from mint.mint_error import *

from mint import buildtemplates
from mint import helperfuncs
from mint.helperfuncs import getProjectText
from mint.lib.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
from mint.logerror import logWebErrorAndEmail
from mint.lib.maillib import sendMailWithChecks
from mint.web import productversion
from mint.web.packagecreator import PackageCreatorMixin
from mint.web.fields import strFields, intFields, listFields, boolFields, dictFields
from mint.web.webhandler import WebHandler, normPath, HttpNotFound, \
     HttpForbidden
from mint.web.decorators import ownerOnly, writersOnly, requiresAuth, \
        requiresAdmin, mailList, redirectHttp

from conary import conaryclient
from conary import conarycfg
from conary.deps import deps
from conary import versions
from conary.conaryclient.cmdline import parseTroveSpec
from conary.errors import TroveNotFound, ParseError

from mcp import mcp_error

from rpath_common.proddef import api1 as proddef

import simplejson

def getUserDict(members):
    users = { userlevels.USER: [],
              userlevels.DEVELOPER: [],
              userlevels.OWNER: [], }
    for userId, username, level in members:
        users[level].append((userId, username,))
    return users

class BaseProjectHandler(WebHandler, productversion.ProductVersionView):

    def handle(self, context):
        self.__dict__.update(**context)

        cmds = self.cmd.split("/")

        try:
            self.project = self.client.getProjectByHostname(cmds[0])
        except ItemNotFound:
            raise HttpNotFound

        self.userLevel = self.project.getUserLevel(self.auth.userId)
        self.isOwner  = (self.userLevel == userlevels.OWNER) or self.auth.admin
        self.isWriter = (self.userLevel in userlevels.WRITERS) or self.auth.admin
        self.isReader = (self.userLevel in userlevels.READERS) or self.auth.admin

        #Take care of hidden projects
        if self.project.hidden and self.userLevel == userlevels.NONMEMBER and not self.auth.admin:
            raise HttpNotFound

        self.handler_customizations(context)

        # add the project name to the base path
        self.basePath += "project/%s" % (cmds[0])
        self.basePath = normPath(self.basePath)

        self.setupView()

        if not cmds[1]:
            return self.index
        try:
            method = self.__getattribute__(cmds[1])
        except AttributeError:
            raise HttpNotFound

        if not callable(method):
            raise HttpNotFound

        return method

    def handler_customizations(self, context):
        """ Override this if necessary """

    def _predirect(self, path = "", temporary = False):
        self._redirectHttp('project/%s/%s' % (self.project.hostname, path),
                temporary=temporary)

    def help(self, auth):
        return self._write("help")

class ProjectHandler(BaseProjectHandler, PackageCreatorMixin):
    def handler_customizations(self, context):
        # go ahead and fetch the release / commits data, too
        self.projectReleases = [self.client.getPublishedRelease(x) for x in self.project.getPublishedReleases()]
        self.projectPublishedReleases = [x for x in self.projectReleases if x.isPublished()]
        self.projectUnpublishedReleases = [x for x in self.projectReleases if not x.isPublished()]
        self.projectCommits =  self.project.getCommits()
        if self.projectPublishedReleases:
            self.latestPublishedRelease = self.projectPublishedReleases[0]
            self.latestBuildsWithFiles = [self.client.getBuild(x) for x in self.latestPublishedRelease.getBuilds() if self.client.getBuild(x).getFiles()]
        else:
            self.latestPublishedRelease = None
            self.latestBuildsWithFiles = []

    @redirectHttp
    def projectPage(self, auth):
        if self.auth.admin:
            # various bits of logic to figure out if we should prompt for
            # mirror preloading

            # already mirrored?
            mirrored = bool(self.client.getInboundMirror(self.project.id))

            # anonymous external projects can't be mirrored
            _, _, userMap, entMap = self.client.getLabelsForProject(
                                                                self.project.id)
            anonymous = len(userMap) == 0 and len(entMap) == 0
        else:
            mirrored = False
            anonymous = False
        if self.cfg.VAMUser:
            vmtnId = self.client.getCommunityId(self.project.getId(), 
                                                communitytypes.VMWARE_VAM)
        else:
            vmtnId = None
            
        if self.project.external:
            external = True
        else:
            external = False

        return self._write("projectPage", mirrored = mirrored, 
                           anonymous = anonymous, vmtnId = vmtnId,
                           external = external)
    index = projectPage

    def releases(self, auth):
        return self._write("pubreleases")

    @writersOnly
    def builds(self, auth):
        builds = [self.client.getBuild(x) for x in self.project.getBuilds()]
        publishedReleases = dict()
        for build in builds:
            if build.getPublished() and \
                    build.pubReleaseId not in publishedReleases:
                publishedReleases[build.pubReleaseId] = \
                        self.client.getPublishedRelease(build.pubReleaseId)

        return self._write("builds", builds = builds, publishedReleases = publishedReleases)

    @writersOnly
    def groups(self, auth):
        # leave this here until old UI is completely removed
        return self._write("groups")

    @writersOnly
    @productversion.productVersionRequired
    def newBuildsFromProductDefinition(self, auth):
        return self._write("newBuildsFromProductDefinition")

    @strFields(action = "cancel", productStageName = None)
    @boolFields(force = False)
    @dictFields(yesArgs = None)
    @writersOnly
    @productversion.productVersionRequired
    def processNewBuildsFromProductDefinition(self, auth, productStageName, action, force, **yesArgs):

        if action.lower() == 'cancel':
            self._predirect('builds')

        try:
            self.client.newBuildsFromProductDefinition(self.currentVersion,
                    productStageName, force)
        except TroveNotFoundForBuildDefinition, tnffbd:
            return self._write("confirm",
                    message = "Some builds will not be built because of the following errors: %s. Continue?" % ', '.join(tnffbd.errlist),
                    yesArgs = { 'func': 'processNewBuildsFromProductDefinition',
                                'productStageName': productStageName,
                                'action': 'submit',
                                'force': '1'},
                    noLink = "builds")
        except Exception, e:
            logWebErrorAndEmail(self.req, self.cfg, *sys.exc_info())
            self._addErrors("Problem encountered when creating build(s): %s" % str(e))
            self._predirect('newBuildsFromProductDefinition')
        else:
            self._setInfo("Builds created.")
            self._predirect('builds')


    @writersOnly
    def newBuild(self, auth):
        return self._write("editBuild",
            buildId = None,
            name = self.project.getName(),
            desc = "",
            buildType = buildtypes.INSTALLABLE_ISO,
            templates = buildtemplates.getDisplayTemplates(),
            dataDict = {},
            troveName = None,
            label = None,
            versionStr = None,
            version = None,
            flavor = None,
            arch = None,
            visibleTypes = self.client.getAvailableBuildTypes(),
            kwargs = {})

    @writersOnly
    @intFields(buildId = -1)
    @strFields(action = "Edit Image")
    def editBuild(self, auth, buildId, action):

        if action == "Edit Image":
            build = self.client.getBuild(buildId)

            troveName, versionStr, flavor = build.getTrove()
            version = versions.ThawVersion(versionStr)
            label = version.branch().label()
            thawedFlavor = deps.ThawFlavor(flavor)
            arch = helperfuncs.getArchFromFlavor(thawedFlavor)

            return self._write("editBuild",
                buildId = buildId,
                name = build.getName(),
                desc = build.getDesc(),
                buildType = build.getBuildType(),
                templates = buildtemplates.getDisplayTemplates(),
                dataDict = build.getDataDict(),
                troveName = troveName,
                label = label,
                version = version,
                flavor = thawedFlavor,
                arch = arch,
                visibleTypes = self.client.getAvailableBuildTypes(),
                kwargs = {})
        elif action == "Recreate Image":
            try:
                job = self.client.startImageJob(buildId)
            except mcp_error.JobConflict:
                pass
            self._predirect("build?id=%d" % buildId)
        else:
            self._addErrors("Invalid action %s" % action)
            self._predirect("build?id=%d" % buildId)


    @writersOnly
    @intFields(buildId = None)
    @strFields(distTroveSpec = "", name = "", desc = "", action = "save")
    def saveBuild(self, auth, buildId, distTroveSpec, name, desc, action, **kwargs):

        if action == "Cancel":
            if buildId:
                self._predirect("build?id=%d" % buildId)
            else:
                self._predirect("builds")

        # Various javascript corner cases may allow the user to submit
        # without a group trove.
        if not distTroveSpec:
            self._addErrors("You must select a group from which to "
                    "build your image.")
            self._predirect("newBuild")
            return

        # check to make sure that we didn't lose buildtype at some point
        # this condition isn't perfect because it loses state and forces
        # the user to redo their build setup, so we should figure out why
        # we are actually losing the buildtype (maybe if javascript is turned
        # off), and fix that, too.
        if 'buildtype' not in kwargs:
            self._addErrors("You cannot save this build because a build type has "
                "not been chosen. Please fix this error and try again.")
            self._predirect("newBuild")
            return

        if not buildId:
            try:
                build = self.client.newBuild(self.project.id, name)
            except NotEntitledError:
                self._addErrors('The build could not retrieve an appropriate '
                    'jobslave because rBuilder is not correctly entitled.')
                self._predirect('newBuild')
                return
            buildId = build.id
        else:
            build = self.client.getBuild(buildId)

        # enforce that job doesn't conflict
        res = build.getStatus()
        jobStatus, msg = res['status'], res['message']
        if jobStatus not in (jobstatus.NO_JOB, jobstatus.FINISHED,
                             jobstatus.FAILED):
            self._addErrors("You cannot alter this image because a "
                            "conflicting image is currently being generated.")
            self._predirect("build?id=%d" % buildId)
            return

        distTroveName, distTroveVersion, distTroveFlavor = parseTroveSpec(distTroveSpec)
        build.setTrove(distTroveName, distTroveVersion, distTroveFlavor.freeze())
        build.setName(name)
        build.setDesc(desc)

        jobArch = helperfuncs.getArchFromFlavor(distTroveFlavor)

        # handle buildType check box state changes
        buildType = int(kwargs['buildtype'])
        build.setBuildType(buildType)

        # convert any python variable-name-safe trove spec parameters to the
        # real data value name (they end in Spec, and have - translated to _)
        specRe = re.compile("([a-zA-Z\-]+)_(\d+)Spec")
        for key in kwargs.keys()[:]:
            m = specRe.match(key)
            if not m:
                continue

            newKey, kwBuildType = m.groups()

            # only match values for this build type
            if buildType == int(kwBuildType):
                kwargs.update({newKey: str(kwargs[key])})
                del kwargs[key]

        # get the template from the build and handle any relevant args
        # remember that checkboxes don't pass args for unchecked boxxen
        template = build.getDataTemplate()

        # validate the template options
        try:
            template.validate(**kwargs)
        except BuildOptionValidationException, e:
            self._addErrors(str(e))
            self._predirect("editBuild?buildId=%d" % build.id)
            return

        buildTroveVersion = build.getTroveVersion().freeze()
        buildTroveFlavor  = build.getTroveFlavor().freeze()

        for name in list(template):
            try:
                val = kwargs[name]
                if template[name][0] == RDT_BOOL:
                    val = True
                if template[name][0] in (RDT_STRING, RDT_ENUM):
                    val = str(val)
                if template[name][0] == RDT_INT:
                    val = int(val)
                if template[name][0] == RDT_TROVE:
                    if val != "NONE":
                        # remove timestamp from version string
                        n, v, f = parseTroveSpec(str(val))
                        if not n or not v or (f is None):
                            # incomplete spec from XMLRPC client
                            val = self.project.resolveExtraTrove(n,
                                buildTroveVersion, buildTroveFlavor,
                                v, f)
                        else:
                            try:
                                # attempt to un-freeze the version
                                versions.ThawVersion(v)
                            except (ValueError, ParseError):
                                # spec with non-frozen version
                                val = self.project.resolveExtraTrove(n,
                                    buildTroveVersion, buildTroveFlavor, v, f)
                            else:
                                # frozen version from picker
                                val = "%s=%s[%s]" % (n, v, f)
            except KeyError:
                if template[name][0] == RDT_BOOL:
                    val = False
                elif template[name][0] == RDT_TROVE:
                    val = self.project.resolveExtraTrove(name,
                            buildTroveVersion, buildTroveFlavor)
                else:
                    val = template[name][1]
            if val:
                build.setDataValue(name, val)

        try:
            self.client.startImageJob(buildId)
        except jobs.DuplicateJob:
            pass

        self._predirect("build?id=%d" % buildId)

    @writersOnly
    @dictFields(yesArgs = {})
    @boolFields(confirmed = False)
    def deleteBuild(self, auth, confirmed, **yesArgs):
        build = self.client.getBuild(int(yesArgs['id']))
        if confirmed:
            build.deleteBuild()
            self._setInfo("Build %s deleted" % build.name)
            self._predirect("builds")
        else:
            message = ""
            if build.pubReleaseId:
                pubRelease = self.client.getPublishedRelease(build.pubReleaseId)
                message += "This image is part of the unpublished release %s (version %s). Deleting the image will automatically remove the image from the release. " % (pubRelease.name, pubRelease.version)
            message += "Are you sure you want to delete this image?"
            return self._write("confirm",
                    message = message,
                    yesArgs = { 'func': 'deleteBuild',
                                'id': yesArgs['id'],
                                'confirmed': '1' },
                    noLink = "builds")

    @writersOnly
    @listFields(int, buildIdsToDelete = [])
    @boolFields(confirmed = False)
    @dictFields(yesArgs = {})
    def deleteBuilds(self, auth, buildIdsToDelete, confirmed, **yesArgs):
        if confirmed:
            buildIds = simplejson.loads(yesArgs['buildIdsJSON'])
            for buildId in buildIds:
                build = self.client.getBuild(int(buildId))
                build.deleteBuild()
            self._setInfo("Images deleted")
            self._predirect("builds")
        else:
            if not buildIdsToDelete:
                self._addErrors("No images specified.")
                self._predirect("builds")
            numToDelete = len(buildIdsToDelete)
            numPublished = 0
            message = ""
            for buildId in buildIdsToDelete:
                build = self.client.getBuild(buildId)
                if build.pubReleaseId:
                    numPublished += 1
            if numPublished:
                message += "One or more of the images you have specified are a part of a release. Deleting these images will automatically remove the images from their corresponding release(s). "

            message += "Are you sure you want to delete these images?"
            # we use JSON to serialize that list because confirm.kid
            # will eat the list.
            return self._write("confirm",
                    message = message,
                    yesArgs = { 'func': 'deleteBuilds',
                                'buildIdsJSON': simplejson.dumps(buildIdsToDelete),
                                'confirmed': 1 },
                    noLink = "builds")

    @intFields(id = None)
    def build(self, auth, id):
        build = self.client.getBuild(id)
        extraFlags = builds.getExtraFlags(build.troveFlavor)
        buildInProgress = False

        if auth.authorized:
            buildInProgress = \
                (build.getStatus()['status'] <= jobstatus.RUNNING)
            showLaunchButton = bool(self.user.getDataDict().get('awsAccountNumber'))
        else:
            showLaunchButton = False

        try:
            trove, version, flavor = build.getTrove()
            versionString = "%s/%s" % \
                (versions.ThawVersion(version).trailingLabel(),
                    versions.ThawVersion(version).trailingRevision())
            files = build.getFiles()

            fileIds = list(set([x['fileId'] for x in files]))

            anacondaVars = {'anaconda-custom':'', 'anaconda-templates':'', 'media-template':''}
            for key in anacondaVars:
                anacondaVars[key] = build.getDataValue(key, validate = False)
                if anacondaVars[key]:
                    if anacondaVars[key] == 'NONE':
                        anacondaVars[key] = ''
                        continue

                    n,v,f = parseTroveSpec(anacondaVars[key])
                    outParts = []

                    if n != key:
                        # Display the name only if it's not the default
                        outParts.append('%s=' % n)

                    if v:
                        # Try to parse the version so that full
                        # ones can be reformatted as a label + rev.
                        vObj = helperfuncs.parseVersion(v)
                        if vObj:
                            outParts.append('%s/%s' % (vObj.trailingLabel(),
                                    vObj.trailingRevision()))
                        else:
                            outParts.append(v)

                    if f is not None and f != deps.Flavor():
                        outParts.append('[%s]' % f)

                    anacondaVars[key] = ''.join(outParts)

            amiId = build.getDataValue('amiId', validate = False)
            amiS3Manifest = build.getDataValue('amiS3Manifest', validate=False)
        except builds.TroveNotSet:
            self._predirect("editBuild?buildId=%d" % build.id)
        else:
            return self._write("build", build = build,
                name = build.getName(),
                files = files,
                fileIds = fileIds,
                trove = trove,
                version = versionString,
                flavor = deps.ThawFlavor(flavor),
                buildId = id,
                projectId = self.project.getId(),
                notes = build.getDesc().strip(),
                buildInProgress = buildInProgress,
                extraFlags = extraFlags,
                amiId = amiId,
                amiS3Manifest = amiS3Manifest,
                anacondaVars = anacondaVars,
                showLaunchButton = showLaunchButton)

    @writersOnly
    @productversion.productVersionRequired
    def newPackage(self, auth):
        uploadDirectoryHandle = self.client.createPackageTmpDir()
        if not self.versions:
            self._addErrors('You must create a product version before using the package creator')
            self._predirect('editVersion', temporary=True)
        return self._write('createPackage', message = '',
                uploadDirectoryHandle = uploadDirectoryHandle,
                sessionHandle=None, name=None)

    @writersOnly
    @strFields(uploadId=None, fieldname=None)
    @boolFields(debug=False)
    def upload_iframe(self, auth, uploadId, fieldname, debug):
        return self._write('uploadPackageFrame', uploadId = uploadId,
                fieldname = fieldname, project = self.project.hostname,
                debug=debug)

    @writersOnly
    @productversion.productVersionRequired
    @strFields(uploadDirectoryHandle=None, upload_url='', sessionHandle='')
    def getPackageFactories(self, auth, uploadDirectoryHandle, upload_url, sessionHandle):
        ret = self._getPackageFactories(uploadDirectoryHandle, self.currentVersion, sessionHandle, upload_url)
        return self._write('createPackageInterview', message=None, **ret)

    @writersOnly
    @strFields(name=None, label=None, prodVer=None, namespace=None)
    def newUpload(self, auth, name, label, prodVer, namespace):
        """"""
        #Start both the upload and the pc sessions
        uploadDirectoryHandle = self.client.createPackageTmpDir()
        sessionHandle = self.client.startPackageCreatorSession(self.project.getId(), prodVer, namespace, name, label)
        return self._write('createPackage', message = '',
                uploadDirectoryHandle = uploadDirectoryHandle,
                sessionHandle=sessionHandle, prodVer=prodVer, namespace=namespace, name=name)

    @writersOnly
    @strFields(name=None, label=None, prodVer=None, namespace=None)
    def maintainPackageInterview(self, auth, name, label, prodVer, namespace):
        """"""
        try:
            sessionHandle, factories, prevChoices = self.client.getPackageFactoriesFromRepoArchive(self.project.getId(), prodVer, namespace, name, label)
            isDefault, recipeContents = self.client.getPackageCreatorRecipe(sessionHandle)

        except MintError, e:
            self._addErrors(str(e))
            self._predirect('newPackage', temporary=True)
        return self._write('createPackageInterview',
                editing = True, sessionHandle = sessionHandle,
                factories = factories, message = None, prevChoices=prevChoices,
                recipeContents = recipeContents,
                useOverrideRecipe = not isDefault)

    @writersOnly
    @strFields(sessionHandle=None, factoryHandle=None, recipeContents='')
    @boolFields(useOverrideRecipe=False)
    def savePackage(self, auth, sessionHandle, factoryHandle, recipeContents, useOverrideRecipe, **kwargs):
        #It is assumed that the package creator service will validate the input
        if not useOverrideRecipe:
            recipeContents = ''
        self.client.savePackageCreatorRecipe(sessionHandle, recipeContents)
        self.client.savePackage(sessionHandle, factoryHandle, kwargs)
        return self._write('buildPackage', sessionHandle = sessionHandle,
                message = None)

    @writersOnly
    @productversion.productVersionRequired
    def packageCreatorPackages(self, auth):
        pkgList = {}
        version = None
        namespace = None
        allPackageCreatorPackagesList = self.client.getPackageCreatorPackages(self.project.getId())
        try:
            ver = self.client.getProductVersion(self.currentVersion)
            version = ver['name']
            namespace = ver['namespace']
            pkgList = dict([x for x in allPackageCreatorPackagesList[ver['name']][ver['namespace']].items() if not x[0].startswith('group-')])
        except KeyError:
            pass # no packages for our namespace / version combo

        return self._write('packageList', pkgList=pkgList, version=version,
                namespace=namespace, message=None)

    @writersOnly
    def sourcePackages(self, auth):
        #This method is not supported, and should not be used
        versionId = self._getCurrentProductVersion()
        pkgList = self.client.getProductVersionSourcePackages(self.project.getId(), versionId)
        pkgList = [(x[0], versions.ThawVersion(x[1])) for x in pkgList]
        return self._write('sourcePackageList', pkgList=pkgList, message=None)

    @writersOnly
    @strFields(troveName=None, troveVersion='')
    def buildSourcePackage(self, auth, troveName, troveVersion):
        #This method is not supported, and should not be used
        versionId = self._getCurrentProductVersion()
        sesH = self.client.buildSourcePackage(self.project.getId(), versionId, troveName, troveVersion)
        return self._write('buildPackage', sessionHandle = sesH,
                message = None)

    @ownerOnly
    def newRelease(self, auth):
        currentBuilds = []
        availableBuilds = [y for y in (self.client.getBuild(x) for x in \
                self.project.getUnpublishedBuilds()) if (y.getFiles() or y.buildType == buildtypes.AMI or y.buildType == buildtypes.IMAGELESS)]

        availableBuilds.sort(lambda x,y: (cmp(x.getTroveVersion(),
                             y.getTroveVersion()) == 0 and \
                             [cmp(x.getBuildType(), y.getBuildType())] or \
                             [cmp(x.getTroveVersion(), 
                              y.getTroveVersion())])[0])
        return self._write("editPubrelease",
                           releaseId = None,
                           name = self.project.name,
                           desc = None,
                           version = None,
                           availableBuilds = availableBuilds,
                           currentBuilds = currentBuilds)

    @ownerOnly
    @intFields(id = None)
    def editRelease(self, auth, id):
        pubrelease = self.client.getPublishedRelease(id)
        currentBuilds = [self.client.getBuild(x) for x in \
                pubrelease.getBuilds()]
        availableBuilds = [y for y in (self.client.getBuild(x) for x in \
                self.project.getUnpublishedBuilds()) if (y.getFiles() or y.buildType == buildtypes.AMI or y.buildType == buildtypes.IMAGELESS)]

        availableBuilds.sort(lambda x,y: (cmp(x.getTroveVersion(),
                             y.getTroveVersion()) == 0 and \
                             [cmp(x.getBuildType(), y.getBuildType())] or \
                             [cmp(x.getTroveVersion(), 
                              y.getTroveVersion())])[0])
        currentBuilds.sort(lambda x,y: (cmp(x.getTroveVersion(),
                             y.getTroveVersion()) == 0 and \
                             [cmp(x.getBuildType(), y.getBuildType())] or \
                             [cmp(x.getTroveVersion(), 
                              y.getTroveVersion())])[0])
        return self._write("editPubrelease",
                           releaseId = id,
                           name = pubrelease.name,
                           desc = pubrelease.description,
                           version = pubrelease.version,
                           availableBuilds = availableBuilds,
                           currentBuilds = currentBuilds)

    @ownerOnly
    @intFields(id = None)
    @strFields(name = '', desc = '', version = '')
    @listFields(int, buildIds = [])
    def saveRelease(self, auth, id, name, desc, version, buildIds):
        currentBuildIds = []
        if not id:
            pubrelease = self.client.newPublishedRelease(self.project.id)
        else:
            pubrelease = self.client.getPublishedRelease(id)
            currentBuildIds = pubrelease.getBuilds()

        # ignore things that are in both before and after sets
        changedIds = set(currentBuildIds) ^ set(buildIds)

        # handle adds and removes
        for b in changedIds:
            # add things that are in the current desired buildIds
            if b in buildIds:
                pubrelease.addBuild(b)
            # delete everything else
            else:
                pubrelease.removeBuild(b)

        # update metadata
        pubrelease.name = name
        pubrelease.description = desc
        pubrelease.version = version

        # ...and save
        pubrelease.save()

        if not id:
            self._setInfo("Created release %s" % name)
        else:
            self._setInfo("Updated release %s" % name)
        self._predirect("releases")

    @ownerOnly
    @dictFields(yesArgs = {})
    @boolFields(confirmed = False)
    def deleteRelease(self, auth, confirmed, **yesArgs):
        if confirmed:
            self.client.deletePublishedRelease(int(yesArgs['id']))
            self._setInfo("Deleted release")
            self._predirect("releases")
        else:
            return self._write("confirm",
                    message = "Are you sure you want to delete this release? All images associated with this release will be put back in the pool of unpublished images.",
                    yesArgs = { 'func': 'deleteRelease',
                                'id': yesArgs['id'],
                                'confirmed': '1' },
                    noLink = "releases")

    def _getLatestVMwareBuild(self, pubrelease):
        buildTypes = pubrelease.getUniqueBuildTypes()
        vmw = False
        for bt in buildTypes:
            if bt[0] in (buildtypes.VMWARE_IMAGE, buildtypes.VMWARE_ESX_IMAGE):
                vmw = True
                break
        if vmw:
            changedTime = 0
            latestBuild = None
            for build in pubrelease.getBuilds():
                bd = self.client.getBuild(build)
                if bd.buildType in (buildtypes.VMWARE_IMAGE, buildtypes.VMWARE_ESX_IMAGE):
                    ct = bd.timeUpdated
                    if ct > changedTime:
                        changedTime = ct
                        latestBuild = bd
        if vmw:
            return latestBuild
        else:
            return None

    def _getPreviewData(self, pubrelease, latestBuild):
        dataDict = {} 
        # Title
        dataDict.update(title=latestBuild.getName())
        # One Line Desc
        if pubrelease.description:
            dataDict.update(oneLiner=pubrelease.description)
        elif latestBuild.getDesc():
            dataDict.update(oneLiner=latestBuild.getDesc())
        else:
            dataDict.update(oneLiner=self.project.getName())
        # Long Description
        if self.project.getDesc():
            dataDict.update(longDesc=self.project.getDesc())
        else:
            dataDict.update(longDesc=self.project.getName())

        return dataDict

    def _getVAMData(self, pubrelease, latestBuild):
        # Get title, one line desc, and long desc
        dataDict = self._getPreviewData(pubrelease, latestBuild) 

        # URL
        dataDict.update(url=self.project.getUrl(self.baseUrl) + 'latestRelease')
        # Memory
        dataDict.update(memory=latestBuild.getDataValue('vmMemory'))
        # Size compressed
        dataDict.update(size=latestBuild.getFiles()[0]['size']/0x100000)
        if dataDict['size'] == '0':
            dataDict['size'] = ''
        # VMware tools installed?
        fl = latestBuild.getTroveFlavor()
        if fl.stronglySatisfies(deps.parseFlavor('use: vmware')):
            dataDict.update(vmtools='1')
        else:
            dataDict.update(vmtools=False)
        # Bit Torrent Available
        dataDict.update(torrent='1')
        # User name
        dataDict.update(userName='root')
        # Password
        dataDict.update(password='')

        # OS 
        dataDict.update(os='rPath Linux')

        # Time
        timeTup = time.gmtime(latestBuild.getChangedTime())
        dataDict.update(year=timeTup[0])
        dataDict.update(month=timeTup[1])
        dataDict.update(day=timeTup[2])
        dataDict.update(hour=timeTup[3])
        dataDict.update(minute=timeTup[4])

        return dataDict

    @ownerOnly
    @dictFields(yesArgs = {})
    @boolFields(confirmed=False, shouldMirror=False)
    @strFields(vmtn = '')
    def publishRelease(self, auth, confirmed, vmtn, shouldMirror, **yesArgs):
        pubrelease = self.client.getPublishedRelease(int(yesArgs['id']))
        if confirmed:
            vmtnError = ''
            if self.cfg.VAMUser and vmtn == 'on':
            # Handle VAM stuff
                build = self._getLatestVMwareBuild(pubrelease)        
                if build:
                    dataDict = self._getVAMData(pubrelease, build)
                    communityId = self.client.getCommunityId(self.project.getId(), communitytypes.VMWARE_VAM)
                    if communityId:
                        try:
                            from mint.web import vmtn
                            v = vmtn.VMTN()
                            v.edit(self.cfg.VAMUser, self.cfg.VAMPassword,
                                         dataDict, communityId)
                        except:
                            vmtnError = "Unable to update this project's VAM entry." 

                    else:
                        # Create new VAM entry & get vamId
                        try:
                            from mint.web import vmtn
                            v = vmtn.VMTN()
                            vamId = v.add(self.cfg.VAMUser, 
                                                    self.cfg.VAMPassword,
                                                    dataDict)
                        except:
                            vmtnError = "Unable to create a VAM entry for this project."
                        else:
                            self.client.setCommunityId(self.project.getId(), 
                                                   communitytypes.VMWARE_VAM,
                                                   vamId)

            pubrelease.publish(shouldMirror=shouldMirror)
            if vmtnError:
                self._setInfo("Published release %s (version %s)" % (pubrelease.name, pubrelease.version) + '.  ' + vmtnError)
            else:
                self._setInfo("Published release %s (version %s)" % (pubrelease.name, pubrelease.version))
            self._predirect("releases")
        else:
            if self.cfg.VAMUser:
                build = self._getLatestVMwareBuild(pubrelease)        
            else:
                build = None
            if build:
                previewData = self._getPreviewData(pubrelease, build)
            else:
                previewData = False
                
            mirroredByRelease = self.client.isProjectMirroredByRelease(
                                    self.project.getId())
            return self._write("confirmPublish",
                    message = "Publishing your release will make it viewable to the public. Be advised that, should you need to make changes to the release in the future (e.g. add/remove images, update description, etc.) you will need to unpublish it first. Are you sure you want to publish this release?",
                    yesArgs = { 'func': 'publishRelease',
                                'id': yesArgs['id'],
                                'confirmed': '1'},
                    noLink = "releases", previewData = previewData, 
                    shouldMirror=False, 
                    mirroredByRelease=mirroredByRelease)

    @ownerOnly
    @dictFields(yesArgs = {})
    @boolFields(confirmed = False)
    def unpublishRelease(self, auth, confirmed, **yesArgs):
        if confirmed:
            pubrelease = self.client.getPublishedRelease(int(yesArgs['id']))
            pubrelease.unpublish()
            self._setInfo("Unpublished release %s (version %s)" % (pubrelease.name, pubrelease.version))
            self._predirect("releases")
        else:
            return self._write("confirm",
                    message = "Unpublishing your release will hide the release from the public, as well as allow you edit the contents of the release.  Note that unpublishing a release will not remove the related content from any repository.  Are you sure you want to unpublish your release?",
                    yesArgs = { 'func': 'unpublishRelease',
                                'id': yesArgs['id'],
                                'confirmed': '1'},
                    noLink = "releases")

    @intFields(id = None)
    @listFields(int, buildType = [])
    def release(self, auth, id, buildType):
        try:
            release = self.client.getPublishedRelease(id)
            builds = [self.client.getBuild(x) for x in release.getBuilds()]
            flaggedBuilds = set([buildtypes.flavorFlagsFromId[x] \
                                     for x in buildType \
                                     if x in buildtypes.FLAG_TYPES])
            builds = (not buildType) and  builds or \
                ([x for x in builds if x.buildType in buildType or \
                      flaggedBuilds.intersection(x.getDataDict())])
        except ItemNotFound:
            self._predirect("releases")
        else:
            return self._write("pubrelease", release = release, builds = builds)

    @listFields(str, buildType = [])
    def latestRelease(self, auth, buildType):
        buildType = [buildtypes.validBuildTypes.get(x) or \
                         buildtypes.deprecatedBuildTypes.get(x) \
                         or buildtypes.flavorFlags.get(x) for x in buildType]
        if None in buildType:
            self._addErrors("Invalid image type")
            self._predirect(temporary = True)
            return
        if not self.latestPublishedRelease:
            self._addErrors("This %s does not have any published releases."%getProjectText().lower())
            self._predirect(temporary = True)
        else:
            if buildType:
                queryStr = '&'.join(['buildType=%d' % x for x in buildType])
                self._predirect('release?id=%d&%s' % \
                                    (self.latestPublishedRelease.id, queryStr),
                                temporary = True)
            else:
                self._predirect('release?id=%d' % \
                                    (self.latestPublishedRelease.id),
                                temporary = True)

    @writersOnly
    @intFields(buildId = None)
    def restartJob(self, auth, buildId):
        self.client.startImageJob(buildId)

        self._predirect("build?id=%d" % buildId)

    def _mailingLists(self, auth, mlists, messages=[]):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        hostname = self.project.getHostname()
        lists = mlists.list_lists(hostname)
        return self._write("mailingListsUI", lists=lists, mailhost=self.cfg.MailListBaseURL, hostname=hostname, messages=messages)

    @mailList
    def mailingLists(self, auth, mlists, messages=[]):
        return self._mailingLists(auth, mlists, messages)

    @ownerOnly
    @strFields(listname=None, description='', listpw='', listpw2='')
    @mailList
    def createList(self, auth, mlists, listname, description, listpw, listpw2):
        # no new lists may be created as of 05/01/2007
        raise mailinglists.MailingListException("Mail Lists Disabled")

        if listpw == listpw2:
            members = self.project.getMembers()
            owners = []
            for member in members:
                if member[2] == userlevels.OWNER:
                    owner = self.client.getUser(member[0])
                    owners.append(owner.getEmail())
            hostname = self.project.getHostname()
            if not mlists.add_list(self.cfg.MailListPass, hostname+'-'+listname, listpw, description, owners):
                raise mailinglists.MailingListException("Mailing list not created")
            return self._mailingLists(auth, mlists, ['Mailing list "%s" created' % hostname+'-'+listname])
        else:
            raise mailinglists.MailingListException("Passwords do not match")

    @ownerOnly
    @boolFields(confirmed = False)
    @mailList
    @dictFields(yesArgs = {})
    def resetPassword(self, auth, confirmed, mlists, **yesArgs):
        if confirmed:
            if mlists.reset_list_password(str(yesArgs['list']), self.cfg.MailListPass):
                return self._mailingLists(auth, mlists, ['Mailing list password reset for %s' % str(yesArgs['list'])])
            else:
                return self._mailingLists(auth, mlists, ['Mailing list password for %s was not reset' % str(yesArgs['list'])])
        else:
            return self._write("confirm", message = "Reset the administrator password for the %s mailing list and send a reminder to the list owners?" % str(yesArgs['list']),
                yesArgs = {'func':'resetPassword', 'list':str(yesArgs['list']), 'confirmed':'1'}, noLink = "mailingLists")


    @ownerOnly
    @strFields(list=None)
    @mailList
    def deleteList(self, auth, mlists, list, confirmed=0, **kwargs):
        if not confirmed:
            return self._write("confirm", message = 'Are you sure you want to delete the mailing list "%s"' % list, yesArgs = {'func':'deleteList', 'confirmed':'1', 'list':list}, noLink =  'mailingLists')
        hostname = self.project.getHostname()
        pcre = re.compile('^%s$|^%s-'%(hostname, hostname), re.I)
        if pcre.search(list):
            #Do not delete mailing list archives by default.  This means that
            #archives must be deleted manually if necessary.
            if not mlists.delete_list(self.cfg.MailListPass, list, False):
                raise mailinglists.MailingListException("Mailing list not deleted")
        else:
            raise mailinglists.MailingListException("You cannot delete this list")
        return self._mailingLists(auth, mlists, ['Mailing list "%s" deleted' % list])

    @requiresAuth
    @strFields(list=None)
    @mailList
    def subscribe(self, auth, mlists, list):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")

        return_data = 'You have been subscribed to %s' % list
        try:
            mlists.server.Mailman.addMember(list, self.cfg.MailListPass, auth.email, auth.fullName, '', False, True)
        except:
            exc_data = sys.exc_info()
            if re.search("Errors\.MMAlreadyAMember", str(exc_data)):
                return_data = "You are already subscribed to %s" % list
            elif re.search("Errors\.MMBadEmailError", str(exc_data)):
                raise mailinglists.MailingListException("Bad E-Mail Address")
            else:
                raise mailinglists.MailingListException("Mailing List Error")
        return self._mailingLists(auth, mlists, [return_data])

    @requiresAuth
    @ownerOnly
    def editProject(self, auth):
        kwargs = {
            'projecturl': self.project.getProjectUrl(),
            'commitEmail': self.project.commitEmail,
            'name': self.project.getName(),
            'desc': self.project.getDesc(),
            'isPrivate': self.project.hidden,
            'namespace': self.project.getNamespace(),
        }
        return self._write("editProject", kwargs = kwargs)

    @strFields(projecturl = '', desc = '', name = '',
               commitEmail = '', isPrivate = 'off', namespace='')
    @ownerOnly
    def processEditProject(self, auth, projecturl, desc, name,
                           commitEmail, isPrivate, namespace):

        isPrivate = (isPrivate.lower() == 'on') and True or False
        
        pText = getProjectText()
        if not name:
            self._addErrors("You must supply a %s title"%pText.lower())

        if not self._getErrors():
            try:
                self.project.editProject(projecturl, desc, name)
                self.project.setNamespace(namespace)
                self.project.setCommitEmail(commitEmail)
            except DuplicateItem:
                self._addErrors("%s title conflicts with another %s"%(pText.title(), pText.lower()))
            
        # set the product visibility
        self.client.setProductVisibility(self.project.id, isPrivate)

        if self._getErrors():
            kwargs = {'projecturl': projecturl, 'desc': desc, 'name': name,
                      'commitEmail': commitEmail, 'isPrivate': isPrivate,
                      'namespace': namespace}
            return self._write("editProject", kwargs = kwargs)
        else:
            self._setInfo("Updated %s %s" % (pText.lower(), name))
            self._predirect()

    @requiresAuth
    @ownerOnly
    @intFields(id = -1)
    def editVersion(self, auth, id, *args, **kwargs):
        isNew = (id == -1)
        
        # external projects can't use this yet
        if self.project.external:
            raise ProductDefinitionVersionExternalNotSup();
        
        availablePlatforms = self.client.getAvailablePlatforms()
        try:
            # Assume that the first available platform is the default
            kwargs['platformLabel'] = availablePlatforms[0][0]
        except IndexError:
            # Failing that, we don't have a platform label
            kwargs['platformLabel'] = ''

        platformName = None
        customPlatform = ()
        acceptablePlatform = True

        if not isNew:
            kwargs.update(self.client.getProductVersion(id))
            pd = self.client.getProductDefinitionForVersion(id)
            platformSourceTrove = pd.getPlatformSourceTrove()
            if platformSourceTrove:
                n,v,f = parseTroveSpec(platformSourceTrove)
                vObj = versions.VersionFromString(v)
                kwargs['platformLabel'] = str(vObj.trailingLabel())
                for lbl, name in availablePlatforms:
                    if lbl == kwargs['platformLabel']:
                        platformName = name
                        break
                if not platformName:
                    platformName = 'Custom appliance platform on %s' % kwargs['platformLabel']
                    customPlatform = (kwargs['platformLabel'], platformName)
                    acceptablePlatform = \
                            self.client.isPlatformAcceptable(kwargs['platformLabel'])

            kwargs['namespace'] = pd.getConaryNamespace()
        else:
            valueToIdMap = buildtemplates.getValueToTemplateIdMap();
            pd = proddef.ProductDefinition()
            helperfuncs.addDefaultStagesToProductDefinition(pd)
            # XXX: this should be carried forward when images and other values are
            kwargs['namespace'] = self.project.namespace
        helperfuncs.addDefaultPlatformToProductDefinition(pd)

        return self._write("editVersion",
                isNew = isNew,
                id=id,
                visibleBuildTypes = self._productVersionAvaliableBuildTypes(pd),
                buildTemplateValueToIdMap = buildtemplates.getValueToTemplateIdMap(),
                productDefinition = pd,
                availablePlatforms = availablePlatforms,
                acceptablePlatform = acceptablePlatform,
                platformName = platformName,
                customPlatform = customPlatform,
                kwargs = kwargs)

    @intFields(id = -1)
    @strFields(namespace = '', name = '', description = '', baseFlavor = '', action = 'Cancel', platformLabel = '')
    @requiresAuth
    @ownerOnly
    def processEditVersion(self, auth, id, namespace, name, description, action, baseFlavor, platformLabel, **kwargs):

        isNew = (id == -1)

        if not namespace:
            self._addErrors('Missing namespace')
        else:
            err = helperfuncs.validateNamespace(namespace)
            if err != True:
                self._addErrors(err)

        if not name:
            self._addErrors("Missing major version")

        # Load the current project definition for this version
        # If this is new, use our template product definition
        # generator. Otherwise, just get it from the repository.
        if isNew:
            pd = proddef.ProductDefinition()
        else:
            pd = self.client.getProductDefinitionForVersion(id)

        pd = helperfuncs.sanitizeProductDefinition(
                    self.project.name,
                    self.project.description,
                    self.project.hostname,
                    self.project.domainname,
                    self.project.shortname,
                    name,
                    description,
                    namespace,
                    pd)

        # Gather all grouped inputs
        collatedDict = helperfuncs.collateDictByKeyPrefix(kwargs,
                coerceValues=True)

        # Process stages
        stages = collatedDict.get('pdstages', {})
        try:
            self._validateStages(stages)
        except ProductDefinitionInvalidStage, e:
            self._addErrors(str(e))

        # XXX ProductDefinition object needs clearStages()
        pd.stages = proddef._Stages()
        for s in stages:
            pd.addStage(s['name'], s['labelSuffix'])

        # Process build definitions
        buildDefsList = collatedDict.get('pdbuilddef',[])

        # Currently, stageNames for each build is
        # defined as the full set of stages.
        stageNames = [x.name for x in pd.getStages()]

        pd.clearBuildDefinition()

        validationErrors = []
        warnedNoNameAlready = False
        for builddef in buildDefsList:
            buildType = int(builddef.get('_buildType'))
            xmlTagName = buildtypes.imageTypeXmlTagNameMap[buildType]
            buildName = builddef.pop('name', '')
            proposedBuildSettings = dict(x for x in builddef.iteritems() if not x[0].startswith('_'))
            bTmpl = buildtemplates.getDataTemplate(buildType)
            buildSettings = bTmpl.getDefaultDict()
            buildSettings.update(proposedBuildSettings)

            # only add this error once
            if not buildName and not warnedNoNameAlready:
                self._addErrors("Missing name for build definition(s)")
                warnedNoNameAlready = True
            else:
                try:
                    bTmpl.validate(**buildSettings)
                except BuildOptionValidationException, e:
                    validationErrors.extend(e.errlist)
            # add regardless of errors.  if an error occurred, we want the user
            # to see what they entered.

            # Coerce trove type options back to their class name
            buildSettings = dict([
                (buildtemplates.reversedOptionNameMap.get(k, k), v)
                 for k, v in buildSettings.iteritems()
                    if v != '' and v is not None
            ])

            flvSetArchRef = builddef.get('flvSetArchRef')
            if flvSetArchRef:
                flavorSetRef, architectureRef = flvSetArchRef.split(',')
            else:
                self._addErrors("The combination of image type and architecture for image '%s' is not compatible with your platform. Please remove it from your image set." % buildName)
                flavorSetRef = architectureRef = None
            pd.addBuildDefinition(name=buildName,
                flavorSetRef = flavorSetRef,
                architectureRef = architectureRef,
                containerTemplateRef = xmlTagName,
                image = pd.imageType(None, buildSettings),
                stages = stageNames)

        for ve in validationErrors:
            self._addErrors(str(ve))

        if not self._getErrors():
            if isNew:
                try:
                    id = self.client.addProductVersion(self.project.id,
                                            namespace, name, description)
                except ProductVersionInvalid, e:
                    self._addErrors(str(e))
            else:
                self.client.editProductVersion(id, description)

        if id != -1 and not self._getErrors():
            if isNew:
                self.client.setProductDefinitionForVersion(id, pd, platformLabel)
            else:
                self.client.setProductDefinitionForVersion(id, pd)

            if kwargs.has_key('linked'):
                # we got here from the "create a product menu" so output
                # accordingly.  Note that the value of linked is the name
                # of the project.
                visibility = self.project.hidden and "private" or "public"
                self._setInfo("Successfully created %s %s '%s' version '%s'" % \
                              (visibility, getProjectText().lower(), 
                               self.project.name,
                               name))
            else:
                action = isNew and "Created" or "Updated"
                self._setInfo("%s %s version '%s'" % \
                              (action, getProjectText().lower(), name))
            #Set the currentVersion to the just created one
            self._setCurrentProductVersion(id)
            self._predirect()
        else:
            # we're displaying the page 
            availablePlatforms = self.client.getAvailablePlatforms()
            platformName = ''
            customPlatform = ()
            acceptablePlatform = True
            for lbl, pName in availablePlatforms:
                if lbl == platformLabel:
                    platformName = pName
                    break
            if not platformName:
                if not platformLabel and pd.getPlatformSourceTrove():
                    platformTroveSpec = pd.getPlatformSourceTrove()
                    platformNVF = parseTroveSpec(platformTroveSpec)
                    platformVersion = versions.VersionFromString(platformNVF[1])
                    platformLabel = str(platformVersion.trailingLabel())
                if platformLabel:
                    platformName = 'Custom appliance platform on %s' % platformLabel
                    acceptablePlatform = \
                            self.client.isPlatformAcceptable(platformLabel)
                else:
                    platformName = 'None'
                    acceptablePlatform = False
                customPlatform = (platformLabel, platformName)


            kwargs.update(name = name, description = description,
                    platformLabel = platformLabel, namespace = namespace)
            return self._write("editVersion", 
               isNew = isNew,
               id=id,
               visibleBuildTypes = self._productVersionAvaliableBuildTypes(pd),
               buildTemplateValueToIdMap = buildtemplates.getValueToTemplateIdMap(),
               availablePlatforms = availablePlatforms,
               acceptablePlatform = acceptablePlatform,
               platformName = platformName,
               customPlatform = customPlatform,
               productDefinition = pd, kwargs = kwargs)

    @intFields(id = -1)
    @requiresAuth
    @ownerOnly
    def rebaseProductVersion(self, auth, id):

        return_to = ''
        if self.req.headers_in.has_key('referer') and \
                self.project.getUrl(self.baseUrl) in self.req.headers_in['referer']:
            return_to = self.req.headers_in['referer'].split('/')[-1]

        productVersion = self.client.getProductVersion(id)
        availablePlatforms = self.client.getAvailablePlatforms()
        try:
            # Assume that the first available platform is the default
            platformLabel = availablePlatforms[0][0]
        except IndexError:
            # Failing that, we don't have a platform label
            platformLabel = ''

        platformName = None
        customPlatform = ()
        acceptablePlatform = True
        pd = self.client.getProductDefinitionForVersion(id)

        platformSourceTrove = pd.getPlatformSourceTrove()
        if platformSourceTrove:
            n,v,f = parseTroveSpec(platformSourceTrove)
            vObj = versions.VersionFromString(v)
            platformLabel = str(vObj.trailingLabel())
            for lbl, name in availablePlatforms:
                if lbl == platformLabel:
                    platformName = name
                    break
            if not platformName:
                platformName = 'Custom appliance platform on %s' % platformLabel
                customPlatform = (platformLabel, platformName)
                acceptablePlatform = \
                        self.client.isPlatformAcceptable(platformLabel)

        return self._write("rebaseProductVersion",
                id = id,
                productName = self.project.name,
                versionName = productVersion.get('name',''),
                currentPlatformLabel = platformLabel,
                customPlatform = customPlatform,
                availablePlatforms = availablePlatforms,
                return_to = return_to)

    @intFields(id = -1)
    @strFields(platformLabel = '', action = 'Cancel', return_to='')
    @requiresAuth
    @ownerOnly
    def processRebaseProductVersion(self, auth, id, platformLabel, action, return_to):
        if action == 'Cancel':
            self._predirect(return_to)

        pd = self.client.getProductDefinitionForVersion(id)
        if self.client.setProductDefinitionForVersion(id, pd, platformLabel):
            self._setInfo("Product version updated")
        else:
            self._addError("Problem updating product version")
        self._predirect(return_to)

    def _productVersionAvaliableBuildTypes(self, pd):
        """
        Get a list of the available build types for build defs
        """
        # get a list of all the types this rBuilder knows about
        availableTypes = helperfuncs.getBuildDefsAvaliableBuildTypes(
            self.client.getAvailableBuildTypes())

        # get a list of all the containerTemplates this proddef has defined
        # filter any containers that don't actually have defined flavors
        definedTypes = set()
        containerTemplates = []
        buildTemplates = []

        if hasattr(pd, 'platform') and pd.platform:
            containerTemplates = pd.platform.containerTemplates
            buildTemplates = pd.platform.buildTemplates
        containerTemplates += pd.getContainerTemplates()
        buildTemplates += pd.getBuildTemplates()
        definedContainers = set([x.containerTemplateRef \
                for x in buildTemplates])

        for template in containerTemplates:
            if template.containerFormat not in definedContainers:
                continue
            definedTypes.add(buildtypes.xmlTagNameImageTypeMap[template.containerFormat])

        return list(definedTypes.intersection(availableTypes))

    def _validateStages(self, stagesList):
        """
        Validate the release stages
        """
        if not stagesList:
            raise ProductDefinitionInvalidStage(
                    'You must have one or more release stages defined')
        
        for stage in stagesList:
            # name is required
            if not stage.has_key('name'):
                raise ProductDefinitionInvalidStage(
                    'The release stage name must be specified')
            # make sure all stages have a labelSuffix
            # value since we allow it to be empty
            if not stage.has_key('labelSuffix'):
                stage['labelSuffix'] = ""
                
    def _getValidatedUpstreamSource(self, us):
        """
        Return the validated troveName and label for the specified upstream
        sources dict.  Any keys missing from the dict will be set to '' so 
        that errors can be properly handled.
        """
        
        # validate the trove name
        if not us.has_key('troveName'):
            troveName = ''
            self._addErrors("Missing trove name for upstream source")
        else:
            troveName = us['troveName']
            
        # validate the label
        if not us.has_key('label'):
            label = ''
            self._addErrors("Missing label for upstream source")
        else:
            try:
                labelObj = versions.Label(us['label'])
                label = labelObj.freeze()
            except Exception ,e:
                label = us['label']
                self._addErrors("Invalid label for upstream source: %s" \
                                % str(e))
            
        return troveName, label

    def _isAdoptable(self, memberList=None):
        if memberList is None:
            memberList = self.project.getMembers()
        return not [x for x in memberList if x[2] in userlevels.WRITERS]

    def members(self, auth):
        memberList = self.project.getMembers()
        if (self.userLevel == userlevels.OWNER or auth.admin):
            reqList = self.client.listJoinRequests(self.project.getId())
        else:
            reqList = []
        hidden = self.project.hidden
        adoptable = self._isAdoptable(memberList)
        joinable = (self.auth.authorized
                and self.userLevel not in userlevels.WRITERS
                and not adoptable)
        return self._write("members",
                projectMemberList=memberList,
                userHasReq = self.client.userHasRequested(self.project.getId(),
                    auth.userId),
                reqList=reqList, hidden=hidden,
                adoptable=adoptable, joinable=joinable)

    def membersUI(self, auth):
        memberList = self.project.getMembers()
        if (self.userLevel == userlevels.OWNER or auth.admin):
            reqList = self.client.listJoinRequests(self.project.getId())
        else:
            reqList = []
        hidden = self.project.hidden
        adoptable = self._isAdoptable(memberList)
        joinable = (self.auth.authorized
                and self.userLevel not in userlevels.WRITERS
                and not adoptable)
        return self._write("membersUI",
                projectMemberList=memberList,
                userHasReq = self.client.userHasRequested(self.project.getId(),
                    auth.userId),
                reqList=reqList, hidden=hidden,
                adoptable=adoptable, joinable=joinable)

    @requiresAuth
    def adopt(self, auth):
        if self._isAdoptable():
            self.project.adopt(auth, self.cfg.EnableMailLists, self.cfg.MailListBaseURL,
                    self.cfg.MailListPass)
            self._setInfo("You have successfully adopted %s" % self.project.getNameForDisplay())
        else:
            self.req.log_error("User %s attempted to illegally adopt "
                    "project %s" % (self.auth.username,
                        self.project.shortname))
            self._addErrors("You cannot adopt this project at this time.")
        self._predirect("members")

    @strFields(username = None)
    @intFields(level = None)
    @ownerOnly
    def addMember(self, auth, username, level):
        self.project.addMemberByName(username, level)
        self._setInfo("User %s has been added to %s" % (username, self.project.getNameForDisplay()))
        self._predirect("members")

    @requiresAuth
    def watch(self, auth):
        #some kind of check to make sure the user's not a member
        if self.userLevel == userlevels.NONMEMBER:
            self.project.addMemberByName(auth.username, userlevels.USER)
            self._setInfo("You are now a registered user of %s" % self.project.getNameForDisplay())
        self._predirect("members")

    @requiresAuth
    def watchUI(self, auth):
        #some kind of check to make sure the user's not a member
        if self.userLevel == userlevels.NONMEMBER:
            self.project.addMemberByName(auth.username, userlevels.USER)
            self._setInfo("You are now a registered user of %s" % self.project.getNameForDisplay())
        self._predirect("membersUI")

    @requiresAuth
    def unwatch(self, auth):
        if self.userLevel == userlevels.USER:
            self.project.delMemberById(auth.userId)
            self._setInfo("You are no longer a registered user of %s" % self.project.getNameForDisplay())
        if self.project.hidden:
            self._redirectHttp()
        else:
            self._predirect("members")

    @requiresAuth
    def unwatchUI(self, auth):
        if self.userLevel == userlevels.USER:
            self.project.delMemberById(auth.userId)
            self._setInfo("You are no longer a registered user of %s" % self.project.getNameForDisplay())
        if self.project.hidden:
            self._redirectHttp()
        else:
            self._predirect("membersUI")

    @strFields(comments = '', keepReq = None)
    @requiresAuth
    def processJoinRequest(self, auth, comments, keepReq):
        projectId = self.project.getId()
        userId = auth.userId
        if keepReq == "Submit":
            self.client.setJoinReqComments(projectId, comments)
            self._setInfo("Join request for %s has been submitted" % self.project.getNameForDisplay())
        else:
            self.client.deleteJoinRequest(projectId, userId)
            self._setInfo("Your join request for %s has been deleted" % self.project.getNameForDisplay())
        self._predirect("members")

    @strFields(comments = '', keepReq = None)
    @requiresAuth
    def processJoinRequestUI(self, auth, comments, keepReq):
        projectId = self.project.getId()
        userId = auth.userId
        if keepReq == "Submit":
            self.client.setJoinReqComments(projectId, comments)
            self._setInfo("Join request for %s has been submitted" % self.project.getNameForDisplay())
        else:
            self.client.deleteJoinRequest(projectId, userId)
            self._setInfo("Your join request for %s has been deleted" % self.project.getNameForDisplay())
        self._predirect("membersUI")

    @ownerOnly
    @intFields(userId = None)
    def viewJoinRequest(self, auth, userId):
        user = self.client.getUser(userId)
        return self._write('viewJoinRequest', userId = userId,
               username = user.getUsername(),
               projectId = self.project.getId(),
               comments = self.client.getJoinReqComments(self.project.getId(),
                   userId))

    @ownerOnly
    @strFields(action = '')
    @intFields(userId = None)
    def acceptJoinRequest(self, auth, userId, action):
        projectId = self.project.getId()
        user = self.client.getUser(userId)
        username = user.getUsername()
        # XXX This is fragile, and probably will not work so well with
        #     i18n efforts in the future. I'm hoping that the webpage
        #     redesign will come up with a better way to manage this
        #     than having three buttons on a separate page. --sgp
        if action == 'Reject Request':
            return self._write('rejectJoinRequest', userId = userId,
                    username = user.getUsername())
        elif action == 'Make Owner':
            self.project.addMemberByName(username, userlevels.OWNER)
            self._setInfo("User %s has been added as an owner to %s" % \
                    (username, self.project.getNameForDisplay()))
        elif action == 'Make Developer':
            self.project.addMemberByName(username, userlevels.DEVELOPER)
            self._setInfo("User %s has been added as a developer to %s" % \
                    (username, self.project.getNameForDisplay()))
        else:
            # do nothing (should never happen)
            pass
        self._predirect("members")

    @ownerOnly
    @intFields(userId = None)
    @strFields(comments = '')
    def processJoinRejection(self, auth, userId, comments):
        pText = getProjectText().lower()
        user = self.client.getUser(userId)
        if self.cfg.sendNotificationEmails:
            subject = "Membership Rejection Notice"
            body = "Your request to join the following %s on %s:\n\n" % (pText, self.cfg.productName)
            body += "%s\n\n" % self.project.getName()
            body += " has been rejected by the %s's owner.\n\n"%pText
            if comments:
                body += "Owner's comments:\n%s" % comments
            else:
                body += "The owner did not provide a reason for this rejection.\n"
            sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, user.getEmail(), subject, body)
        self.client.deleteJoinRequest(self.project.getId(), userId)
        self._setInfo("Join request for user %s has been rejected " \
                "for %s %s" % (user.getUsername(), \
                pText, self.project.getNameForDisplay()))
        self._predirect("members")

    @requiresAuth
    def joinRequest(self, auth):
        return self._write("joinRequest", comments = self.client.getJoinReqComments(self.project.getId(), auth.userId) )

    @requiresAuth
    def joinRequestUI(self, auth):
        return self._write("joinRequestUI", comments = self.client.getJoinReqComments(self.project.getId(), auth.userId) )

    @intFields(userId = None, level = None)
    @ownerOnly
    def editMember(self, auth, userId, level):
        user = self.client.getUser(userId)
        self.project.updateUserLevel(userId, level)
        self._setInfo("User %s has been updated for %s %s" % \
                (user.getUsername(), getProjectText(), self.project.getNameForDisplay()))
        self._predirect("members")

    @intFields(userId = None)
    @ownerOnly
    def promoteMember(self, auth, userId):
        #USERS and DEVELOPERS can be promoted (see below)
        user = self.client.getUser(userId)
        userDict = getUserDict(self.project.getMembers())
        for level in [userlevels.DEVELOPER, userlevels.USER]:
            for u in userDict[level]:
                if u[0] == userId:
                    levelidx = userlevels.LEVELS.index(level)
                    self.project.updateUserLevel(userId, userlevels.LEVELS[levelidx - 1])
                    self._setInfo("User %s promoted" % user.getUsername())
                    self._predirect("members")
        self._addErrors("User %s not a member of %s %s" % \
                (user.getUsername(), getProjectText().lower(), self.project.getNameForDisplay()))
        self._predirect("members")

    @intFields(userId = None)
    @ownerOnly
    def demoteMember(self, auth, userId):
        #But only owners may be demoted.  Developers must be deleted. (see above)
        user = self.client.getUser(userId)
        userDict = getUserDict(self.project.getMembers())
        for level in [userlevels.OWNER]:
            for u in userDict[level]:
                if u[0] == userId:
                    levelidx = userlevels.LEVELS.index(level)
                    self.project.updateUserLevel(userId, userlevels.LEVELS[levelidx + 1])
                    self._setInfo("User %s demoted" % user.getUsername())
                    self._predirect("members")
        self._addErrors("User %s not a member of %s %s" % \
                (user.getUsername(), getProjectText().lower(), self.project.getNameForDisplay()))
        self._predirect("members")

    @requiresAuth
    @writersOnly
    @intFields(span = 7)
    @strFields(format = 'png')
    def downloadChartImg(self, auth, span, format):
        contentTypes = {
            'png': 'image/png',
            'svg': 'image/svg+xml',
            'pdf': 'application/pdf',
        }

        self.req.content_type = contentTypes[format]

        # constrain the span to a reasonable limit
        span = span <= 30 and span or 30

        return self.client.getDownloadChart(self.project.id, days = span, format = format)

    @requiresAuth
    @writersOnly
    @intFields(span = 7)
    def downloads(self, auth, span):
        return self._write("downloads", span = span)

    @requiresAuth
    @writersOnly
    @intFields(span = 7)
    def downloadsUI(self, auth, span):
        return self._write("downloadsUI", span = span)

    @requiresAuth
    @boolFields(confirmed = False)
    @dictFields(yesArgs = {})
    def resign(self, auth, confirmed, **yesArgs):
        if confirmed:
            self.project.delMemberById(auth.userId)
            self._setInfo("You have resigned from %s %s" % \
                    (getProjectText().lower(), self.project.getNameForDisplay()))
            self._redirectHttp()
        else:
            return self._write("confirm", message = "Are you sure you want to resign from this %s?"%getProjectText().lower(),
                yesArgs = {'func':'resign', 'confirmed':'1'}, noLink = "/")
            
    @requiresAuth
    @boolFields(confirmed = False)
    @dictFields(yesArgs = {})
    def deleteProject(self, auth, confirmed, **yesArgs):
        if confirmed:
            pName = self.project.name
            self.client.deleteProject(self.project.id)
            self._setInfo("%s '%s' has been deleted." % \
                    (getProjectText().title(), pName))
            self._redirectHttp()
        else:
            pText = getProjectText().lower()
            noLink = "%sproject/%s" % (self.cfg.basePath, self.project.getHostname())
            return self._write("confirm",
                message = """Warning: Deleting this %s is an irreversible operation, and
                             will negatively impact all %ss and individuals that consume
                             it, even if a %s is later created with the same name."""
                             % (pText, pText, pText),
                messageBottom = "Are you sure you want to delete this %s?" % pText,
                yesArgs = {'func':'deleteProject', 'confirmed':'1'}, noLink = noLink)

    @strFields(feed= "releases")
    def rss(self, auth, feed):
        if feed == "releases":
            title = "%s - %s releases" % (self.cfg.productName, self.project.getName())
            link = "http://%s%sproject/%s/releases" % \
                (self.cfg.siteHost, self.cfg.basePath, self.project.getHostname())
            desc = "Latest releases from %s" % self.project.getName()

            items = []
            hostname = self.project.getHostname()
            projectName = self.project.getName()
            for release in self.projectPublishedReleases[:10]:
                item = {}
                item['title'] = "%s (version %s)" % (release.name, release.version)
                item['link'] = "http://%s%sproject/%s/release?id=%d" % \
                    (self.cfg.siteHost, self.cfg.basePath, hostname, release.getId())
                item['content']  = "This release contains the following images:"
                item['content'] += "<ul>"
                builds = [self.client.getBuild(x) for x in release.getBuilds()]
                for build in builds:
                    item['content'] += "<li><a href=\"http://%s%sproject/%s/build?id=%ld\">%s (%s %s)</a></li>" % \
                        (self.cfg.siteHost, self.cfg.basePath, hostname, build.id, build.getName(),
                         build.getArch(), buildtypes.typeNamesShort[build.buildType])
                item['content'] += "</ul>"
                item['date_822'] = email.Utils.formatdate(release.timePublished)
                item['creator'] = "http://%s%s" % (self.siteHost, self.cfg.basePath)
                items.append(item)
        elif feed == "commits":
            title = "%s - %s commits" % (self.cfg.productName, self.project.getName())
            link = "http://%s%sproject/%s/" % \
                    (self.cfg.siteHost, self.cfg.basePath, self.project.getHostname())
            desc = "Latest commits from %s" % self.project.getName()
            items = []
            hostname = self.project.getHostname()
            projectName = self.project.getName()
            # get commits from backend
            for commit in self.project.getCommits():
                troveName, troveVersionString, troveFrozenVersion, timestamp = commit
                item = {}
                item['title'] = "%s (version %s)" % (troveName, troveVersionString)
                item['link'] = "http://%s%srepos/%s/troveInfo?t=%s;v=%s" % \
                    (self.cfg.siteHost, self.cfg.basePath, hostname, troveName, troveFrozenVersion)
                item['content']  = "A new version of %s has been committed to %s." % (troveName, projectName)
                item['date_822'] = email.Utils.formatdate(timestamp)
                item['creator'] = "http://%s%s" % (self.siteHost, self.cfg.basePath)
                items.append(item)
        else:
            items = []
            title = "Invalid RSS feed style requested."
            link = ""
            desc = ""

        return self._writeRss(items = items, title = title, link = link, desc = desc)

