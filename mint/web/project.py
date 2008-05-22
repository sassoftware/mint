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
import tempfile
from mod_python import apache

from mint.web import basictroves
from mint import communitytypes
from mint import database
from mint import mailinglists
from mint import jobs
from mint import jobstatus
from mint import builds
from mint import buildtypes
from mint import userlevels
from mint import users
from mint import packagecreator
from mint.mint_error import *

from mint import buildtemplates
from mint import helperfuncs
from mint.helperfuncs import getProjectText
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
from mint.users import sendMailWithChecks
from mint.web.fields import strFields, intFields, listFields, boolFields, dictFields
from mint.web.webhandler import WebHandler, normPath, HttpNotFound, \
     HttpForbidden
from mint.web.decorators import ownerOnly, writersOnly, requiresAuth, \
        requiresAdmin, mailList, redirectHttp

import conary
from conary.lib import util
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


class ProjectHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)

        cmds = self.cmd.split("/")

        try:
            self.project = self.client.getProjectByHostname(cmds[0])
        except ItemNotFound:
            raise HttpNotFound

        # redirect endorsed (external) projects
        # to the right url if accessed incorrectly,
        # and vice-versa for internal (unendorsed) projects
        if self.project.external:
            if self.req.hostname != self.cfg.siteHost.split(':')[0]:
                self.req.log_error("%s %s accessed incorrectly; referer: %s" % \
                    (self.req.hostname, self.req.unparsed_uri, self.req.headers_in.get('referer', 'N/A')))
                self._redirect("http://" + self.cfg.siteHost + self.req.unparsed_uri)
        else:
            if self.req.hostname != self.cfg.projectSiteHost.split(':')[0]:
                self.req.log_error("%s %s accessed incorrectly; referer: %s" % \
                    (self.req.hostname, self.req.unparsed_uri, self.req.headers_in.get('referer', 'N/A')))
                self._redirect("http://" + self.cfg.projectSiteHost + self.req.unparsed_uri)

        self.userLevel = self.project.getUserLevel(self.auth.userId)
        self.isOwner  = (self.userLevel == userlevels.OWNER) or self.auth.admin
        self.isWriter = (self.userLevel in userlevels.WRITERS) or self.auth.admin

        #Take care of hidden projects
        if self.project.hidden and self.userLevel == userlevels.NONMEMBER and not self.auth.admin:
            raise HttpNotFound

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

        # add the project name to the base path
        self.basePath += "project/%s" % (cmds[0])
        self.basePath = normPath(self.basePath)

        if not cmds[1]:
            return self.projectPage
        try:
            method = self.__getattribute__(cmds[1])
        except AttributeError:
            raise HttpNotFound

        return method

    def _predirect(self, path = "", temporary = False):
        self._redirect("http://%s%sproject/%s/%s" % (self.cfg.projectSiteHost, self.cfg.basePath, self.project.hostname, path), temporary = temporary)

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
            
        if self.userLevel == userlevels.OWNER and not external:
            # get the versions associated with a product
            versions = self.client.getProductVersionListForProduct(
                                                                self.project.id)
        else:
            versions = []
            
        return self._write("projectPage", mirrored = mirrored, 
                           anonymous = anonymous, vmtnId = vmtnId,
                           versions = versions,
                           external = external)

    def releases(self, auth):
        return self._write("pubreleases")

    @writersOnly
    def builds(self, auth):
        builds = [self.client.getBuild(x) for x in self.project.getBuilds()]
        projectLabels = self.client.getAllProjectLabels(self.project.id)
        return self._write("builds", builds = builds, projectLabels = projectLabels)

    @writersOnly
    def groups(self, auth):
        builds = [self.client.getBuild(x) for x in self.project.getBuilds()]
        publishedBuilds = [x for x in builds if x.getPublished()]
        groupTrovesInProject = self.client.listGroupTrovesByProject(self.project.id)

        return self._write("groups", publishedBuilds = publishedBuilds,
            groupTrovesInProject = groupTrovesInProject)

    def _getBasicTroves(self):
        cfg = conarycfg.ConaryConfiguration()

        conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
        if os.path.exists(conarycfgFile):
            cfg.read(conarycfgFile)

        cfg.dbPath = cfg.root = ":memory:"
        cfg = helperfuncs.configureClientProxies(cfg, self.cfg.useInternalConaryProxy, self.cfg.proxy)
        repos = conaryclient.ConaryClient(cfg).getRepos()

        labels = basictroves.labelDict
        messages = basictroves.messageDict
        troveNames = {}
        troveList = []
        metadata = {}

        for lbl, trv in labels.items():
            label = versions.Label(lbl)
            troveNames.update({lbl: []})
            for group in trv:
                versionDict = repos.getTroveLeavesByLabel({group[0]: {label: None}})[group[0]]
                latestVersion = None
                for version, flavorList in versionDict.iteritems():
                    if latestVersion is None or version > latestVersion:
                        latestVersion = version
                        latestFlavor = flavorList[0]

                troveNames[lbl].append(group[0])
                troveList.append((group[0], (latestVersion, latestFlavor)))
                metadata.update({group[0]:group[1]})

        troveDict = dict(troveList)

        return troveNames, troveDict, metadata, messages

    @writersOnly
    def newGroup(self, auth):
        troveNames, troveDict, metadata, messages = self._getBasicTroves()

        return self._write("newGroup", kwargs = {},
                           troves = troveNames, troveDict = troveDict,
                           metadata = metadata, messages = messages)

    @strFields(groupName = "", version = "", description = "")
    @listFields(str, initialTrove = [])
    @writersOnly
    def createGroup(self, auth, groupName, version, description, initialTrove):
        fullGroupName = "group-" + groupName

        # validate version
        try:
            versions.Revision(version + "-1-1")
        except ParseError, e:
            self._addErrors("Error parsing version string: %s" % version)

        # validate group name
        if not re.match("group-[a-zA-Z0-9\-_]+$", fullGroupName):
            self._addErrors("Invalid group trove name: %s" % fullGroupName)

        if not self._getErrors():
            # do stuff
            gt = self.client.createGroupTrove(self.project.getId(), fullGroupName,
                version, description, True)
            gtId = gt.getId()

            for troveName, troveVersion, troveFlavor in (x.split(" ") for x in initialTrove):
                gt.addTrove(troveName, troveVersion, troveFlavor, fullGroupName, False, False, False)

            self._predirect("editGroup?id=%d" % gtId)
        else:
            kwargs = {'groupName': groupName, 'version': version}
            troves, troveDict, metadata, messages = self._getBasicTroves()

            return self._write("newGroup", kwargs = kwargs,
                troves = troves, troveDict = troveDict, metadata = metadata, 
                         messages = messages)

    @intFields(id = None)
    @writersOnly
    def editGroup(self, auth, id):
        curGroupTrove = self.client.getGroupTrove(id)
        self.session['groupTroveId'] = id
        self.groupTrove = curGroupTrove
        # these are mutually exclusive

        self.groupProject = self.client.getProject(self.groupTrove.projectId)
        return self._write("editGroup", message = None, curGroupTrove = curGroupTrove)

    def _saveGroupInfo(self, id, version, description, components, **kwargs):
        curGroupTrove = self.client.getGroupTrove(id)

        # Set the new version and description
        if description != curGroupTrove.description:
            curGroupTrove.setDesc(description)
        if version != curGroupTrove.upstreamVersion:
            curGroupTrove.setUpstreamVersion(version)

        # Set the troveItems lock states
        for t in curGroupTrove.listTroves():
            cvalue = kwargs.get('%d_versionLock' % t['groupTroveItemId'], 'off')
            if t['versionLock'] ^ (cvalue == 'on'):
                curGroupTrove.setTroveVersionLock(t['groupTroveItemId'], cvalue == 'on')

        curGroupTrove.setRemovedComponents(components)

    @intFields(id = None)
    @strFields(version = None, description = '', action = None)
    @listFields(str, components = [])
    @writersOnly
    def editGroup2(self, auth, id, version, description, components, action, **kwargs):
        if action == "Save Changes Only":
            self._saveGroupInfo(id, version, description, components, **kwargs)
            self._setInfo('Changes saved successfully')
            self._predirect("editGroup?id=%d" % id)
        elif action == "Delete This Group":
            self._predirect("deleteGroup?id=%d" % id)
        elif action == "Save and Cook":
            self._saveGroupInfo(id, version, description, components, **kwargs)
            return self._write("pickArch", groupTroveId = id)
        else:
            raise HttpNotFound

    @strFields(referer = None)
    @writersOnly
    def closeCurrentGroup(self, auth, referer):
        if 'groupTroveId' in self.session:
            del self.session['groupTroveId']
            self.session.save()
        self._redirect("http://%s%s" % (self.cfg.siteHost, referer))

    @dictFields(yesArgs = {})
    @boolFields(confirmed=False)
    @writersOnly
    def deleteGroup(self, auth, confirmed, **yesArgs):
        if 'id' not in yesArgs:
            raise HttpForbidden
        if confirmed:
            # Delete the group
            self.client.deleteGroupTrove(int(yesArgs['id']))
            if 'groupTroveId' in self.session and self.session['groupTroveId'] == int(yesArgs['id']):
                del self.session['groupTroveId']
            self._predirect("groups")
        else:
            return self._write('confirm', message = "Are you sure you want to delete this group trove?",
                yesArgs = {'func':'deleteGroup', 'id':yesArgs['id'], 'confirmed':'1'} , noLink = "groups")

    @intFields(id=None)
    @strFields(trove=None, version='', flavor='', referer='', projectName = '')
    @boolFields(versionLock=False)
    @writersOnly
    def addGroupTrove(self, auth, id, trove, version, flavor, referer, versionLock, projectName):
        curGroupTrove = self.client.getGroupTrove(id)
        if version != '':
            curGroupTrove.addTrove(trove, version, '', '', versionLock, False, False)
        else:
            try:
                curGroupTrove.addTroveByProject(trove, projectName, '', '', versionLock, False, False)
            except TroveNotFound, e:
                self._addErrors("Trove not found: %s" % trove)
        if not referer:
            referer = self.project.getUrl()
            self._redirect(referer)
        self._redirect("http://%s%s" % (self.cfg.siteHost, referer))

    @intFields(id=None, troveId=None)
    @strFields(referer='')
    @writersOnly
    def deleteGroupTrove(self, auth, id, troveId, referer):
        """Remove a trove from a group trove."""
        curGroupTrove = self.client.getGroupTrove(id)
        curGroupTrove.delTrove(troveId)
        if not referer:
            referer = self.project.getUrl()
            self._redirect(referer)
        self._redirect("http://%s%s" % (self.cfg.siteHost, referer))

    @intFields(id = None)
    @writersOnly
    def pickArch(self, auth, id):
        return self._write("pickArch", groupTroveId = id)

    @intFields(id = None)
    @listFields(str, flavor = ['1#x86'])
    @writersOnly
    def cookGroup(self, auth, id, flavor):
        curGroupTrove = self.client.getGroupTrove(id)

        arch = deps.mergeFlavorList([deps.ThawFlavor(x) for x in flavor]).freeze()
        jobId = curGroupTrove.startCookJob(arch)

        if 'groupTroveId' in self.session:
            del self.session['groupTroveId']

        return self._write("cookGroup", jobId = jobId,
            curGroupTrove = curGroupTrove)

    @writersOnly
    def newBuildsFromProductDefinition(self, auth):
        return self._write("newBuildsFromProductDefinition",
            productVersions = self.client.getProductVersionListForProduct(self.project.id))

    @intFields(productVersionId = -1)
    @strFields(action = "cancel", productStageName = None)
    @boolFields(force = False)
    @dictFields(yesArgs = None)
    @writersOnly
    def processNewBuildsFromProductDefinition(self, auth, productVersionId, productStageName, action, force, **yesArgs):

        if action.lower() == 'cancel':
            self._predirect('builds')

        try:
            self.client.newBuildsFromProductDefinition(productVersionId,
                    productStageName, force)
        except TroveNotFoundForBuildDefinition, tnffbd:
            return self._write("confirm",
                    message = "Some builds will not be built because of the following errors: %s" % ', '.join(tnffbd.errlist),
                    yesArgs = { 'func': 'processNewBuildsFromProductDefinition',
                                'productVersionId': productVersionId,
                                'productStageName': productStageName,
                                'action': 'submit',
                                'force': '1'},
                    noLink = "builds")
        except Exception, e:
            self._addErrors("Problem encountered when creating builds: %s" % str(e))
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
            arch = thawedFlavor.members[deps.DEP_CLASS_IS].members.keys()[0]

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

        jobArch = distTroveFlavor.members[deps.DEP_CLASS_IS].members.keys()[0]

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
                            val = self.project.resolveBuildTrove(n, v, f,
                                    buildTroveVersion, buildTroveFlavor)
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
        try:
            trove, version, flavor = build.getTrove()
            versionString = "%s/%s" % \
                (versions.ThawVersion(version).trailingLabel(),
                    versions.ThawVersion(version).trailingRevision())
            files = build.getFiles()

            fileIds = list(set([x['fileId'] for x in files]))
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
                amiS3Manifest = amiS3Manifest)

    @writersOnly
    def newPackage(self, auth):
        # XXX a test case had params passed into this thing. figure out which one's busted
        #Create the temporary storage
        #### If the directory prefix changes, you must change the cgi script
        #### and the poller too

        sessionHandle = self.client.createPackageTmpDir()
        versions = self.project.getProductVersionList()
        return self._write('createPackage', message = '',
                sessionHandle = sessionHandle,
                versions = versions, versionId = -1)

    @writersOnly
    def upload_iframe(self, auth, uploadId, fieldname):
        return self._write('uploadPackageFrame', uploadId = uploadId,
                fieldname = fieldname, project = self.project.hostname)

    @writersOnly
    @strFields(sessionHandle=None, upload_url='')
    @intFields(versionId=None)
    def getPackageFactories(self, auth, sessionHandle, versionId, upload_url):
        factories = self.client.getPackageFactories(self.project.getId(), sessionHandle, versionId, upload_url)
        return self._write('createPackageInterview',
                sessionHandle = sessionHandle, factories = factories,
                message = None)

    @writersOnly
    @strFields(sessionHandle=None, factoryHandle=None)
    def savePackage(self, auth, sessionHandle, factoryHandle, **kwargs):
        #It is assumed that the package creator service will validate the input
        self.client.savePackage(sessionHandle, factoryHandle, kwargs)
        return self._write('buildPackage', sessionHandle = sessionHandle,
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
        dataDict.update(url=self.project.getUrl() + 'latestRelease')
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
                    message = "Unpublishing your release will hide the release from the public, as well as allow you edit the contents of the release. Are you sure you want to unpublish your release?",
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
            self._redirect('http://%s%sproject/%s/releases' % (self.cfg.siteHost, self.cfg.basePath, self.project.getHostname()))
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
        return self._write("mailingLists", lists=lists, mailhost=self.cfg.MailListBaseURL, hostname=hostname, messages=messages)

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
            'desc': self.project.getDesc()
        }
        return self._write("editProject", kwargs = kwargs)

    @strFields(projecturl = '', desc = '', name = '',
               commitEmail = '')
    @ownerOnly
    def processEditProject(self, auth, projecturl, desc, name,
                           commitEmail):
        pText = getProjectText()
        if not name:
            self._addErrors("You must supply a %s title"%pText.lower())

        if not self._getErrors():
            try:
                self.project.editProject(projecturl, desc, name)
                self.project.setCommitEmail(commitEmail)
            except DuplicateItem:
                self._addErrors("%s title conflicts with another %s"%(pText.title(), pText.lower()))

        if self._getErrors():
            kwargs = {'projecturl': projecturl, 'desc': desc, 'name': name,
                      'commitEmail': commitEmail}
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
        
        if not isNew:
            kwargs.update(self.client.getProductVersion(id))
            pd = self.client.getProductDefinitionForVersion(id)
        else:
            valueToIdMap = buildtemplates.getValueToTemplateIdMap();
            pd = proddef.ProductDefinition()
            helperfuncs.addDefaultStagesToProductDefinition(pd)

        return self._write("editVersion",
                isNew = isNew,
                id=id,
                visibleBuildTypes = self._productVersionAvaliableBuildTypes(),
                buildTemplateValueToIdMap = buildtemplates.getValueToTemplateIdMap(),
                productDefinition = pd,
                kwargs = kwargs)

    @intFields(id = -1)
    @strFields(name = '', description = '', baseFlavor = '', action = 'Cancel')
    @requiresAuth
    @ownerOnly
    def processEditVersion(self, auth, id, name, description, action, baseFlavor,
            **kwargs):

        isNew = (id == -1)

        if not name:
            self._addErrors("Missing version")

        # Load the current project definition for this version
        # If this is new, use our template product definition
        # generator. Otherwise, just get it from the repository.
        if isNew:
            pd = proddef.ProductDefinition()
        else:
            version = self.client.getProductVersion(id)
            pd = self.client.getProductDefinitionForVersion(id)

        pd = helperfuncs.sanitizeProductDefinition(
                    self.project.name,
                    self.project.description,
                    self.project.hostname,
                    self.project.domainname,
                    self.project.shortname,
                    name,
                    description,
                    self.cfg.namespace,
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

        # Process upstream sources
        # XXX ProductDefinition object needs clearUpstreamSources()
        pd.upstreamSources = proddef._UpstreamSources()
        usources = collatedDict.get('pdusource',{})
        for us in usources:
            troveName, label = self._getValidatedUpstreamSource(us)
            # add regardless of errors.  if an error occurred, we want the user
            # to see what they entered.
            pd.addUpstreamSource(troveName, label)

        # Process build definitions
        buildDefsList = collatedDict.get('pdbuilddef',[])

        # Currently, stageNames for each build is
        # defined as the full set of stages.
        stageNames = [x.name for x in pd.getStages()]

        # XXX ProductDefinition object needs clearBuildDefinitions()
        pd.buildDefinition = proddef._BuildDefinition()

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
            buildSettings = dict([(buildtemplates.reversedOptionNameMap.get(k,k),v) for k, v in buildSettings.iteritems()])

            pd.addBuildDefinition(name=buildName,
                baseFlavor=builddef.get('baseFlavor'),
                imageType=pd.imageType(xmlTagName, buildSettings),
                stages = stageNames)

        for ve in validationErrors:
            self._addErrors(str(ve))

        if not self._getErrors():
            if id == -1:
                id = self.client.addProductVersion(self.project.id,
                        name, description)
            else:
                self.client.editProductVersion(id, description)

            assert(id != -1)
            self.client.setProductDefinitionForVersion(id, pd)

            if kwargs.has_key('linked'):
                # we got here from the "create a product menu" so output
                # accordingly.  Note that the value of linked is the name
                # of the project.
                self._setInfo("Successfully created %s '%s' version '%s'" % \
                              (getProjectText().lower(), self.project.name,
                               name))
            else:
                if isNew:
                    action = "Created"
                else:
                    action = "Updated"
                self._setInfo("%s %s version '%s'" % \
                              (action, getProjectText().lower(), name))
            self._predirect()
        else:
            kwargs.update(name=name, description=description)
            return self._write("editVersion", 
               isNew = isNew,
               id=id,
               visibleBuildTypes = self._productVersionAvaliableBuildTypes(),
               buildTemplateValueToIdMap = buildtemplates.getValueToTemplateIdMap(),
               productDefinition = pd, kwargs = kwargs)
            
    def _productVersionAvaliableBuildTypes(self):
        """
        Get a list of the available build types for build defs
        """
        return helperfuncs.getBuildDefsAvaliableBuildTypes(
            self.client.getAvailableBuildTypes())
            
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

    def members(self, auth):
        self.projectMemberList = self.project.getMembers()
        if (self.userLevel == userlevels.OWNER or auth.admin):
            reqList = self.client.listJoinRequests(self.project.getId())
        else:
            reqList = []
        return self._write("members",
                userHasReq = self.client.userHasRequested(self.project.getId(),
                    auth.userId),
                reqList = reqList)

    @requiresAuth
    def adopt(self, auth):
        self.project.adopt(auth, self.cfg.EnableMailLists, self.cfg.MailListBaseURL, self.cfg.MailListPass)
        self._setInfo("You have successfully adopted %s" % self.project.getNameForDisplay())
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
            self._setInfo("You are now watching %s" % self.project.getNameForDisplay())
        self._predirect("members")

    @requiresAuth
    def unwatch(self, auth):
        if self.userLevel == userlevels.USER:
            self.project.delMemberById(auth.userId)
            self._setInfo("You are no longer watching %s" % self.project.getNameForDisplay())
        self._predirect("members")

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

    @requiresAuth
    @intFields(userId = None)
    def viewJoinRequest(self, auth, userId):
        user = self.client.getUser(userId)
        return self._write('viewJoinRequest', userId = userId,
               username = user.getUsername(),
               projectId = self.project.getId(),
               comments = self.client.getJoinReqComments(self.project.getId(),
                   userId))

    @requiresAuth
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

    @requiresAuth
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
    @boolFields(confirmed = False)
    @dictFields(yesArgs = {})
    def resign(self, auth, confirmed, **yesArgs):
        if confirmed:
            self.project.delMemberById(auth.userId)
            self._setInfo("You have resigned from %s %s" % \
                    (getProjectText().lower(), self.project.getNameForDisplay()))
            self._redirect('http://%s%s' % (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self._write("confirm", message = "Are you sure you want to resign from this %s?"%getProjectText().lower(),
                yesArgs = {'func':'resign', 'confirmed':'1'}, noLink = "/")

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

    def help(self, auth):
        return self._write("help")

    @intFields(projectId = None)
    @strFields(operation = None)
    @requiresAdmin
    def processProjectAction(self, auth, projectId, operation):
        pText = getProjectText()
        project = self.client.getProject(projectId)

        if operation == "project_hide":
            if not project.hidden:
                self.client.hideProject(projectId)
                self._setInfo("%s hidden"%pText.title())
            else:
                self._addErrors("%s is already hidden"%pText.title())
        elif operation == "project_unhide":
            if project.hidden:
                self.client.unhideProject(projectId)
                self._setInfo("%s is now visible"%pText.title())
            else:
                self._addErrors("%s is already visible"%pText.title())
        else:
            self._addErrors("Please select a valid %s administration option from the menu"%pText.lower())

        return self._predirect()
