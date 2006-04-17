#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

import os
import sys

from mod_python import apache

from mint import mint_error
from mint import maintenance
from mint.web.webhandler import normPath, WebHandler, HttpNotFound, HttpForbidden

from conary import versions
from conary.web.fields import strFields, intFields, listFields, boolFields

class AdminHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        if not self.auth.admin:
            raise HttpForbidden

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        if not cmd:
            return self._frontPage
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            raise HttpNotFound

        if not callable(method):
            raise HttpNotFound

        return method

    def _frontPage(self, *args, **kwargs):
        return self._write('admin/frontPage', kwargs = kwargs)

    def users(self, *args, **kwargs):
        userlist = self.client.getUsersList()
        return self._write('admin/user', userlist = userlist, kwargs = kwargs)

    def newUser(self, *args, **kwargs):
        return self._write('admin/newUser', kwargs = kwargs, errors=[])

    @strFields(username = '', email = '', password = '', password2 = '',
               fullName = '', displayEmail = '', blurb = '')
    def processNewUser(self, username, fullName, email, password,
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
            return self.users(*args, **kwargs)
        else:
            kwargs = {'username': username,
                      'email': email,
                      'fullName': fullName,
                      'displayEmail': displayEmail,
                      'blurb': blurb
                     }
            return self._write("admin/newUser", errors=errors, kwargs = kwargs)

    @intFields(userId = None)
    @strFields(operation = None)
    def processUserAction(self, userId, operation, *args, **kwargs):
        errors = []
        if operation == "user_reset_password":
            self._resetPasswordById(userId)
            extraMsg = "User password reset"
        elif operation == "user_cancel":
            if userId == self.auth.userId:
                errors = ['You cannot close your account from this interface.']
            self.client.removeUserAccount(userId)
            extraMsg = "User account deleted"
        elif operation == "user_promote_admin":
            self.client.promoteUserToAdmin(userId)
            extraMsg = 'User promoted to administrator.'
        elif operation == "user_demote_admin":
            self.client.demoteUserFromAdmin(userId)
            extraMsg = 'Administrative privileges revoked'

        if not errors:
            kwargs['extraMsg'] = extraMsg
        else:
            kwargs['errors'] = errors
        return self.users(*args, **kwargs)


    def projects(self, *args, **kwargs):
        projects = self.client.getProjectsList()
        return self._write('admin/project', projects = projects, kwargs = kwargs)

    @intFields(projectId = None)
    @strFields(operation = None)
    def processProjectAction(self, projectId, operation, *args, **kwargs):
        project = self.client.getProject(projectId)

        if operation == "project_toggle_hide":
            if project.hidden:
                self.client.unhideProject(projectId)
                kwargs['extraMsg'] = "Project unhidden"
            else:
                self.client.hideProject(projectId)
                kwargs['extraMsg'] = "Project hidden"
        elif operation == "project_toggle_disable":
            if project.disabled:
                self.client.enableProject(projectId)
                kwargs['extraMsg'] = "Project enabled"
            else:
                self.client.disableProject(projectId)
                kwargs['extraMsg'] = "Project disabled"
        else:
            raise HttpNotFound

        return self.projects(*args, **kwargs)

    def notify(self, *args, **kwargs):
        return self._write('admin/notify', kwargs=kwargs)

    def sendNotify(self, *args, **kwargs):
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
                return self.notify(*args, **kwargs)
        else:
            return self.notify(*args, **kwargs)
        self.redirect(self.cfg.basePath + "admin")

    def reports(self, *args, **kwargs):
        reports = self.client.listAvailableReports()
        return self._write('admin/report', kwargs=kwargs,
            availableReports = reports.iteritems())

    @strFields(reportName = None)
    def viewReport(self, *args, **kwargs):
        pdfData = self.client.getReportPdf(kwargs['reportName'])
        self.req.content_type = "application/x-pdf"
        return pdfData

    @strFields(name = None, hostname = None, label = None, url = '',\
        mirrorUser = '', mirrorPass = '', mirrorEnt = '')
    @boolFields(useMirror = False)
    def processExternal(self, name, hostname, label, url,
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

    def external(self, *args, **kwargs):
        from mint import database
        try:
            self.client.getProjectByHostname('rpath')
        except database.ItemNotFound:
            firstTime = True
        else:
            firstTime = False
        return self._write('admin/external', kwargs = kwargs,
                           firstTime = firstTime)

    def jobs(self, *args, **kwargs):
        try:
            enableToggle = True
            jobServerStatus = self.client.getJobServerStatus()
        except:
            enableToggle = False
            jobServerStatus = "Job server status is unknown."

        return self._write('admin/jobs', kwargs = kwargs,
                jobServerStatus = jobServerStatus, enableToggle = enableToggle)

    @strFields(operation = None)
    def jobserverOperation(self, operation, *args, **kwargs):
        if operation not in ('start', 'stop'):
            raise HttpNotFound
        try:
            pipeFD = os.popen("sudo /sbin/service rbuilder-isogen %s" % operation)
            kwargs['extraMsg'] = pipeFD.read()
            pipeFD.close()
        except:
            kwargs['extraMsg'] = "Failed to %s the job server." % operation
        return self.jobs(*args, **kwargs)

    def outbound(self, *args, **kwargs):
        outboundLabels = [(self.client.getProject(x[0]), self.client.getLabel(x[1]), x[1], x[2], x[3], x[4]) for x in self.client.getOutboundLabels()]
        return self._write('admin/outbound', outboundLabels = outboundLabels)

    def addOutbound(self, *args, **kwargs):
        projects = self.client.getProjectsList()
        return self._write('admin/add_outbound', projects = projects)

    @intFields(projectId = None)
    @strFields(targetUrl = None, mirrorUser = None, mirrorPass = None)
    def processAddOutbound(self, projectId, targetUrl, mirrorUser, mirrorPass, *args, **kwargs):
        project = self.client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]
        self.client.addOutboundLabel(projectId, labelId, targetUrl, mirrorUser, mirrorPass)

        self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))

    @listFields(str, remove = [])
    def removeOutbound(self, remove, *args, **kwargs):
        for x in remove:
            labelId, url = x.split(" ")
            self.client.delOutboundLabel(int(labelId), url)
        self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))

    def maintenance(self, *args, **kwargs):
        return self._write('admin/maintenance', kwargs = kwargs)

    def toggleMaintLock(self, *args, **kwargs):
        mode = maintenance.getMaintenanceMode(self.cfg) ^ 1
        maintenance.setMaintenanceMode(self.cfg, mode)
        self._redirect("http://%s%sadmin/maintenance" % (self.cfg.siteHost, self.cfg.basePath))
