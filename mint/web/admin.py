#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#

import sys
from mod_python import apache

from mint import mint_error
from webhandler import WebHandler
from conary.web.fields import strFields, intFields, listFields, boolFields

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
        return self._write('admin/user', userlist=userlist, kwargs = kwargs)

    @intFields(userId=None)
    def _admin_user_cancel(self, userId, *args, **kwargs):
        self.client.removeUserAccount(userId)
        kwargs['extraMsg'] = "User account deleted"
        return self._admin_user(*args, **kwargs)

    def _admin_user_new(self, *args, **kwargs):
        return self._write('admin/newUser', kwargs = kwargs, errors=[])

    @strFields(username = '', email = '', password = '', password2 = '',
               fullName = '', displayEmail = '', blurb = '')
    def _admin_user_register(self, username, fullName, email, password,
                             password2, displayEmail, blurb, *args, **kwargs):
        errors = []
        if not username:
            errors.append("You must supply a username.")
        if not email:
            errors.append("You must supply a valid e-mail address.  This will be used to confirm your account.")
        if not password or not password2:
            errors.append("Password field left blank.")
        if password != password2:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Password must be 6 characters or longer.")
        if not errors:
            try:
                self.client.registerNewUser(username, password, fullName, email,
                            displayEmail, blurb, active=True)
            except users.UserAlreadyExists:
                errors.append("An account with that username already exists.")
            except users.GroupAlreadyExists:
                errors.append("An account with that username already exists.")
            except users.MailError,e:
                errors.append(e.context);
        if not errors:
            kwargs['extraMsg'] = "User account created"
            return self._admin_user(*args, **kwargs)
        else:
            kwargs = {'username': username,
                      'email': email,
                      'fullName': fullName,
                      'displayEmail': displayEmail,
                      'blurb': blurb
                     }
            return self._write("admin/newUser", errors=errors, kwargs = kwargs)

    @intFields(userId=None)
    def _admin_user_reset_password(self, userId, *args, **kwargs):
        self._resetPasswordById(userId)
        kwargs['extraMsg'] = "User password reset"
        return self._admin_user(*args, **kwargs)

    def _admin_project(self, *args, **kwargs):
        #Get a list of all the projects in a format suitable for producing
        #a dropdown or multi-select list.
        projects = self.client.getProjectsList()

        return self._write('admin/project', projects = projects, kwargs = kwargs)

    def _admin_project_delete(self, *args, **kwargs):
        # XXX Go through with it.  This functionality may be added in some later release
        return self._admin_project(*args, **kwargs)

    @intFields(projectId = None)
    def _admin_project_hide(self, projectId, *args, **kwargs):
        self.client.hideProject(projectId)
        kwargs['extraMsg'] = "Project hidden"
        return self._admin_project(*args, **kwargs)

    @intFields(projectId = None)
    def _admin_project_unhide(self, projectId, *args, **kwargs):
        self.client.unhideProject(projectId)
        kwargs['extraMsg'] = "Project unhidden"
        return self._admin_project(*args, **kwargs)

    @intFields(projectId = None)
    def _admin_project_disable(self, projectId, *args, **kwargs):
        self.client.disableProject(projectId)
        kwargs['extraMsg'] = "Project disabled"
        return self._admin_project(*args, **kwargs)

    @intFields(projectId = None)
    def _admin_project_enable(self, projectId, *args, **kwargs):
        self.client.enableProject(projectId)
        kwargs['extraMsg'] = "Project enabled"
        return self._admin_project(*args, **kwargs)

    def _admin_project_jump(self, page, **kwargs):
        name = self.client.getProject(int(kwargs['projectId'])).getHostname()
        return self._redirect('/project/%s/%s' % (name, page))

    def _admin_project_maillists(self, *args, **kwargs):
        return self._admin_project_jump('mailingLists', **kwargs)

    def _admin_project_edit(self, *args, **kwargs):
        return self._admin_project_jump('editProject', **kwargs)

    def _admin_project_change_members(self, *args, **kwargs):
        return self._admin_project_jump('members', **kwargs)

    def _admin_notify(self, *args, **kwargs):
        return self._write('admin/notify', kwargs=kwargs)

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

    def _admin_report(self, *args, **kwargs):
        reports = self.client.listAvailableReports()
        return self._write('admin/report', kwargs=kwargs,
            availableReports = reports.iteritems())

    @strFields(reportName = None)
    def _admin_report_view(self, *args, **kwargs):
        pdfData = self.client.getReportPdf(kwargs['reportName'])
        self.req.content_type = "application/x-pdf"
        return self.req.write(pdfData)

    def _administer(self, *args, **kwargs):
        return self._write('admin/administer', kwargs=kwargs)
