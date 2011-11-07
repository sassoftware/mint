#
# Copyright (c) 2011 rPath, Inc.
#

import email
from mint import buildtypes
from mint import userlevels
from mint.mint_error import ItemNotFound

from mint.web.fields import strFields
from mint.web.webhandler import WebHandler, normPath, HttpNotFound


def getUserDict(members):
    users = { userlevels.USER: [],
              userlevels.DEVELOPER: [],
              userlevels.OWNER: [], }
    for userId, username, level in members:
        users[level].append((userId, username,))
    return users

class BaseProjectHandler(WebHandler):

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


class ProjectHandler(BaseProjectHandler):
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

