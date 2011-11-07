#
# Copyright (c) 2011 rPath, Inc.
#

from mint import userlevels
from mint.mint_error import ItemNotFound

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
    pass
