#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import dns.resolver
import dns.exception
import email
import os
import re
import sys
from mod_python import apache

from mint import database
from mint import mailinglists
from mint import jobs
from mint import jobstatus
from mint import builds
from mint import buildtypes
from mint import userlevels
from mint import users

from mint import buildtemplates
from mint.builds import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
from mint.users import sendMailWithChecks
from mint.web.webhandler import WebHandler, normPath, HttpNotFound
from mint.web.decorators import ownerOnly, writersOnly, requiresAuth, \
        requiresAdmin, mailList, redirectHttp

from conary import conaryclient
from conary import conarycfg
from conary.deps import deps
from conary import versions
from conary.web.fields import strFields, intFields, listFields, boolFields, dictFields

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
        except database.ItemNotFound:
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

        #Take care of hidden projects
        if self.project.hidden and self.userLevel == userlevels.NONMEMBER and not self.auth.admin:
            raise HttpNotFound

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

    def _predirect(self, path = ""):
        self._redirect("http://%s%sproject/%s/%s" % (self.cfg.projectSiteHost, self.cfg.basePath, self.project.hostname, path))

    @redirectHttp
    def projectPage(self, auth):
        try:
            dns.resolver.query(self.project.getFQDN())
        except dns.exception.DNSException:
            canResolve = self.project.external
        else:
            canResolve = True

        return self._write("projectPage", canResolve = canResolve)

    def conaryUserCfg(self, auth):
        return self._write("conaryUserCfg")

    def conaryDevelCfg(self, auth):
        return self._write("conaryDevelCfg")

    def releases(self, auth):
        releases = [self.client.getPublishedRelease(x) for x in self.project.getPublishedReleases()]
        return self._write("pubreleases", releases = releases)

    def createRelease(self, auth):
        release = self.client.newPublishedRelease(self.project.id)
        release.name = self.project.name
        return self._write("editPubrelease", release = release,
                           isNewRelease = True)

    def builds(self, auth):
        builds = self.project.getBuilds()
        publishedBuilds = [x for x in builds if x.getPublished()]

        # Group versions by name or default name (based on group trove).
        # FIXME: this is a hack until we get a better way to do build
        # management.
        buildsByGroupTrove = {}
        for r in builds:
            k = r.getDefaultName()
            buildsByVersion = buildsByGroupTrove.has_key(k) and buildsByGroupTrove[k] or []
            buildsByVersion.append(r)
            buildsByVersion.sort(key = lambda x: x.getArch())
            buildsByGroupTrove[k] = buildsByVersion

        # return a list of items in buildsByGroupTrove for web display
        buildVersions = sorted(buildsByGroupTrove.items(),
            key = lambda x: x[1][0], # first item in the buildsByVersion
            cmp = lambda x, y: cmp(x.getChangedTime(), y.getChangedTime()),
            reverse = True)

        return self._write("builds", builds = builds,
                publishedBuilds = publishedBuilds,
                buildVersions = buildVersions)

    def groups(self, auth):
        builds = self.project.getBuilds()
        publishedBuilds = [x for x in builds if x.getPublished()]
        groupTrovesInProject = self.client.listGroupTrovesByProject(self.project.id)

        return self._write("groups", publishedBuilds = publishedBuilds,
            groupTrovesInProject = groupTrovesInProject)

    def _getBasicTroves(self):
        # XXX all of this is kind of a hardcoded hack that should be pulled out
        # into a config file somewhere, or something.
        cfg = conarycfg.ConaryConfiguration()
        cfg.dbPath = cfg.root = ":memory:"
        label = versions.Label('conary.rpath.com@rpl:1')

        repos = conaryclient.ConaryClient(cfg).getRepos()
        versionDict = repos.getTroveLeavesByLabel({'group-dist': {label: None}})['group-dist']
        latestVersion = None
        for version, flavorList in versionDict.iteritems():
            if latestVersion is None or version > latestVersion:
                latestVersion = version
                latestFlavor = flavorList[0]

        trove = repos.getTroves([('group-dist', latestVersion, latestFlavor)])[0]

        # mash the trove list into something usable
        troves = [(x[0], (x[1], x[2])) for x in trove.iterTroveList(strongRefs = True)]

        # pop group-core out of the list and stick it on the top
        troveNames = [x[0] for x in sorted(troves)]
        troveNames = [troveNames.pop(troveNames.index('group-core'))] + troveNames
        troveDict = dict(troves)

        metadata = {'group-core':           'A basic set of packages required for a functional system.',
                    'group-base':           'Basic but non-essential packages.',
                    'group-devel':          'Software development tools.',
                    'group-dist-base':      None,
                    'group-dist-extras':    'Some assorted extra packages.',
                    'group-gnome':          'The GNOME desktop environment.',
                    'group-kde':            'The KDE desktop environment.',
                    'group-netserver':      'Network servers, tools, and support.',
                    'group-xorg':           'The X.org windowing system.',
                    'group-compat32':       '32 bit compatibility packages. (for 64 bit systems)'}
        return troveNames, troveDict, metadata

    def newGroup(self, auth):
        troves, troveDict, metadata = self._getBasicTroves()

        return self._write("newGroup", kwargs = {},
                           troves = troves, troveDict = troveDict,
                           metadata = metadata)

    @strFields(groupName = "", version = "", description = "")
    @listFields(str, initialTrove = [])
    def createGroup(self, auth, groupName, version, description, initialTrove):
        fullGroupName = "group-" + groupName

        # validate version
        try:
            versions.Revision(version + "-1-1")
        except versions.ParseError, e:
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
            troves, troveDict, metadata = self._getBasicTroves()

            return self._write("newGroup", kwargs = kwargs,
                troves = troves, troveDict = troveDict, metadata = metadata)

    @intFields(id = None)
    def editGroup(self, auth, id):
        curGroupTrove = self.client.getGroupTrove(id)
        self.session['groupTroveId'] = id
        self.groupTrove = curGroupTrove
        # these are mutually exclusive
        if 'rMakeBuildId' in self.session:
            del self.session['rMakeBuildId']
        self.rMakeBuild = None

        self.groupProject = self.client.getProject(self.groupTrove.projectId)
        return self._write("editGroup", message = None, curGroupTrove = curGroupTrove)

    @intFields(id = None)
    @strFields(version = None, description = '')
    @listFields(str, components = [])
    def editGroup2(self, auth, id, version, description, components, **kwargs):
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

        curGroupTrove.refresh()
        curGroupTrove.setRemovedComponents(components)
        self._setInfo('Changes saved successfully')
        self._predirect("editGroup?id=%d" % id)

    @strFields(referer = None)
    def closeCurrentGroup(self, auth, referer):
        if 'groupTroveId' in self.session:
            del self.session['groupTroveId']
            self.session.save()
        self._redirect("http://%s%s" % (self.cfg.siteHost, referer))

    @dictFields(yesArgs = {})
    @boolFields(confirmed=False)
    def deleteGroup(self, auth, confirmed, **yesArgs):
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
    def addGroupTrove(self, auth, id, trove, version, flavor, referer, versionLock, projectName):
        curGroupTrove = self.client.getGroupTrove(id)
        if version != '':
            curGroupTrove.addTrove(trove, version, '', '', versionLock, False, False)
        else:
            curGroupTrove.addTroveByProject(trove, projectName, '', '', versionLock, False, False)
        if not referer:
            referer = project.getUrl()
            self._redirect(referer)
        self._redirect("http://%s%s" % (self.cfg.siteHost, referer))

    @intFields(id=None, troveId=None)
    @strFields(referer='')
    def deleteGroupTrove(self, auth, id, troveId, referer):
        """Remove a trove from a group trove."""
        curGroupTrove = self.client.getGroupTrove(id)
        curGroupTrove.delTrove(troveId)
        if not referer:
            referer = project.getUrl()
            self._redirect(referer)
        self._redirect("http://%s%s" % (self.cfg.siteHost, referer))

    @intFields(id = None)
    def pickArch(self, auth, id):
        return self._write("pickArch", groupTroveId = id)

    @intFields(id = None)
    @listFields(str, flavor = ['1#x86'])
    def cookGroup(self, auth, flavor, id):
        curGroupTrove = self.client.getGroupTrove(id)

        arch = deps.mergeFlavorList([deps.ThawFlavor(x) for x in flavor]).freeze()
        job = curGroupTrove.getJob()
        if not job or (job and job.status not in (jobstatus.WAITING, jobstatus.RUNNING)):
            jobId = curGroupTrove.startCookJob(arch)
        else:
            jobId = job.id

        if 'groupTroveId' in self.session:
            del self.session['groupTroveId']

        return self._write("cookGroup", jobId = jobId,
            curGroupTrove = curGroupTrove)

    @writersOnly
    def newBuild(self, auth):

        return self._write("editBuild",
            buildId = None,
            name = self.project.getName(),
            desc = "",
            buildType = buildtypes.INSTALLABLE_ISO,
            defaultTemplate = buildtypes.INSTALLABLE_ISO,
            templates = buildtemplates.getDisplayTemplates(),
            dataDict = {},
            trove = None,
            troveName = None,
            label = None,
            versionStr = None,
            version = None,
            flavor = None,
            arch = None,
            kwargs = {})

    @writersOnly
    @intFields(buildId = -1)
    @strFields(trove = "")
    def editBuild(self, auth, buildId, trove):

        build = self.client.getBuild(buildId)

        troveName, version, flavor = build.getTrove()
        versionStr = versions.ThawVersion(version)
        label = versionStr.branch().label()
        thawedFlavor = deps.ThawFlavor(flavor)
        arch = thawedFlavor.members[deps.DEP_CLASS_IS].members.keys()[0]

        return self._write("editBuild",
            buildId = buildId,
            name = build.getName(),
            desc = build.getDesc(),
            buildType = build.getBuildType(),
            defaultTemplate = buildtypes.INSTALLABLE_ISO,
            templates = buildtemplates.getDisplayTemplates(),
            dataDict = build.getDataDict(),
            trove = trove,
            troveName = troveName,
            label = label,
            versionStr = versionStr.asString(),
            version = version,
            flavor = flavor,
            arch = arch,
            kwargs = {})

    @requiresAuth
    @intFields(buildId = None)
    @strFields(trove = None, version = None, name = "", desc = "")
    def saveBuild(self, auth, buildId, trove, version, desc, name,
                    **kwargs):
        if not buildId:
            build = self.client.newBuild(self.project.id, name)
            buildId = build.id
        else:
            build = self.client.getBuild(buildId)

        job = build.getJob()
        if job and job.status in (jobstatus.WAITING, jobstatus.RUNNING):
            self._addErrors("You cannot alter this build because a "
                            "conflicting image is currently being generated.")
            self._predirect("build?id=%d" % buildId)
            return

        trove, label = trove.split("=")
        version, flavor = version.split(" ")
        build.setTrove(trove, version, flavor)
        build.setName(name)
        build.setDesc(desc)

        flavor = deps.ThawFlavor(flavor)
        jobArch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        assert(jobArch in ('x86', 'x86_64'))

        # handle buildType check box state changes
        buildType = int(kwargs['buildtype'])

        build.setBuildType(buildType)

        # get the template from the build and handle any relevant args
        # remember that checkboxes don't pass args for unchecked boxxen
        template = build.getDataTemplate()
        for name in list(template):
            try:
                val = kwargs[name]
                if template[name][0] == RDT_BOOL:
                    val = True
                if template[name][0] in (RDT_STRING, RDT_ENUM):
                    val = str(val)
                if template[name][0] == RDT_INT:
                    val = int(val)
            except KeyError:
                if template[name][0] == RDT_BOOL:
                    val = False
                else:
                    val = template[name][1]
            build.setDataValue(name, val)

        try:
            job = self.client.startImageJob(buildId)
        except jobs.DuplicateJob:
            pass

        self._predirect("build?id=%d" % buildId)

    @intFields(buildId = None)
    @writersOnly
    def deleteBuild(self, auth, buildId):
        build = self.client.getBuild(buildId)
        build.deleteBuild()
        self._predirect("build")

    @intFields(id = None)
    def build(self, auth, id):
        builds = self.project.getBuilds()
        publishedBuilds = [x for x in builds if x.getPublished()]
        build = self.client.getBuild(id)
        buildInProgress = False
        if auth.authorized:
            buildJob = build.getJob()
            if buildJob:
                buildInProgress = \
                        (buildJob.getStatus() <= jobstatus.RUNNING)

        try:
            trove, version, flavor = build.getTrove()
            files = build.getFiles()
        except builds.TroveNotSet:
            self._predirect("editBuild?buildId=%d" % build.id)
        else:
            return self._write("build", build = build,
                name = build.getName(),
                isPublished = build.getPublished(),
                trove = trove, version = versions.ThawVersion(version),
                flavor = deps.ThawFlavor(flavor),
                buildId = id, projectId = self.project.getId(),
                publishedBuilds = publishedBuilds,
                files = files,
                buildInProgress = buildInProgress)

    @ownerOnly
    @intFields(buildId = None)
    def publish(self, auth, buildId):
        build = self.client.getBuild(buildId)
        build.setPublished(True)

        self.predirect("build?id=%d" % buildId)

    @ownerOnly
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
        if not self.cfg.EnableMailLists:
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
    def deleteList(self, auth, mlists, list):
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
            'name': self.project.getName(),
            'desc': self.project.getDesc(),
            'branch': self.project.getLabel().split('@')[1],
        }
        return self._write("editProject", kwargs = kwargs)

    @strFields(projecturl = '', desc = '', name = '', branch = '')
    @ownerOnly
    def processEditProject(self, auth, projecturl, desc, name, branch):
        if not name:
            self._addErrors("You must supply a project title")
        try:
            host = versions.Label(self.project.getLabel()).getHost()
            label = host + '@' + branch
            versions.Label(label)
        except versions.ParseError:
            self._addErrors("Invalid branch name")

        if not self._getErrors():
            try:
                self.project.editProject(projecturl, desc, name)

                # this is a little bit nasty because the label API
                # needs some work.
                oldLabel = self.project.getLabel()
                if oldLabel != label:
                    labelId = self.project.getLabelIdMap()[oldLabel]
                    oldLabel, oldUrl, oldUser, oldPass = self.client.server.getLabel(labelId)
                    self.project.editLabel(labelId, label, oldUrl, oldUser, oldPass)
            except database.DuplicateItem:
                self._addErrors("Project title conflicts with another project")

        if self._getErrors():
            kwargs = {'projecturl': projecturl, 'desc': desc, 'name': name,
                'branch': self.project.getLabel().split('@')[1]}
            return self._write("editProject", kwargs = kwargs)
        else:
            self._setInfo("Updated project %s" % name)
            self._predirect()

    def members(self, auth):
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
            self._setInfo("You have are now watching %s" % self.project.getNameForDisplay())
        self._predirect("members")

    @requiresAuth
    def unwatch(self, auth):
        if self.userLevel == userlevels.USER:
            self.project.delMemberById(auth.userId)
            self._setInfo("You have are no longer watching %s" % self.project.getNameForDisplay())
        self._predirect("members")

    @strFields(comments = '')
    @intFields(keepReq = None)
    @requiresAuth
    def processJoinRequest(self, auth, comments, keepReq):
        projectId = self.project.getId()
        userId = auth.userId
        if(keepReq):
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
    @intFields(makeOwner = False, makeDevel = False, reject = False, userId = None)
    def acceptJoinRequest(self, auth, userId, makeOwner, makeDevel, reject):
        projectId = self.project.getId()
        user = self.client.getUser(userId)
        username = user.getUsername()
        if reject:
            return self._write('rejectJoinRequest', userId = userId,
                    username = user.getUsername())
        if (makeOwner):
            self.project.addMemberByName(username, userlevels.OWNER)
            self._setInfo("User %s has been added as an owner to %s" % \
                    (username, self.project.getNameForDisplay()))
        elif (makeDevel):
            self.project.addMemberByName(username, userlevels.DEVELOPER)
            self._setInfo("User %s has been added as a developer to %s" % \
                    (username, self.project.getNameForDisplay()))
        self._predirect("members")

    @requiresAuth
    @intFields(userId = None)
    @strFields(comments = '')
    def processJoinRejection(self, auth, userId, comments):
        user = self.client.getUser(userId)
        if self.cfg.sendNotificationEmails:
            subject = "Membership Rejection Notice"
            body = "Your request to join the following project on %s:\n\n" % self.cfg.productName
            body += "%s\n\n" % self.project.getName()
            body += " has been rejected by the project's owner.\n\n"
            if comments:
                body += "Owner's comments:\n%s" % comments
            else:
                body += "The owner did not provide a reason for this rejection.\n"
            sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, user.getEmail(), subject, body)
        self.client.deleteJoinRequest(self.project.getId(), userId)
        self._setInfo("Join request for user %s has been rejected " \
                "for project %s" % (user.getUsername(), \
                self.project.getNameForDisplay()))
        self._predirect("members")

    @requiresAuth
    def joinRequest(self, auth):
        return self._write("joinRequest", comments = self.client.getJoinReqComments(self.project.getId(), auth.userId) )

    @intFields(userId = None, level = None)
    @ownerOnly
    def editMember(self, auth, userId, level):
        user = self.client.getUser(userId)
        self.project.updateUserLevel(userId, level)
        self._setInfo("User %s has been updated for project %s" % \
                (user.getUsername(), self.project.getNameForDisplay()))
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
        self._addErrors("User %s not a member of project %s" % \
                (user.getUsername(), self.project.getNameForDisplay()))
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
        self._addErrors("User %s not a member of project %s" % \
                (user.getUsername(), self.project.getNameForDisplay()))
        self._predirect("members")

    @intFields(id = None)
    @ownerOnly
    def delMember(self, auth, id):
        user = self.client.getUser(id)
        self.project.delMemberById(id)
        msg = "User %s deleted from project %s" % \
                (user.getName(), self.project.getNameForDisplay())
        if self.project.getMembers() == []:
            self.project.orphan(self.cfg.EnableMailLists, self.cfg.MailListBaseURL, self.cfg.MailListPass)
            msg += " (project has been orphaned)"
        self._setInfo(msg)
        self._predirect("members")

    @requiresAuth
    @boolFields(confirmed = False)
    @dictFields(yesArgs = {})
    def resign(self, auth, confirmed, **yesArgs):
        if confirmed:
            self.project.delMemberById(auth.userId)
            self._setInfo("You have resigned from project %s" % \
                    self.project.getNameForDisplay())
            self._redirect('http://%s%s' % (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self._write("confirm", message = "Are you sure you want to resign from this project?",
                yesArgs = {'func':'resign', 'confirmed':'1'}, noLink = "/")

    @strFields(feed= "builds")
    def rss(self, auth, feed):
        if feed == "builds":
            title = "%s builds" % self.project.getName()
            link = "http://%s%sproject/%s/builds" % \
                (self.cfg.siteHost, self.cfg.basePath, self.project.getHostname())
            desc = "Current builds from %s" % self.project.getName()

            builds = self.project.getBuilds()
            items = []
            for build in builds[:10]:
                item = {}
                item['title'] = "%s=%s" % (build.getTroveName(),
                    build.getTroveVersion().trailingRevision().asString())
                item['link'] = "http://%s%sproject/%s/build?id=%d" % \
                    (self.cfg.siteHost, self.cfg.basePath, self.project.getHostname(), build.getId())
                item['content'] = "A new version of %s has been buildd: %s version %s." % \
                    (build.getName(), build.getTroveName(),
                     build.getTroveVersion().trailingRevision().asString())
                item['date_822'] = email.Utils.formatdate(build.getChangedTime())
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
        project = self.client.getProject(projectId)

        if operation == "project_hide":
            if not project.hidden:
                self.client.hideProject(projectId)
                self._setInfo("Project hidden")
            else:
                self._addErrors("Project is already hidden")
        elif operation == "project_unhide":
            if project.hidden:
                self.client.unhideProject(projectId)
                self._setInfo("Project is now visible")
            else:
                self._addErrors("Project is already visible")
        else:
            self._addErrors("Please select a valid project administration option from the menu")

        return self._predirect()
