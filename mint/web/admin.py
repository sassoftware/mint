#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#

import os
import sys
import BaseHTTPServer
import xmlrpclib
import urllib
import socket

from mod_python import apache

from mint import users
from mint import mint_error
from mint import maintenance
from mint.helperfuncs import cleanseUrl
from mint.web.webhandler import normPath, WebHandler, HttpNotFound, HttpForbidden

from kid.pull import XML
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

    def reports(self, *args, **kwargs):
        reports = self.client.listAvailableReports()
        return self._write('admin/report', kwargs=kwargs,
            availableReports = reports.iteritems())

    @strFields(reportName = None)
    def viewReport(self, *args, **kwargs):
        pdfData = self.client.getReportPdf(kwargs['reportName'])
        self.req.content_type = "application/x-pdf"
        return pdfData

    def _validateExternalProject(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntClass, externalEntKey,
                        useMirror, authType,
                        additionalLabelsToMirror):
        additionalLabels = []
        extLabel = ""
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
        if useMirror == 'net' and additionalLabelsToMirror:
            for l in additionalLabelsToMirror.split():
                # skip a redundant label specification
                if l != label:
                    try:
                        testlabel = versions.Label(l)
                        additionalLabels.append(l)
                    except versions.ParseError:
                        self._addErrors("Invalid additional label %s" % l)
        if authType != 'none':
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
        return additionalLabels, extLabel

    @strFields(name = '', hostname = '', label = '', url = '',\
        externalUser = '', externalPass = '', externalEntKey = '',\
        externalEntClass = '', authType = 'none',\
        additionalLabelsToMirror = '', useMirror = 'none')
    @intFields(projectId = -1)
    def processAddExternal(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntClass, externalEntKey,
                        useMirror, authType, additionalLabelsToMirror,
                        projectId, *args, **kwargs):

        print >> sys.stderr, label
        sys.stderr.flush()

        kwargs = {'name': name, 'hostname': hostname, 'label': label,
            'url': url, 'authType': authType, 'externalUser': externalUser,
            'externalPass': externalPass,
            'externalEntKey': externalEntKey,
            'externalEntClass': externalEntClass,
            'useMirror': useMirror,
            'additionalLabelsToMirror': additionalLabelsToMirror}

        editing = (projectId != -1)
        externalAuth = (authType != 'none')

        additionalLabels, extLabel = self._validateExternalProject(**kwargs)
        if not self._getErrors():
            if not editing:
                projectId = self.client.newExternalProject(name, hostname,
                    self.cfg.projectDomainName, label, url, useMirror == 'net')

            project = self.client.getProject(projectId)
            if editing:
                project.editProject(project.projecturl, project.description, name)

            labelIdMap, _, _ = self.client.getLabelsForProject(projectId)
            label, labelId = labelIdMap.items()[0]

            if not url and not externalAuth:
                url = "http://%s/conary/" % extLabel.getHost()
            elif not url and externalAuth:
                url = "https://%s/conary/" % extLabel.getHost()

            # set up the authentication
            if externalAuth:
                if authType == 'userpass':
                    project.editLabel(labelId, str(extLabel), url,
                            externalUser, externalPass)
                elif authType == 'entitlement':
                    externalEnt = conarycfg.emitEntitlement(extLabel.getHost(), externalEntClass, externalEntKey)
                    entF = file(os.path.join(self.cfg.dataPath, "entitlements", extLabel.getHost()), "w")
                    entF.write(externalEnt)
                    entF.close()
                    project.editLabel(labelId, str(extLabel), url,
                            self.cfg.authUser, self.cfg.authPass)
                else:
                    raise RuntimeError, "Invalid authentication type specified"
            else:
                project.editLabel(labelId, str(extLabel), url,
                    'anonymous', 'anonymous')

            mirror = self.client.getInboundMirror(projectId)
            # set up the mirror, if requested
            if useMirror == 'net':
                localUrl = "http%s://%s%srepos/%s/" % (self.cfg.SSL and 's' or\
                           '', self.cfg.projectSiteHost, self.cfg.basePath, 
                           hostname)

                # set the internal label to our authUser and authPass
                project.editLabel(labelId, str(extLabel), localUrl, self.cfg.authUser, self.cfg.authPass)

                if mirror and editing:
                    mirrorId = mirror['inboundMirrorId']
                    self.client.editInboundMirror(mirrorId, [str(extLabel)] + additionalLabels, url, externalUser, externalPass)
                else:
                    self.client.addInboundMirror(projectId, [str(extLabel)] + additionalLabels, url, externalUser, externalPass)
                    self.client.addRemappedRepository(hostname + "." + self.cfg.siteDomainName, extLabel.getHost())
            # remove mirroring if requested
            elif useMirror == 'none' and mirror and editing:
                project.editLabel(labelId, str(extLabel), url, externalUser, externalPass)
                self.client.delInboundMirror(mirror['inboundMirrorId'])
                self.client.delRemappedRepository(hostname + "." + self.cfg.siteDomainName)

            verb = editing and "Edited" or "Added"
            self._setInfo("%s external project %s" % (verb, name))
            self._redirect("http://%s%sproject/%s/" % \
                (self.cfg.projectSiteHost,
                 self.cfg.basePath, hostname))
        else:
            if editing:
                return self.editExternal(projectId = projectId, **kwargs)
            else:
                return self.addExternal(**kwargs)

    @strFields(authType = 'none')
    def addExternal(self, *args, **kwargs):
        from mint import database
        kwargs.setdefault('authtype', 'none')
        try:
            self.client.getProjectByHostname('rpath')
        except database.ItemNotFound:
            firstTime = True
            kwargs.setdefault('name', 'rPath Linux')
            kwargs.setdefault('hostname', 'rpath')
            kwargs.setdefault('url', 'https://conary.rpath.com/conary/')
            kwargs.setdefault('label', 'conary.rpath.com@rpl:1')
            kwargs.setdefault('additionalLabelsToMirror', 'conary.rpath.com@rpl:1-compat conary.rpath.com@rpl:1-xen')
        else:
            firstTime = False

        return self._write('admin/addExternal', firstTime = firstTime,
                editing = False, mirrored = False, projectId = -1,
                kwargs = kwargs, initialKwargs = {})

    @intFields(projectId = None)
    def editExternal(self, projectId, *args, **kwargs):
        project = self.client.getProject(projectId)
        label = project.getLabel()
        conaryCfg = project.getConaryConfig()

        initialKwargs = {}
        initialKwargs['name'] = project.name
        initialKwargs['hostname'] = project.hostname
        initialKwargs['label'] = label

        fqdn = versions.Label(label).getHost()
        initialKwargs['url'] = conaryCfg.repositoryMap[fqdn]
        userMap = conaryCfg.user.find(fqdn)

        ent = conarycfg.loadEntitlement(os.path.join(self.cfg.dataPath, "entitlements"), fqdn)
        if ent:
            initialKwargs['authType'] = 'entitlement'
            initialKwargs['externalEntClass'] = ent[0]
            initialKwargs['externalEntKey'] = ent[1]
        else:
            initialKwargs['externalUser'] = userMap[0]
            initialKwargs['externalPass'] = userMap[1]
            initialKwargs['authType'] = 'userpass'
            if userMap[0] == 'anonymous':
                initialKwargs['authType'] = 'none'

        initialKwargs['useMirror'] = 'none'
        mirrored = False
        mirror = self.client.getInboundMirror(projectId)
        if mirror:
            labels = mirror['sourceLabels'].split()
            if label in labels:
                labels.remove(label)

            initialKwargs['url'] = mirror['sourceUrl']
            initialKwargs['externalUser'] = mirror['sourceUsername']
            initialKwargs['externalPass'] = mirror['sourcePassword']
            initialKwargs['additionalLabelsToMirror'] = " ".join(labels)
            initialKwargs['useMirror'] = 'net'
            mirrored = True

        return self._write('admin/addExternal', firstTime = False,
            editing = True, mirrored = mirrored, kwargs = kwargs,
            initialKwargs = initialKwargs, projectId = projectId)


    def external(self, auth):
        columns = ['Project Name', 'Mirrored']
        rows = []
        for p in self.client.getProjectsList():
            project = self.client.getProject(p[0])
            if not project.external:
                continue

            mirrored = self.client.getInboundMirror(project.id)
            data = [('editExternal?projectId=%s' % project.id, project.name),
                    bool(mirrored) and 'Yes' or 'No']
            rows.append({'columns': data})

        return self._write('admin/external', columns = columns, rows = rows)

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
        if operation == 'Start Job Server':
            op = 'start'
        elif operation == 'Stop Job Server':
            op = 'stop'
        elif operation == 'Restart Job Server':
            op = 'restart'
        else:
            raise HttpNotFound

        try:
            pipeFD = os.popen("sudo /sbin/service multi-jobserver %s" % op)
            self._setInfo(pipeFD.read())
            pipeFD.close()
        except:
            self._setInfo("Failed to %s the job server" % op)
        return self.jobs(*args, **kwargs)

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

        return self._write("admin/preview", firstTime=self.session.get('firstTimer', False),
            popularProjects= [], selectionData = selectionData,
            activeProjects = [], spotlightData=spotlightData,
            publishedReleases=publishedReleases, table1Data=table1Data, table2Data=table2Data)

    def outbound(self, *args, **kwargs):
        columns = ["Project", "Labels Mirrored", "Target Repository", "Remove"]

        rows = []
        for x in self.client.getOutboundMirrors():
            outboundMirrorId, projectId, label, url, user, passwd, allLabels, recurse, matchStrings = x
            project = self.client.getProject(projectId)

            data = [(project.getUrl(), project.name), allLabels and "All Labels" or label,
                url, XML('<input type="checkbox" name="remove" value="%d" />' % outboundMirrorId) ]
            rows.append({'columns': data})

        return self._write('admin/outbound', rows = rows, columns = columns)

    def addOutbound(self, *args, **kwargs):
        projects = self.client.getProjectsList()
        return self._write('admin/add_outbound', projects = projects, kwargs = kwargs)

    def _updateMirror(self, user, servername, sp):
        passwd = ''
        try:
            res1 = sp.conaryserver.ConaryServer.addServerName(servername)
            passwd = sp.mirrorusers.MirrorUsers.addRandomUser(user)
        except xmlrpclib.ProtocolError, e:
            self._addErrors("""Protocol Error: %s (%d %s). Please be sure your
                                  rPath Mirror is configured properly.""" % \
                (cleanseUrl('https', e.url), e.errcode, e.errmsg))
        except socket.error, e:
            self._addErrors("""%s. Please be sure you rPath Mirror
                               is configured properly.""" % str(e))
        else: 
            if not res1 or not passwd:
                self._addErrors("""An error occured configuring your rPath
                                   Mirror.""")
        return passwd

    @intFields(projectId = None)
    @strFields(targetUrl = '', mirrorUser = '', mirrorPass = '')
    @boolFields(mirrorSources = False, allLabels = False)
    def processAddOutbound(self, projectId, targetUrl, mirrorUser, mirrorPass,
            mirrorSources, allLabels, *args, **kwargs):

        inputKwargs = {'projectId': projectId, 'targetUrl': targetUrl,
            'mirrorUser': mirrorUser, 'mirrorPass': mirrorPass,
            'mirrorSources': mirrorSources, 'allLabels': allLabels}

        if not mirrorUser:
            self._addErrors("rAA username must be specified")
        if not mirrorPass:
            self._addErrors("rAA user password must be specified")
        if not targetUrl:
            self._addErrors("Target FQDN must be specified")

        urltype, mirrorUrl = urllib.splittype(targetUrl)
        if not urltype:
            mirrorUrl = '//' + mirrorUrl
        mirrorUrl, ignoreMe = urllib.splithost(mirrorUrl)

        if not self._getErrors():
            project = self.client.getProject(projectId)
            servername = self.client.translateProjectFQDN(project.getFQDN())
            user = '%s-%s' % (servername, mirrorUrl)
            sp = xmlrpclib.ServerProxy("https://%s:%s@%s:8003/rAA/" % (mirrorUser, mirrorPass, mirrorUrl))
            passwd = self._updateMirror(user, servername, sp)

        if not self._getErrors():
            project = self.client.getProject(projectId)
            label = project.getLabel()
            outboundMirrorId = self.client.addOutboundMirror(projectId, [label], 'https://%s/conary/' % mirrorUrl, user, passwd, allLabels)
            if not mirrorSources:
                self.client.setOutboundMirrorMatchTroves(outboundMirrorId,
                                                   ["-.*:source", "-.*:debuginfo",
                                                    "+.*"])

            self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self.addOutbound(**inputKwargs)

    @listFields(str, remove = [])
    def removeOutbound(self, remove, *args, **kwargs):
        outbound = self.client.getOutboundMirrors()
        for ids in remove:
            self.client.delOutboundMirror(int(ids))
        self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))

    def maintenance(self, *args, **kwargs):
        return self._write('admin/maintenance', kwargs = kwargs)

    @intFields(curMode = None)
    def toggleMaintLock(self, curMode, *args, **kwargs):
        mode = curMode ^ 1
        maintenance.setMaintenanceMode(self.cfg, mode)
        self._redirect("http://%s%sadmin/maintenance" % (self.cfg.siteHost, self.cfg.basePath))
