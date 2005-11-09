#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import email
import kid
import os
import re
import sys
from mod_python import apache

from mint import database
from mint import mailinglists
from mint import releases
from mint import releasetypes
from mint import userlevels
from mint import users
from mint import jobs
from mint import jobstatus

from repository import netclient
import versions
from deps import deps

from webhandler import WebHandler, normPath
from decorators import ownerOnly, requiresAuth, requiresAdmin, mailList, redirectHttp
from web import fields
from web.fields import strFields, intFields, listFields, boolFields
from mint.users import sendMailWithChecks

from mint.releases import RDT_STRING, RDT_BOOL, RDT_INT

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
            return self._404

        # redirect endorsed (external) projects
        # to the right url if accessed incorrectly,
        # and vice-versa for internal (unendorsed) projects
        if self.project.external:
            if self.req.hostname != self.cfg.siteHost:
                self.req.log_error("%s %s accessed incorrectly; referer: %s" % \
                    (self.req.hostname, self.req.unparsed_uri, self.req.headers_in.get('referer', 'N/A')))
                return self._redirector("http://" + self.cfg.siteHost + self.req.unparsed_uri)
        else:
            if self.req.hostname != self.cfg.projectSiteHost:
                self.req.log_error("%s %s accessed incorrectly; referer: %s" % \
                    (self.req.hostname, self.req.unparsed_uri, self.req.headers_in.get('referer', 'N/A')))
                return self._redirector("http://" + self.cfg.projectSiteHost + self.req.unparsed_uri)

        self.userLevel = self.project.getUserLevel(self.auth.userId)

        #Take care of hidden projects
        if self.project.hidden and self.userLevel == userlevels.NONMEMBER:
            return self._404
        
        # add the project name to the base path
        self.basePath += "project/%s" % (cmds[0])
        self.basePath = normPath(self.basePath)

        if not cmds[1]:
            return self.projectPage
        try:
            method = self.__getattribute__(cmds[1])
        except AttributeError:
            return self._404

        return method

    @redirectHttp
    def projectPage(self, auth):
        self._write("projectPage", userHasReq = self.client.userHasRequested(self.project.getId(), auth.userId))
        return apache.OK

    def conaryUserCfg(self, auth):
        self._write("conaryUserCfg")
        return apache.OK

    def conaryDevelCfg(self, auth):
        self._write("conaryDevelCfg")
        return apache.OK

    def releases(self, auth):
        releases = self.project.getReleases(showUnpublished = True)
        publishedReleases = [x for x in releases if x.getPublished()]

        #releasesByTrove = {}
        #for release in releases:
        #    l = releasesByTrove.setdefault(release.getTroveName(), [])
        #    l.append(release)
        #for l in releasesByTrove.values():
        #    l.sort(key = lambda x: x.getTroveVersion(), reverse = True)

        self._write("releases", releases = releases, publishedReleases = publishedReleases)
        return apache.OK

    @ownerOnly
    def groups(self, auth):
        releases = self.project.getReleases(showUnpublished = True)
        publishedReleases = [x for x in releases if x.getPublished()]
        groupTrovesInProject = self.client.listGroupTrovesByProject(self.project.id)
            
        self._write("groups", publishedReleases = publishedReleases,
                    groupTrovesInProject = groupTrovesInProject)
        return apache.OK

    @ownerOnly
    def newGroup(self, auth):
        self._write("newGroup", errors = [], kwargs = {})
        return apache.OK

    @ownerOnly
    @strFields(groupName = "", version = "", description = "")
    def createGroup(self, auth, groupName, version, description):
        errors = []
        groupName = "group-" + groupName

        # validate version
        try:
            versions.Revision(version + "-1-1")
        except versions.ParseError, e:
            errors.append("Error parsing version string: %s" % version)

        # validate group name
        if not re.match("group-[a-zA-Z0-9\-_]+$", groupName):
            errors.append("Invalid group trove name: %s" % groupName)

        if not errors:
            # do stuff
            gt = self.client.createGroupTrove(self.project.getId(), groupName,
                version, description, True)
            gtId = gt.getId()
            return self._redirect("editGroup?id=%d" % gtId)
        else:
            kwargs = {'groupName': groupName, 'version': version}
            self._write("newGroup", errors = errors, kwargs = kwargs)
            return apache.OK
    
    @ownerOnly
    @intFields(id = None)
    def editGroup(self, auth, id):
        curGroupTrove = self.client.getGroupTrove(id)
        self.session['groupTroveId'] = id

        self._write("editGroup", curGroupTrove = curGroupTrove)
        return apache.OK

    @ownerOnly
    @intFields(id=None)
    @strFields(trove=None, version=None, flavor='', referer='')
    @boolFields(versionlocked=False)
    def addGroupTrove(self, auth, id, trove, version, flavor, referer, versionlocked):
        assert(id == self.session['groupTroveId'])
        curGroupTrove = self.client.getGroupTrove(id)
        curGroupTrove.addTrove(trove, version, '', '', versionlocked, False, False)
        if not referer:
            referer = project.getUrl()
        return self._redirect(referer)

    @ownerOnly
    @intFields(id=None, troveId=None)
    @strFields(referer='')
    def deleteGroupTrove(self, auth, id, troveId, referer):
        assert(id == self.session['groupTroveId'])
        curGroupTrove = self.client.getGroupTrove(id)
        curGroupTrove.delTrove(troveId)
        if not referer:
            referer = project.getUrl()
        return self._redirect(referer)

    @ownerOnly
    @intFields(id = None)
    def cookGroup(self, auth, id):
        curGroupTrove = self.client.getGroupTrove(id)
        
        recipe = curGroupTrove.getRecipe()
        job = curGroupTrove.getJob()
        if not job or (job and job.status not in (jobstatus.WAITING, jobstatus.RUNNING)):
            jobId = curGroupTrove.startCookJob()
        else:
            jobId = job.id

        self._write("cookGroup", jobId = jobId, recipe = recipe)
        return apache.OK
    
    @ownerOnly
    def newRelease(self, auth):
        self._write("newRelease", errors = [], kwargs = {})
        return apache.OK

    @ownerOnly
    @intFields(releaseId = -1, imageType = releasetypes.INSTALLABLE_ISO)
    @strFields(trove = "", releaseName = "")
    def editRelease(self, auth, releaseId, imageType, trove, releaseName):
        errors = []
        if imageType not in releasetypes.TYPES:
            errors.append("Invalid image type selected.")

        projectId = self.project.getId()
        if releaseId == -1:
            assert(projectId != -1)
            if '=' not in trove:
                errors.append("You must select a group trove.")

            if not errors:
                release = self.client.newRelease(projectId, releaseName)

                ilp = "%s conary.rpath.com@rpl:devel contrib.rpath.org@rpl:devel" % self.project.getLabel()
                release.setImageType(imageType)
                release.setDataValue("installLabelPath", ilp)
                trove, label = trove.split("=")
                label = versions.Label(label)
                version = None
                flavor = None
            else:
                kwargs = {'releaseId':      releaseId,
                          'imageType':      imageType,
                          'trove':          trove,
                          'releaseName':    releaseName}
                self._write("newRelease", errors = errors, kwargs = kwargs)
                return apache.OK
        else:
            release = self.client.getRelease(releaseId)
            if not release.getDataValue("installLabelPath"):
                ilp = "%s conary.rpath.com@rpl:devel contrib.rpath.org@rpl:devel" % self.project.getLabel()
                release.setDataValue("installLabelPath", ilp)
                
            trove, versionStr, flavor = release.getTrove()
            version = versions.ThawVersion(versionStr)
            label = version.branch().label()

        if self.project.external:
            cfg = self.project.getConaryConfig()
        else:
            cfg = self.project.getConaryConfig(overrideSSL = True, useSSL = self.cfg.SSL)
        nc = netclient.NetworkRepositoryClient(cfg.repositoryMap)
        leaves = nc.getAllTroveLeaves(cfg.repositoryMap.keys()[0], {trove: {None: None}})

        # group troves by major architecture
        def dictByArch(leaves, troveName):
            archMap = {}
            for v, flavors in reversed(sorted(leaves[troveName].items())):
                for f in flavors:
                    # skip broken groups that don't have an instruction set
                    if deps.DEP_CLASS_IS not in f.members:
                        continue
                    arch = f.members[deps.DEP_CLASS_IS].members.keys()[0]

                    l = archMap.setdefault(arch, [])
                    l.append((v, f, ))
            return archMap

        archMap = dictByArch(leaves, trove)
        versionFlavors = []
        for arch, vfList in archMap.items():
            for vf in vfList:
                versionFlavors.append(vf)
        versionFlavors.sort(key=lambda x: x[0], reverse=True)

        self._write("editRelease", trove = trove, version = version,
                                   flavor = deps.ThawDependencySet(flavor),
                                   label = label.asString(), release = release,
                                   archMap = archMap)
        return apache.OK
        
    @requiresAuth
    @intFields(releaseId = None)
    @strFields(trove = None, version = None,
               desc = "", mediaSize = "640")
    def editRelease2(self, auth, releaseId,
                     trove, version,
                     desc, mediaSize, **kwargs):
        release = self.client.getRelease(releaseId)

        version, flavor = version.split(" ")
        release.setTrove(trove, version, flavor)
        release.setDesc(desc)

        flavor = deps.ThawDependencySet(flavor)
        jobArch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        assert(jobArch in ('x86', 'x86_64'))

        # get the template from the release and handle any relevant args
        # remember that checkboxes don't pass args for unchecked boxxen
        template = release.getDataTemplate()
        for name in list(template):
            try:
                val = kwargs[name]
                if template[name][0] == RDT_BOOL:
                    val = True
                if template[name][0] == RDT_STRING:
                    val = str(val)
            except KeyError:
                if template[name][0] == RDT_BOOL:
                    val = False
                else:
                    val = template[name][1]
            release.setDataValue(name, val)

        try:
            job = self.client.startImageJob(releaseId)
        except jobs.DuplicateJob:
            pass

        return self._redirect(self.basePath + "release?id=%d" % releaseId)

    @intFields(releaseId = None)
    @ownerOnly
    def deleteRelease(self, auth, releaseId):
        release = self.client.getRelease(releaseId)
        release.deleteRelease()
        return self._redirect(self.basePath + "releases")

    @intFields(id = None)
    def release(self, auth, id):
        releases = self.project.getReleases(showUnpublished = True)
        publishedReleases = [x for x in releases if x.getPublished()]
        release = self.client.getRelease(id)

        try:
            trove, version, flavor = release.getTrove()
        except releases.TroveNotSet:
            return self._redirect(self.basePath + "editRelease?releaseId=%d" % release.getId())
        else:
            self._write("release", release = release,
                                   name = release.getName(),
                                   trove = trove, version = versions.ThawVersion(version),
                                   flavor = deps.ThawDependencySet(flavor),
                                   releaseId = id, projectId = self.project.getId(),
                                   publishedReleases = publishedReleases)
        return apache.OK

    @ownerOnly
    @intFields(releaseId = None)
    def publish(self, auth, releaseId):
        release = self.client.getRelease(releaseId)
        release.setPublished(True)

        return self._redirect(self.basePath + "release?id=%d" % releaseId)

    @ownerOnly
    @intFields(releaseId = None)
    def restartJob(self, auth, releaseId):
        self.client.startImageJob(releaseId)
        return self._redirect(self.basePath + "release?id=%d" % releaseId)

    def _mailingLists(self, auth, mlists, messages=[]):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        hostname = self.project.getHostname()
        lists = mlists.list_lists(hostname)
        self._write("mailingLists", lists=lists, mailhost=self.cfg.MailListBaseURL, hostname=hostname, messages=messages)
        return apache.OK

        
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
        mlists.server.subscribe(list, self.cfg.MailListPass, [auth.email], False, True)
        return self._mailingLists(auth, mlists, ['You have been subscribed to %s' % list])

    @requiresAuth
    @ownerOnly
    def editProject(self, auth):
        kwargs = {
            'projecturl': self.project.getProjectUrl(),
            'name': self.project.getName(),
            'desc': self.project.getDesc(),
        }
        self._write("editProject", errors = [], kwargs = kwargs)
        return apache.OK

    @strFields(projecturl = '', desc = '', name = '')
    @ownerOnly
    def processEditProject(self, auth, projecturl, desc, name):
        errors = []
        if not name:
            errors.append("You must supply a project title")
        if not errors:
            try:
                self.project.editProject(projecturl, desc, name)
            except database.DuplicateItem:
                errors.append("Project title conflicts with another project.")

        if errors:
            kwargs = {'projecturl': projecturl, 'desc': desc, 'name': name}
            self._write("editProject", kwargs = kwargs, errors = errors)
            return apache.OK
        else:
            return self._redirect(self.basePath)

    def members(self, auth):
        if (self.userLevel == userlevels.OWNER or auth.admin):
            reqList = self.client.listJoinRequests(self.project.getId())
        else:
            reqList = []
        self._write("members", reqList = reqList)
        return apache.OK

    @requiresAuth
    def adopt(self, auth):
        self.project.adopt(auth, self.cfg.MailListBaseURL, self.cfg.MailListPass)
        return self._redirect(self.basePath + "members")

    @strFields(username = None)
    @intFields(level = None)
    @ownerOnly
    def addMember(self, auth, username, level):
        self.project.addMemberByName(username, level)
        return self._redirect(self.basePath + "members")

    @requiresAuth
    def watch(self, auth):
        #some kind of check to make sure the user's not a member
        if self.userLevel == userlevels.NONMEMBER:
            self.project.addMemberByName(auth.username, userlevels.USER)
        return self._redirect(self.basePath)

    @requiresAuth
    @boolFields(confirmed=False)
    def unwatch(self, auth, confirmed):
        if confirmed:
            if self.userLevel == userlevels.USER:
                self.project.delMemberById(auth.userId)
            return self._redirect(self.basePath)
        else:
            self._write("confirm", message = "Are you sure you want to remove this project from your watch list?",
                yesLink = "unwatch?confirmed=1",
                noLink = "/")
            return apache.OK

    @strFields(comments = '')
    @intFields(keepReq = None)
    @requiresAuth
    def processJoinRequest(self, auth, comments, keepReq):
        projectId = self.project.getId()
        userId = auth.userId
        if(keepReq):
            self.client.setJoinReqComments(projectId, comments)
        else:
            self.client.deleteJoinRequest(projectId, userId)
        return self._redirect(self.basePath)

    @requiresAuth
    @intFields(userId = None)
    def viewJoinRequest(self, auth, userId):
        user = self.client.getUser(userId)
        self._write('viewJoinRequest', userId = userId, username = user.getUsername(), projectId = self.project.getId(), comments = self.client.getJoinReqComments(self.project.getId(), userId))
        return apache.OK

    @requiresAuth
    @intFields(makeOwner = False, makeDevel = False, reject = False, userId = None)
    def acceptJoinRequest(self, auth, userId, makeOwner, makeDevel, reject):
        projectId = self.project.getId()
        user = self.client.getUser(userId)
        if reject:
            self._write('rejectJoinRequest', userId = userId, username = user.getUsername())
            return apache.OK
        user = self.client.getUser(userId)
        username = user.getUsername()
        if (makeOwner):
            self.project.addMemberByName(username, userlevels.OWNER)
        elif (makeDevel):
            self.project.addMemberByName(username, userlevels.DEVELOPER)
        return self._redirect(self.basePath + "members")

    @requiresAuth
    @intFields(userId = None)
    @strFields(comments = '')
    def processJoinRejection(self, auth, userId, comments):
        if self.cfg.sendNotificationEmails:
            subject = "Membership Rejection Notice"
            body = "Your request to join the following project on %s:\n\n" % self.cfg.productName
            body += "%s\n\n" % self.project.getName()
            body += " has been rejected by the project's owner.\n\n"
            if comments:
                body += "Owner's comments:\n%s" % comments
            else:
                body += "The owner did not provide a reason for this rejection.\n"
            user = self.client.getUser(userId)
            sendMailWithChecks(self.cfg.adminMail, self.cfg.productName, user.getEmail(), subject, body)
        self.client.deleteJoinRequest(self.project.getId(), userId)
        return self._redirect(self.basePath + "members")

    @requiresAuth
    def joinRequest(self, auth):
        self._write("joinRequest", comments = self.client.getJoinReqComments(self.project.getId(), auth.userId) )
        return apache.OK

    @intFields(userId = None, level = None)
    @ownerOnly
    def editMember(self, auth, userId, level):
        self.project.updateUserLevel(userId, level)
        return self._redirect(self.basePath + "members")

    @intFields(userId = None)
    @ownerOnly
    def promoteMember(self, auth, userId):
        #USERS and DEVELOPERS can be promoted (see below)
        userDict = getUserDict(self.project.getMembers())
        for level in [userlevels.DEVELOPER, userlevels.USER]:
            for user in userDict[level]:
                if user[0] == userId:
                    levelidx = userlevels.LEVELS.index(level)
                    self.project.updateUserLevel(userId, userlevels.LEVELS[levelidx - 1])
                    return self._redirect(self.basePath + "members")
        return self._redirect(self.basePath + "members")

    @intFields(userId = None)
    @ownerOnly
    def demoteMember(self, auth, userId):
        #But only owners may be demoted.  Developers must be deleted. (see above)
        userDict = getUserDict(self.project.getMembers())
        for level in [userlevels.OWNER]:
            for user in userDict[level]:
                if user[0] == userId:
                    levelidx = userlevels.LEVELS.index(level)
                    self.project.updateUserLevel(userId, userlevels.LEVELS[levelidx + 1])
                    return self._redirect(self.basePath + "members")
        return self._redirect(self.basePath + "members")

    @intFields(id = None)
    @ownerOnly
    def delMember(self, auth, id):
        self.project.delMemberById(id)
        if self.project.getMembers() == []:
            self.project.orphan(self.cfg.MailListBaseURL, self.cfg.MailListPass)
        return self._redirect(self.basePath + "members")

    @requiresAuth
    @boolFields(confirmed = False)
    def resign(self, auth, confirmed):
        if confirmed:
            self.project.delMemberById(auth.userId)
            return self._redirect(self.basePath)
        else:
            self._write("confirm", message = "Are you sure you want to resign from this project?",
                yesLink = "resign?confirmed=1",
                noLink = "/")
        return apache.OK

    @strFields(feed= "releases")
    def rss(self, auth, feed):
        if feed == "releases":
            title = "%s releases" % self.project.getName()
            link = "%sproject/%s/releases" % \
                (self.cfg.basePath, self.project.getHostname())
            desc = "Current releases from %s" % self.project.getName()

            releases = self.project.getReleases()
            items = []
            for release in releases[:10]:
                item = {}
                item['title'] = "%s=%s" % (release.getTroveName(),
                    release.getTroveVersion().trailingRevision().asString())
                item['link'] = "%sproject/%s/release?id=%d" % \
                    (self.cfg.basePath, self.project.getHostname(), release.getId())
                item['content'] = "A new version of %s has been released: %s version %s." % \
                    (release.getName(), release.getTroveName(),
                     release.getTroveVersion().trailingRevision().asString())
                item['date_822'] = email.Utils.formatdate(release.getChangedTime())
                item['creator'] = "http://%s%s" % (self.siteHost, self.cfg.basePath)
                items.append(item)
        else:
            items = []
            title = "Invalid RSS feed style requested."
            link = ""
            desc = ""

        self._writeRss(items = items, title = title, link = link, desc = desc)
        return apache.OK
