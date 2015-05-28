#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from mint.lib import maillib
from mint import userlevels

from mint.rest.db import manager
class EmailNotifier(manager.Manager):

    def notify_UserProductEvent(self, event, userId, projectId, oldLevel=None,
                                userlevel=None):
        performer = self.auth.auth
        fqdn = self.db.getProductFQDNFromId(projectId)
        project = self.db.getProduct(fqdn.split('.')[0])
        username = self.db.getUsername(userId)
        # we need to get this user's email address even though it's != our  
        # account.
        user = self.db._getUser(username)

        userlevelname = ((userlevel >=0) and userlevels.names[userlevel] or\
                                             'Unknown')
        action = event[len('UserProduct'):]
        projectUrl = 'http://%s%sproject/%s/' %\
                      (self.cfg.siteHost,
                       self.cfg.basePath,
                       project.hostname)

        greeting = "Hello,"

        actionText = {'Removed':'has been removed from the "%s" project'%\
                       project.name,

                      'Added':'has been added to the "%s" project as %s %s' % (project.name, userlevelname == 'Owner' and 'an' or 'a', userlevelname),

                      'Changed':'has had its current access level changed to "%s" on the "%s" project' % (userlevelname, project.name)
                     }

        helpLink = """

Instructions on how to set up your build environment for this project can be found at http://wiki.rpath.com/

If you would not like to be %s %s of this project, you may resign from this project at %smembers""" % \
        (userlevelname == 'Developer' and 'a' or 'an',
            userlevelname, projectUrl)

        closing = 'If you have questions about the project, please contact the project owners.'

        adminHelpText = {'Removed':'',
                         'Added':'\n\nIf you would not like this account to be %s %s of this project, you may remove them from the project at %smembers' %\
                         (userlevelname == 'Developer' and 'a' or 'an', 
                          userlevelname, projectUrl),

                         'Changed':'\n\nIf you would not like this account to be %s %s of this project, you may change their access level at %smembers' %\
                         (userlevelname == 'Developer' and 'a' or 'an',
                          userlevelname, projectUrl)
                        }

        message = adminMessage = None
        if performer.userId != user.id:
            message = 'Your %s account "%s" ' % (self.cfg.productName, 
                                                 user.username)
            message += actionText[action] + '.'
            if action == "Added":
                message += helpLink

            adminMessage = 'The %s account "%s" ' % (self.cfg.productName,
                                                   user.username)
            adminMessage += actionText[action] + ' by the project owner "%s".' % (performer.username)
            adminMessage += adminHelpText[action]
        else:
            if action == 'Removed':
                message = 'You have resigned from the %s project "%s".' %\
                          (self.cfg.productName, project.name)
                adminMessage = 'The %s account "%s" has resigned from the "%s" project.' % (self.cfg.productName, user.username, project.name)
            elif action == 'Changed':
                message = 'You have changed your access level from Owner to Developer on the %s project "%s".' % (self.cfg.productName, project.name)
                adminMessage = 'The %s account "%s" ' % (self.cfg.productName,
                                                         user.username)
                adminMessage += actionText[action] + ' by the project owner "%s".' % (performer.username)
                adminMessage += adminHelpText[action]

        if self.cfg.sendNotificationEmails:
            if message:
                maillib.sendMail(self.cfg.adminMail, self.cfg.productName,
                               user.email,
                               "Your %s account" % \
                               self.cfg.productName,
                               '\n\n'.join((greeting, message, closing)))
            if adminMessage:
                memberList = self.db.listProductMembers(project.hostname)
                adminUsers = []
                for level in [userlevels.OWNER]:
                    for membership in memberList.members:
                        if membership.level == level:
                            user = self.db._getUser(membership.username)
                            adminUsers.append(user)
                             
                for usr in adminUsers:
                    if usr.username != user.username:
                        maillib.sendMail(self.cfg.adminMail, 
                                       self.cfg.productName,
                                       usr.email,
                                       "%s project membership modification" % \
                                       self.cfg.productName,
                                       '\n\n'.join((greeting, adminMessage)))

    notify_UserProductRemoved = notify_UserProductEvent
    notify_UserProductAdded = notify_UserProductEvent
    notify_UserProductChanged = notify_UserProductEvent
