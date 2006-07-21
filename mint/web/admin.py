#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#

import os
import sys
import BaseHTTPServer

from mod_python import apache

from mint import users
from mint import mint_error
from mint import maintenance
from mint import projectlisting
from mint.web.webhandler import normPath, WebHandler, HttpNotFound, HttpForbidden
from mint.mirrorprime import TarHandler

from conary import conarycfg, versions
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

    def newUser(self, *args, **kwargs):
        return self._write('admin/newUser', kwargs = kwargs)

    @strFields(newUsername = '', email = '', password = '', password2 = '',
               fullName = '', displayEmail = '', blurb = '')
    def processNewUser(self, newUsername, fullName, email, password,
                             password2, displayEmail, blurb, *args, **kwargs):
        # newUsername was only used to prevent browsers from supplying a
        # remembered value
        username = newUsername
        if not username:
            self._addErrors("You must supply a username.")
        if not email:
            self._addErrors("You must supply a valid e-mail address.  This will be used to confirm your account.")
        if not password or not password2:
            self._addErrors("Password field left blank.")
        if password != password2:
            self._addErrors("Passwords do not match.")
        if len(password) < 6:
            self._addErrors("Password must be 6 characters or longer.")
        if not self._getErrors():
            try:
                self.client.registerNewUser(username, password, fullName, email,
                            displayEmail, blurb, active=True)
            except users.UserAlreadyExists:
                self._addErrors("An account with that username already exists.")
            except users.GroupAlreadyExists:
                self._addErrors("An account with that username already exists.")
            except users.MailError,e:
                self._addErrors(e.context);
        if not self._getErrors():
            self._setInfo("User account created")
            self._redirect(self.cfg.basePath + "admin/")
        else:
            kwargs = {'username': username,
                      'email': email,
                      'fullName': fullName,
                      'displayEmail': displayEmail,
                      'blurb': blurb
                     }
            return self._write("admin/newUser", kwargs = kwargs)


    def notify(self, *args, **kwargs):
        return self._write('admin/notify', kwargs=kwargs)

    def sendNotify(self, *args, **kwargs):
        if not kwargs.get('subject', None):
            self._addErrors('You must supply a subject')
        if not kwargs.get('body', None):
            self._addErrors('You must supply a message body')
        if not self._getErrors():
            try:
                returner = self.client.notifyUsers(str(kwargs['subject']), str(kwargs['body']))
                self._setInfo('Message sent successfully')
            except Exception, e:
                self._addErrors('An unknown error occurred: %s' % str(e))
                return self.notify(*args, **kwargs)
        else:
            return self.notify(*args, **kwargs)
        self._redirect(self.cfg.basePath + "admin/")

    def reports(self, *args, **kwargs):
        reports = self.client.listAvailableReports()
        return self._write('admin/report', kwargs=kwargs,
            availableReports = reports.iteritems())

    @strFields(reportName = None)
    def viewReport(self, *args, **kwargs):
        pdfData = self.client.getReportPdf(kwargs['reportName'])
        self.req.content_type = "application/x-pdf"
        return pdfData

    @strFields(name = '', hostname = '', label = '', url = '',\
        externalUser = '', externalPass = '', externalEntKey = '',\
        externalEntClass = '', authType = 'username')
    @boolFields(useMirror = False, primeMirror = False, externalAuth = False)
    def processExternal(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntClass, externalEntKey,
                        useMirror, primeMirror, externalAuth, authType,
                        *args, **kwargs):

        if not name:
            self._addErrors("Missing project title")
        if not hostname:
            self._addErrors("Missing project name")
        if not label:
            self._addErrors("Missing project label")
        else:
            try:
                extLabel = versions.Label(label)
            except versions.ParseError:
                self._addErrors("Invalid label %s" % label)
        if externalAuth:
            if authType == 'userpass':
                if not externalUser:
                    self._addErrors("Missing username for local mirror authentication")
                if not externalPass:
                    self._addErrors("Missing password for local mirror authentication")
            elif authType == 'entitlement':
                if not externalEntKey:
                    self._addErrors('Missing entitlement class for local mirror authentication')
                if not externalEntClass:
                    self._addErrors('Missing entitlement key for local mirror authentication')

        if not self._getErrors():
            if primeMirror and useMirror:
                startPrimeServer()
                # return the prime mirror page loaded with enough information to create the
                # project once the priming was successful
                serverName = extLabel.getHost()
                return self._write("admin/primeMirror", name = name, hostname = hostname,
                    label = label, url = url, externalUser = externalUser, serverName = serverName,
                    externalPass = externalPass, externalEntKey = externalEntKey,
                    externalEntClass = externalEntClass, authType = authType,
                    useMirror = True, primeMirror = False, externalAuth = externalAuth)

            projectId = self.client.newExternalProject(name, hostname,
                self.cfg.projectDomainName, label, url, useMirror)
            project = self.client.getProject(projectId)

            labelIdMap, _, _ = self.client.getLabelsForProject(projectId)
            label, labelId = labelIdMap.items()[0]

            if not url and not externalAuth:
                url = "http://%s/conary/" % extLabel.getHost()
            elif not url and externalAuth:
                url = "https://%s/conary/" % extLabel.getHost()

            # set up the authentication
            if externalAuth:
                if authType == 'userpass':
                    project.editLabel(labelId, label, url,
                            externalUser, externalPass)
                elif authType == 'entitlement':
                    externalEnt = conarycfg.emitEntitlement(extLabel.getHost(), externalEntClass, externalEntKey)
                    entF = file(os.path.join(self.cfg.dataPath, "entitlements", extLabel.getHost()), "w")
                    entF.write(externalEnt)
                    entF.close()
                    project.editLabel(labelId, label, url,
                            self.cfg.authUser, self.cfg.authPass)

            # set up the mirror, if requested
            if useMirror:
                localUrl = "http://%s%srepos/%s/" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname)

                # set the internal label to our authUser and authPass
                project.editLabel(labelId, label, localUrl, self.cfg.authUser, self.cfg.authPass)
                self.client.addInboundLabel(projectId, labelId, url, externalUser, externalPass)
                self.client.addRemappedRepository(hostname + "." + self.cfg.siteDomainName, extLabel.getHost())

            self._setInfo("Added external project %s" % name)
            self._redirect("http://%s%sproject/%s/" % \
                (self.cfg.projectSiteHost,
                 self.cfg.basePath, hostname))
        else:
            kwargs = {'name': name, 'hostname': hostname, 'label': label,
                'url': url, 'externalAuth': externalAuth,
                'authType': authType, 'externalUser': externalUser,
                'externalPass': externalPass,
                'externalEntKey': externalEntKey,
                'externalEntClass': externalEntClass,
                'useMirror': useMirror, 'primeMirror': primeMirror}
            return self.external(name = name, hostname = hostname,
                    label = label, url = url, externalAuth = externalAuth,
                    externalUser = externalUser, externalPass = externalPass,
                    externalEntKey = externalEntKey,
                    externalEntClass = externalEntClass,
                    useMirror = useMirror, primeMirror = primeMirror,
                    authType = authType)

    @strFields(authType = 'userpass')
    def external(self, *args, **kwargs):
        from mint import database
        kwargs.setdefault('authtype', 'userpass')
        try:
            self.client.getProjectByHostname('rpath')
        except database.ItemNotFound:
            firstTime = True
            kwargs.setdefault('name', 'rPath Linux')
            kwargs.setdefault('hostname', 'rpath')
            kwargs.setdefault('url', 'http://conary.rpath.com/conary/')
            kwargs.setdefault('label', 'conary.rpath.com@rpl:1')
        else:
            firstTime = False

        return self._write('admin/external', firstTime = firstTime,
                kwargs = kwargs)

    def removeExternal(self, *args, **kwargs):
        return self._write('admin/removeExternal')

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
            pipeFD = os.popen("sudo /sbin/service multi-jobserver %s" % operation)
            self._setInfo(pipeFD.read())
            pipeFD.close()
        except:
            self._setInfo("Failed to %s the job server" % operation)
        return self.jobs(*args, **kwargs)

    def outbound(self, *args, **kwargs):
        outboundLabels = [(self.client.getProject(x[0]), self.client.getLabel(x[1]), x[1], x[2], x[3], x[4]) for x in self.client.getOutboundLabels()]
        return self._write('admin/outbound', outboundLabels = outboundLabels)

    def addOutbound(self, *args, **kwargs):
        projects = self.client.getProjectsList()
        return self._write('admin/add_outbound', projects = projects)

    def selections(self, *args, **kwargs):
        return self._write('admin/selections',
                           selectionData=self.client.getFrontPageSelection())

    def useIt(self, *args, **kwargs):
        data = self.client.getUseItIcons()
        if data:
            if len(data) < 4:
                table1Data = data
                table2Data = False
            elif len(data) == 4:
                table1Data = data[:2]
                table2Data = data[2:]
            else:
                table1Data = data[:3]
                table2Data = data[3:]
        else:
            table1Data = False
            table2Data = False
        return self._write('admin/useit', table1Data=table1Data, 
                           table2Data=table2Data)

    @strFields(name1='', link1='', name2='', link2='', name3='', 
               link3='', name4='', link4='', name5='', link5='',
               name6='', link6='', op='preview')
    def setIcons(self, name1, link1, name2, link2, name3, link3, name4, link4,
                 name5, link5, name6, link6, op, *args, **kwargs):
        if op == 'preview':
            newIcons = []
            newIcons.append({'itemId':1, 'name':name1, 'link':link1})
            newIcons.append({'itemId':2, 'name':name2, 'link':link2})
            newIcons.append({'itemId':3, 'name':name3, 'link':link3})
            newIcons.append({'itemId':4, 'name':name4, 'link':link4})
            newIcons.append({'itemId':5, 'name':name5, 'link':link5})
            newIcons.append({'itemId':6, 'name':name6, 'link':link6})
            data = self.client.getUseItIcons()
            newData = []
            for icon in newIcons:
                if not icon['name']:
                    if data:
                        for item in data:
                            if item['itemId'] == icon['itemId']:
                                newData.append(item)
                else:
                    newData.append(icon)
            return self.preview(newData=newData)
        elif op == "set":
            self.client.addUseItIcon(1, name1, link1)
            self.client.addUseItIcon(2, name2, link2)
            self.client.addUseItIcon(3, name3, link3)
            self.client.addUseItIcon(4, name4, link4)
            self.client.addUseItIcon(5, name5, link5)
            self.client.addUseItIcon(6, name6, link6)
        return self.useIt()

    @intFields(itemId=None)
    def deleteUseItIcon(self, itemId, *args, **kwargs):
        self.client.deleteUseItIcon(itemId)
        return self.useIt()

    @strFields(name=None, link=None)
    @intFields(rank=0)
    def addSelection(self, name, link, rank, op, *args, **kwargs):
        if op == 'preview':
            return self.preview(name=name, link=link, rank=rank)
        self.client.addFrontPageSelection(name, link, rank)
        return self.selections()

    @intFields(itemId=None)
    def deleteSelection(self, itemId, *args, **kwargs):
        self.client.deleteFrontPageSelection(itemId)
        return self.selections()

    def spotlight(self, *args, **kwargs):
        return self._write('admin/spotlight',
                           spotlightData=self.client.getSpotlightAll())

    @strFields(title = None, text=None, link=None, logo=None, startDate=None, 
               endDate=None, operation='preview')
    @intFields(showArchive=0)
    def addSpotlightItem(self, title, text, link, logo, showArchive, startDate,
                                 endDate, operation, *args, **kwargs):
        if not startDate or not endDate:
            return self.spotlight()

        if operation == 'preview':
            return self.preview(title=title, text=text, logo=logo,
                                 showArchive=showArchive, link=link, 
                                 startDate=startDate, endDate=endDate)
        elif operation == 'apply':
            self.client.addSpotlightItem(title, text, link, logo,
                                         showArchive, startDate, endDate)
        return self.spotlight()

    @intFields(itemId=None)
    @strFields(title=None)
    def deleteSpotlightItem(self, itemId, title, *args, **kwargs):
        message = 'Delete Appliance Spotlight Entry "%s"?' % title
        noLink = os.path.join(self.cfg.basePath, 'admin', 'spotlight') 
        yesArgs = dict(func='delSpotlight', itemId=itemId)
        return self._write('confirm', message=message, noLink=noLink, 
                           yesArgs=yesArgs)
    
    @intFields(itemId=None)
    def delSpotlight(self, itemId, *args, **kwargs):
        self.client.deleteSpotlightItem(itemId)
        return self.spotlight()

    def preview(self, *args, **kwargs):
        if not kwargs.has_key('showArchive'):
            spotlightData = self.client.getCurrentSpotlight()
        else:
            spotlightData = kwargs
        if spotlightData:
            if not spotlightData.has_key('logo'):
                spotlightData['logo'] = ''
        selectionData = self.client.getFrontPageSelection()
        if kwargs.has_key('name'):
            newSelectionData = kwargs
            if selectionData:
                selectionData.append(newSelectionData)
                selectionData.sort(lambda x,y: cmp(x['rank'], y['rank']))
            else:
                selectionData = [newSelectionData]
        if not kwargs.has_key('newData'):
            newData = self.client.getUseItIcons()
        else:
            newData = kwargs['newData']
            
        popularProjects, _ = self.client.getProjects(projectlisting.NUMDEVELOPERS_DES, 10, 0)
        activeProjects, _  = self.client.getProjects(projectlisting.ACTIVITY_DES, 10, 0)
        publishedReleases = self.client.getPublishedReleaseList()

        if newData:
            if len(newData) < 4:
                table1Data = newData
                table2Data = False
            elif len(newData) == 4:
                table1Data = newData[:2]
                table2Data = newData[2:]
            else:
                table1Data = newData[:3]
                table2Data = newData[3:]
        else:
            table1Data = False
            table2Data = False

        return self._write("admin/preview", firstTime=self.session.get('firstTimer', False), popularProjects=popularProjects, selectionData = selectionData, activeProjects = activeProjects, spotlightData=spotlightData, publishedReleases=publishedReleases, table1Data=table1Data, table2Data=table2Data)

    @intFields(projectId = None)
    @strFields(targetUrl = None, mirrorUser = None, mirrorPass = None)
    @boolFields(mirrorSources = False, allLabels = False)
    def processAddOutbound(self, projectId,
            targetUrl, mirrorUser, mirrorPass,
            mirrorSources, allLabels,
            *args, **kwargs):
        project = self.client.getProject(projectId)
        labelId = project.getLabelIdMap().values()[0]

        self.client.addOutboundLabel(projectId, labelId, targetUrl, mirrorUser, mirrorPass, allLabels)
        if not mirrorSources:
            self.client.setOutboundMatchTroves(projectId, labelId,
                                               ["-.*:source", "-.*:debuginfo",
                                                "+.*"])

        self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))

    @listFields(str, remove = [])
    def removeOutbound(self, remove, *args, **kwargs):
        for x in remove:
            labelId, url = x.split(" ")
            self.client.delOutboundLabel(int(labelId), url)
        self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))

    def maintenance(self, *args, **kwargs):
        return self._write('admin/maintenance', kwargs = kwargs)

    @intFields(curMode = None)
    def toggleMaintLock(self, curMode, *args, **kwargs):
        mode = curMode ^ 1
        maintenance.setMaintenanceMode(self.cfg, mode)
        self._redirect("http://%s%sadmin/maintenance" % (self.cfg.siteHost, self.cfg.basePath))

def startPrimeServer():
    pid = os.fork()
    if not pid:
        os.system("/usr/share/rbuilder/scripts/mirror-prime-server")
        os._exit(0)
