#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import email
import kid
import os
import sys
from mod_python import apache

from mint import database
from mint import mailinglists
from mint import releasetypes
from mint import userlevels

from repository import netclient
import versions
from deps import deps

from webhandler import WebHandler, normPath
from decorators import ownerOnly, requiresAuth, requiresAdmin, mailList
from web import fields
from web.fields import strFields, intFields, listFields, boolFields

def getUserDict(members):
    users = { userlevels.DEVELOPER: [],
              userlevels.OWNER: [], }
    for userId, username, level in members:
        users[level].append((userId, username,))
    return users


class ProjectHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        
        cmds = self.cmd.split("/")

        try:
            self.project = self.client.getProjectByFQDN(cmds[0] + "." + self.cfg.domainName)
        except database.ItemNotFound:
            return self._404

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

    def projectPage(self, auth):
        self._write("projectPage", userHasReq = self.client.userHasRequested(self.project.getId(), auth.userId))
        return apache.OK

    def releases(self, auth):
        releases = self.project.getReleases(showUnpublished = True)

        #releasesByTrove = {}
        #for release in releases:
        #    l = releasesByTrove.setdefault(release.getTroveName(), [])
        #    l.append(release)
        #for l in releasesByTrove.values():
        #    l.sort(key = lambda x: x.getTroveVersion(), reverse = True)

        self._write("releases", releases = releases)
        return apache.OK

    @ownerOnly
    def newRelease(self, auth):
        self._write("newRelease")
        return apache.OK

    @ownerOnly
    @intFields(releaseId = -1, imageType = releasetypes.INSTALLABLE_ISO)
    @strFields(trove = "", releaseName = "")
    def editRelease(self, auth, releaseId, imageType, trove, releaseName):
        projectId = self.project.getId()
        if releaseId == -1:
            assert(projectId != -1)
            release = self.client.newRelease(projectId, releaseName)

            release.setImageType(imageType)
            trove, label = trove.split("=")
            label = versions.Label(label)
            version = None
            flavor = None
        else:
            release = self.client.getRelease(releaseId)

            trove, versionStr, flavor = release.getTrove()
            version = versions.ThawVersion(versionStr)
            label = version.branch().label()

        cfg = self.project.getConaryConfig()
        nc = netclient.NetworkRepositoryClient(cfg.repositoryMap)
        leaves = nc.getTroveLeavesByLabel({trove: {label: None}})

        # group troves by major architecture
        def dictByArch(leaves, troveName):
            archMap = {}
            for v, flavors in reversed(sorted(leaves[troveName].items())):
                for f in flavors:
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
                     desc, mediaSize):
        release = self.client.getRelease(releaseId)

        version, flavor = version.split(" ")
        release.setTrove(trove, version, flavor)
        release.setDesc(desc)

        flavor = deps.ThawDependencySet(flavor)
        jobArch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        assert(jobArch in ('x86', 'x86_64'))

        try:
            job = self.client.startImageJob(releaseId)
        except jobs.DuplicateJob:
            pass

        return self._redirect(self.basePath + "release?id=%d" % releaseId)

    @intFields(id = None)
    def release(self, auth, id):
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
                                   releaseId = id, projectId = self.project.getId())
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

    @mailList
    def mailingLists(self, auth, mlists):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        hostname = self.project.getHostname()
        lists = mlists.list_lists(hostname)
        self._write("mailingLists", lists=lists, mailhost=self.cfg.MailListBaseURL, hostname=hostname)
        return apache.OK

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
            return self._redirect(self.basePath + "mailingLists")
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
        return self._redirect(self.basePath + "mailingLists")

    @requiresAuth
    @strFields(list=None)
    @mailList
    def subscribe(self, auth, mlists, list):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        mlists.server.subscribe(list, self.cfg.MailListPass, [auth.email], False, True)
        return self._redirect(self.basePath + "mailingLists")

    @requiresAuth
    @ownerOnly
    def editProject(self, auth):
        self._write("editProject")
        return apache.OK

    @strFields(projecturl = '', desc = '')
    @ownerOnly
    def processEditProject(self, auth, projecturl, desc):
        self.project.editProject(projecturl, desc)
        return self._redirect(self.basePath)

    def members(self, auth):
        if (self.userLevel == userlevels.OWNER or auth.admin):
            reqList = self.client.listJoinRequests(self.project.getId())
        else:
            reqList = []
        self._write("members", reqList = reqList)
        return apache.OK

    def memberSettings(self, auth):
        self._write("memberSettings")
        return apache.OK

    @requiresAuth
    def adopt(self, auth):
        self.project.adopt(auth, self.cfg.MailListBaseURL, self.cfg.MailListPass)
        self._write("members", reqList = [])
        return apache.OK

    @strFields(username = None)
    @intFields(level = None)
    @ownerOnly
    def addMember(self, auth, username, level):
        self.project.addMemberByName(username, level)
        return self._redirect(self.basePath + "members")

    @strFields(comments = '')
    @requiresAuth
    def processJoinRequest(self, auth, comments):
        self.client.setJoinReqComments(self.project.getId(), auth.userId, comments)
        return self._redirect(self.basePath)

    @intFields(userId = None)
    def viewJoinRequest(self, auth, userId):
        user = self.client.getUser(userId)
        self._write('viewJoinRequest', userId = userId, username = user.getUsername(), projectId = self.project.getId(), comments = self.client.getJoinReqComments(self.project.getId(), userId))
        return apache.OK

    @intFields(makeOwner = False, makeDevel = False, reject = False, userId = None)
    def acceptJoinRequest(self, auth, userId, makeOwner, makeDevel, reject):
        projectId = self.project.getId()
        self.client.deleteJoinRequest(projectId, userId)
        user = self.client.getUser(userId)
        username = user.getUsername()
        if (makeOwner):
            self.project.addMemberByName(username, userlevels.OWNER)
        elif (makeDevel):
            self.project.addMemberByName(username, userlevels.DEVELOPER)
        return self._redirect(self.basePath + "members")

    @requiresAuth
    def joinRequest(self, auth):
        self._write("joinRequest", comments = self.client.getJoinReqComments(self.project.getId(), auth.userId) )
        return apache.OK

    @intFields(userId = None, level = None)
    @ownerOnly
    def editMember(self, auth, userId, level):
        userDict = getUserDict(self.project.getMembers())
        # if there is only one owner, and that
        # owner is being changed to a non-owner, fail.
        if len(userDict[userlevels.OWNER]) == 1 and \
           userDict[userlevels.OWNER][0][0] == userId and\
           level != userlevels.OWNER:
            raise users.LastOwner

        self.project.updateUserLevel(userId, level)
        return self._redirect(self.basePath + "members")

    @intFields(id = None)
    @ownerOnly
    def delMember(self, auth, id):
        userDict = getUserDict(self.project.getMembers())
        # if there are developers, only one owner, and that
        # owner is being deleted from the project, fail.
        if len(userDict[userlevels.DEVELOPER]) > 0 and \
           len(userDict[userlevels.OWNER]) == 1 and \
           userDict[userlevels.OWNER][0][0] == id:
            raise users.LastOwner

        self.project.delMemberById(id)
        if self.project.getMembers() == []:
            self.project.orphan(self.cfg.MailListBaseURL, self.cfg.MailListPass)
        return self._redirect(self.basePath + "members")

    @intFields(userId = None)
    @ownerOnly
    def memberSettings(self, auth, userId):
        user, level = self.client.getMembership(userId, self.project.getId())
        self._write("memberSettings", user = user, otherUserLevel = level, userId = userId)
        return apache.OK

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
        def writeRss(**values):
            path = os.path.join(self.cfg.templatePath, "rss20.kid")
            template = kid.load_template(path)
            t = template.Template(**values)
            self.req.content_type = "text/xml"
            t.write(self.req, encoding = "utf-8", output = "xml")

        if feed == "releases":
            title = "%s releases" % self.project.getName()
            link = "http://%s/project/%s/releases" % \
                (self.siteHost, self.project.getHostname())
            desc = "Current releases from %s" % self.project.getName()

            releases = self.project.getReleases()
            items = []
            for release in releases[:10]:
                item = {}
                item['title'] = "%s=%s" % (release.getTroveName(),
                    release.getTroveVersion().trailingRevision().asString())
                item['link'] = "http://%s/project/%s/release?id=%d" % \
                    (self.siteHost, self.project.getHostname(), release.getId())
                item['content'] = "A new version of %s has been released: %s version %s." % \
                    (release.getName(), release.getTroveName(),
                     release.getTroveVersion().trailingRevision().asString())
                item['date_822'] = email.Utils.formatdate(release.getChangedTime())
                item['creator'] = "http://%s/" % self.cfg.domainName
                items.append(item)
        else:
            items = []
            title = "Invalid RSS feed style requested."
            link = ""
            desc = ""

        writeRss(items = items, title = title, link = link, desc = desc)
        return apache.OK

