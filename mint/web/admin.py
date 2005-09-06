#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#

import sys
from mod_python import apache

from mint import mint_error
from webhandler import WebHandler

class AdminHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        if not self.auth.admin:
            raise mint_error.PermissionDenied
   
        return self.adminHandler

    def adminHandler(self, *args, **kwargs):
        operation = kwargs.get('operation', '')
        if not operation:
            return self._administer(*args, **kwargs)
            
        return self.__getattribute__('_admin_%s'%operation)(*args, **kwargs)
        
    def _admin_user(self, *args, **kwargs):
        #get a list of all users in a format suitable for producing a
        #dropdown or multi-select list
        userlist = self.client.getUsersList()
        self._write('admin/user', userlist=userlist, kwargs = kwargs)
        return apache.OK

    def _admin_user_cancel(self, *args, **kwargs):
        self.client.removeUserAccount(kwargs['userId'])
        kwargs['extraMsg'] = "User account deleted"
        return self._admin_user(*args, **kwargs)

    def _admin_user_reset_password(self, *args, **kwargs):
        self._resetPasswordById(kwargs['userId'])
        kwargs['extraMsg'] = "User password reset"
        return self._admin_user(*args, **kwargs)

    def _admin_project(self, *args, **kwargs):
        #Get a list of all the projects in a format suitable for producing
        #a dropdown or multi-select list.
        projects = self.client.getProjectsList()

        self._write('admin/project', projects = projects, kwargs = kwargs)
        return apache.OK

    def _admin_project_delete(self, *args, **kwargs):
        # XXX Go through with it.  This functionality may be added in some later release
        return self._admin_project(*args, **kwargs)

    def _admin_project_disable(self, *args, **kwargs):
        self.client.disableProject(kwargs['projectId'])
        kwargs['extraMsg'] = "Project disabled"
        return self._admin_project(*args, **kwargs)

    def _admin_project_enable(self, *args, **kwargs):
        self.client.enableProject(kwargs['projectId'])
        kwargs['extraMsg'] = "Project enabled"
        return self._admin_project(*args, **kwargs)

    def _admin_project_jump(self, page, **kwargs):
        name = self.client.getProject(kwargs['projectId']).getHostname()
        return self._redirect('/project/%s/%s' % (name, page))

    def _admin_project_maillists(self, *args, **kwargs):
        return self._admin_project_jump('mailingLists', **kwargs)

    def _admin_project_edit(self, *args, **kwargs):
        return self._admin_project_jump('editProject', **kwargs)

    def _admin_project_change_members(self, *args, **kwargs):
        return self._admin_project_jump('members', **kwargs)

    def _admin_notify(self, *args, **kwargs):
        self._write('admin/notify', kwargs=kwargs)
        return apache.OK

    def _admin_notify_send(self, *args, **kwargs):
        #send the message
        kwargs['errors'] = []
        if not kwargs.get('subject', None):
            kwargs['errors'].append('You must supply a subject')
        if not kwargs.get('body', None):
            kwargs['errors'].append('You must supply a message body')
        if not kwargs['errors']:
            try:
                returner = self.client.notifyUsers(kwargs['subject'], kwargs['body'])
                kwargs['extraMsg'] = 'Message sent successfully'
            except Exception, e:
                kwargs['errors'].append('An unknown error occurred: %s' % str(e))
                return self._admin_notify(*args, **kwargs)
        else:
            return self._admin_notify(*args, **kwargs)
        return self._administer(*args, **kwargs)

    def _administer(self, *args, **kwargs):
        self._write('admin/administer', kwargs=kwargs)
        return apache.OK
