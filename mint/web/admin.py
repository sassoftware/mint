#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

import sys
import os
from mod_python import apache

from mint import mint_error
from webhandler import WebHandler, HttpNotFound
from conary import versions
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

        try:
            return self.__getattribute__('_admin_%s'%operation)(*args, **kwargs)
        except AttributeError:
            raise HttpNotFound

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

    @intFields(userId=None)
    def _admin_user_promote_admin(self, userId, *args, **kwargs):
        self.client.promoteUserToAdmin(userId)
        kwargs['extraMsg'] = 'User promoted to administrator.'
        return self._admin_user(*args, **kwargs)

    @intFields(userId=None)
    def _admin_user_demote_admin(self, userId, *args, **kwargs):
	self.client.demoteUserFromAdmin(userId)
	kwargs['extraMsg'] = 'Administrative privileges revoked'
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
    def _admin_project_toggle_hide(self, projectId, *args, **kwargs):
        project = self.client.getProject(projectId)
        if project.hidden:
            self.client.unhideProject(projectId)
            kwargs['extraMsg'] = "Project unhidden"
        else:
            self.client.hideProject(projectId)
            kwargs['extraMsg'] = "Project hidden"
        return self._admin_project(*args, **kwargs)

    @intFields(projectId = None)
    def _admin_project_toggle_disable(self, projectId, *args, **kwargs):
        project = self.client.getProject(projectId)
        if project.disabled:
            self.client.enableProject(projectId)
            kwargs['extraMsg'] = "Project enabled"
        else:
            self.client.disableProject(projectId)
            kwargs['extraMsg'] = "Project disabled"
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
                returner = self.client.notifyUsers(str(kwargs['subject']), str(kwargs['body']))
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
        return pdfData

    @strFields(name = None, hostname = None, label = None, url = '',\
        mirrorUser = '', mirrorPass = '', mirrorEnt = '')
    @boolFields(useMirror = False)
    def _admin_process_external(self, name, hostname, label, url,
                                mirrorUser, mirrorPass, mirrorEnt,
                                useMirror, *args, **kwargs):
        projectId = self.client.newExternalProject(name, hostname,
            self.cfg.projectDomainName, label, url, useMirror)
        project = self.client.getProject(projectId)

        extLabel = versions.Label(label)
        # set up the mirror, if requested
        if useMirror:
            labelIdMap, _, _ = self.client.getLabelsForProject(projectId)
            label, labelId = labelIdMap.items()[0]
            localUrl = "http://%s%srepos/%s/" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname)

            project.editLabel(labelId, label, localUrl, self.cfg.authUser, self.cfg.authPass)
            self.client.addInboundLabel(projectId, labelId, url, mirrorUser, mirrorPass)
            self.client.addRemappedRepository(hostname + "." + self.cfg.siteDomainName, extLabel.getHost())

        self._redirect(self._redirect("http://%s%sproject/%s/" % \
                                      (self.cfg.projectSiteHost,
                                       self.cfg.basePath, hostname)))

    def _admin_external(self, *args, **kwargs):
        from mint import database
        try:
            self.client.getProjectByHostname('rpath')
        except database.ItemNotFound:
            firstTime = True
        else:
            firstTime = False
        return self._write('admin/external', kwargs = kwargs,
                           firstTime = firstTime)

    def _admin_jobs(self, *args, **kwargs):
        try:
            enableToggle = True
            jobServerStatus = self.client.getJobServerStatus()
        except:
            enableToggle = False
            jobServerStatus = "Job server status is unknown."

        return self._write('admin/jobs', kwargs = kwargs,
                jobServerStatus = jobServerStatus, enableToggle = enableToggle)

    def _admin_jobs_jobserver_start(self, *args, **kwargs):
        try:
            pipeFD = os.popen("sudo /sbin/service rbuilder-isogen start")
            kwargs['extraMsg'] = pipeFD.read()
            pipeFD.close()
        except:
            kwargs['extraMsg'] = "Failed to start the job server."

        return self._admin_jobs(*args, **kwargs)

    def _admin_jobs_jobserver_stop(self, *args, **kwargs):
        try:
            pipeFD = os.popen("sudo /sbin/service rbuilder-isogen stop")
            kwargs['extraMsg'] = pipeFD.read()
            pipeFD.close()
        except:
            kwargs['extraMsg'] = "Failed to stop the job server."

        return self._admin_jobs(*args, **kwargs)

    def _admin_outbound(self, *args, **kwargs):
        outboundLabels = [(self.client.getProject(x[0]), self.client.getLabel(x[1]), x[1], x[2], x[3], x[4]) for x in self.client.getOutboundLabels()]
        return self._write('admin/outbound', outboundLabels = outboundLabels)

    def _admin_add_outbound(self, *args, **kwargs):
        projects = self.client.getProjectsList()
        return self._write('admin/add_outbound', projects = projects)

    @intFields(projectId = None)
    @strFields(targetUrl = None, mirrorUser = None, mirrorPass = None)
    def _admin_process_add_outbound(self, projectId, targetUrl, mirrorUser, mirrorPass, *args, **kwargs):
        project = self.client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]
        self.client.addOutboundLabel(projectId, labelId, targetUrl, mirrorUser, mirrorPass)

        self._redirect("administer?operation=outbound")

    @listFields(str, remove = [])
    def _admin_remove_outbound(self, remove, *args, **kwargs):
        for x in remove:
            labelId, url = x.split(" ")
            self.client.delOutboundLabel(int(labelId), url)
        self._redirect("administer?operation=outbound")

    def _administer(self, *args, **kwargs):
        return self._write('admin/administer', kwargs = kwargs)
