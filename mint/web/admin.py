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

from conary import conarycfg
from conary import conaryclient
from conary.repository import errors

from mod_python import apache

from mint import users
from mint import mint_error
from mint import maintenance
from mint import mirror
from mint.helperfuncs import cleanseUrl, getUrlHost
from mint.web.webhandler import normPath, WebHandler, HttpNotFound, HttpForbidden
from mint.web.fields import strFields, intFields, listFields, boolFields

from kid.pull import XML
from conary import conarycfg, versions

import simplejson

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
                        additionalLabelsToMirror, allLabels):
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
                if externalEntKey and externalEntClass:
                    from conary.repository import netclient
                    # Test that the entitlement is valid
                    cfg = conarycfg.ConaryConfiguration()
                    if url:
                        cfg.configLine('repositoryMap %s %s' % (extLabel.host,
                                                                url))

                    cfg.configLine('entitlement %s %s' % (extLabel.host, externalEntKey))
                    nc = conaryclient.ConaryClient(cfg).getRepos()
                    try:
                        # use 2**64 to ensure we won't make the server do much
                        nc.getNewTroveList(extLabel.host, '4611686018427387904')
                    except errors.InsufficientPermission:
                        self._addErrors("Entitlement does not grant mirror access to external repository")
                    except errors.OpenError:
                        if url:
                            self._addErrors("Error contacting remote repository. Please ensure entitlement and repository URL are correct.")
                        else:
                            self._addErrors("Error contacting remote repository. Please ensure entitlement is correct.")

        if additionalLabelsToMirror and allLabels:
            self._addErrors("Do not request additional labels and all labels to be mirrored: these options are exclusive.")
        return additionalLabels, extLabel

    @strFields(name = '', hostname = '', label = '', url = '',\
        externalUser = '', externalPass = '', externalEntKey = '',\
        externalEntClass = '', authType = 'none',\
        additionalLabelsToMirror = '', useMirror = 'none')
    @intFields(projectId = -1)
    @boolFields(allLabels = False)
    def processAddExternal(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntClass, externalEntKey,
                        useMirror, authType, additionalLabelsToMirror,
                        projectId, allLabels, *args, **kwargs):

        # strip extraneous whitespace
        externalEntKey = externalEntKey.strip()
        externalEntClass = externalEntClass.strip()

        kwargs = {'name': name, 'hostname': hostname, 'label': label,
            'url': url, 'authType': authType, 'externalUser': externalUser,
            'externalPass': externalPass,
            'externalEntKey': externalEntKey,
            'externalEntClass': externalEntClass,
            'useMirror': useMirror,
            'additionalLabelsToMirror': additionalLabelsToMirror,
            'allLabels': allLabels}

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
                    self.client.editInboundMirror(mirrorId, [str(extLabel)] + additionalLabels, url, externalUser, externalPass, allLabels)
                else:
                    self.client.addInboundMirror(projectId, [str(extLabel)] + additionalLabels, url, externalUser, externalPass, allLabels)
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
            kwargs.setdefault('allLabels', 0)
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
            initialKwargs['allLabels'] = mirror['allLabels']
            initialKwargs['useMirror'] = 'net'
            mirrored = True

        return self._write('admin/addExternal', firstTime = False,
            editing = True, mirrored = mirrored, kwargs = kwargs,
            initialKwargs = initialKwargs, projectId = projectId)


    def external(self, auth):
        regColumns = ['Project Name', 'Mirrored']
        regRows = []

        # iterate through all projects, set up the
        # regular project rows, and save the mirrored
        # projects for later.
        mirroredProjects = []
        for p in self.client.getProjectsList():
            project = self.client.getProject(p[0])
            if not project.external:
                continue
            mirrored = self.client.getInboundMirror(project.id)

            if not mirrored:
                data = [('editExternal?projectId=%s' % project.id, project.name),
                        bool(mirrored) and 'Yes' or 'No']
                regRows.append({'columns': data})
            else:
                mirroredProjects.append((project, mirrored))

        # set up the mirrored projects list
        mirroredProjects.sort(key = lambda x: x[1]['mirrorOrder'])
        mirrorColumns = ['Mirrored Project Name', 'Order']
        mirrorRows = []
        for i, (project, mirrored) in enumerate(mirroredProjects):
            orderHtml = self._makeMirrorOrderingLinks("InboundMirror",
                len(mirroredProjects), mirrored['mirrorOrder'], i, mirrored['inboundMirrorId'])
            data = [('editExternal?projectId=%s' % project.id, project.name), orderHtml]
            mirrorRows.append({'columns': data})

        return self._write('admin/external',
            regColumns = regColumns, regRows = regRows,
            mirrorColumns = mirrorColumns, mirrorRows = mirrorRows)

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

    def _makeMirrorOrderingLinks(self, name, count, order, index, id):
        """Helper function to make the up/down links for mirror ordering"""
        blank = """<img src="%s/apps/mint/images/blank.gif" width="15" height="15" />""" % \
            self.cfg.staticPath
        up = down = ""
        if order > 0 and index > 0:
            up = """<img src="%s/apps/mint/images/BUTTON_collapse.gif" class="pointer" 
                         onclick="javascript:setMirrorOrder('%s', %d, %d);" />""" % \
                (self.cfg.staticPath, name, id, order-1)
        else:
            up = blank
        if order < count and index < (count-1):
            down = """<img src="%s/apps/mint/images/BUTTON_expand.gif" class="pointer"
                           onclick="javascript:setMirrorOrder('%s', %d, %d);" />""" % \
                (self.cfg.staticPath, name, id, order+1)
        else:
            down = blank

        orderHtml = XML("%s %s" % (up, down))
        return orderHtml

    def outbound(self, *args, **kwargs):
        rows = []
        mirrors = self.client.getOutboundMirrors()
        for i, x in enumerate(mirrors):
            outboundMirrorId, projectId, label, \
                allLabels, recurse, matchStrings, order = x
            project = self.client.getProject(projectId)
            mirrorData = {}
            mirrorData['id'] = outboundMirrorId
            mirrorData['projectName'] = project.name
            mirrorData['projectUrl'] = project.getUrl()
            mirrorData['orderHTML'] = self._makeMirrorOrderingLinks("OutboundMirror", len(mirrors), order, i, outboundMirrorId)
            mirrorData['allLabels'] = allLabels
            if not allLabels:
                mirrorData['labels'] = label.split(' ')
            mirrorData['targets'] = [ (x[0], getUrlHost(x[1])) for x in self.client.getOutboundMirrorTargets(outboundMirrorId) ]
            mirrorData['ordinal'] = i
            matchStrings = self.client.getOutboundMirrorMatchTroves(outboundMirrorId)
            for x in matchStrings:
                if x.startswith('+group'):
                    mirrorData['group'] = x[1:]
            mirrorData['mirrorSources'] = "-.*:source" not in matchStrings
            rows.append(mirrorData)

        return self._write('admin/outbound', rows = rows)

    def addOutbound(self, *args, **kwargs):
        projects = self.client.getProjectsList()
        return self._write('admin/add_outbound', projects = projects, kwargs = kwargs)

    def _genPasswd(self):
        import random
        random = random.SystemRandom()
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789"
        len = 128
        chars = ''
        for x in range(len):
            chars += random.choice(allowed)
        return chars

    def _updateMirror(self, user, servername, host, sp):
        passwd = ''
        try:
            res1 = sp.conaryserver.ConaryServer.addServerName(servername)
            passwd = sp.mirrorusers.MirrorUsers.addRandomUser(user)
            
            rapa_passwd = self._genPasswd()
            passData = self.client.getrAPAPassword(host, 'serverNames')
            server_user = host.replace('.', '_')
            # Create serverName group if it doesn't exist
            users = sp.usermanagement.UserInterface.users()
            if 'serverNames' not in users['all_groups']:
                sp.usermanagement.UserInterface.addGroup('serverNames', 
                                                     ['serverNames'])
            # Recreate the user if it arleady exists
            for x in users['items']:
                if x['username'] == server_user:
                    sp.usermanagement.UserInterface.deleteUser(server_user)
                    break
            sp.usermanagement.UserInterface.addUser(server_user, rapa_passwd, rapa_passwd, ['serverNames'])
            # Update the password in our database
            self.client.setrAPAPassword(host, server_user, rapa_passwd, 'serverNames')
        except xmlrpclib.ProtocolError, e:
            safeUrl = cleanseUrl('https', e.url)
            if e.errcode == 403:
                self._addErrors("Username and/or password incorrect.")
            else:
                self._addErrors("""Protocol error: %s (%d %s). Please be sure your
                                      rPath Mirror is configured properly.""" % \
                    (safeUrl, e.errcode, e.errmsg))
        except socket.error, e:
            self._addErrors("""Socket error: %s. Please be sure your rPath Mirror
                               is configured properly.""" % str(e[1]))
        else:
            if not res1 or not passwd:
                self._addErrors("""An error occured configuring your rPath
                                   Mirror.""")
        # Clear the mirror mark for this server name
        ccfg = conarycfg.ConaryConfiguration()
        ccfg.user.addServerGlob(servername, user, passwd)
        ccfg.repositoryMap.update({servername:'https://%s/conary/' % host})
        cc = conaryclient.ConaryClient(ccfg)
        try:
            cc.repos.setMirrorMark(servername, -1)
        except errors.OpenError:
            # This servername is not configured yet, so ignore
            pass

        return passwd

    @intFields(projectId = None)
    @boolFields(mirrorSources = False, allLabels = False)
    @strFields(mirrorBy = 'label')
    def processAddOutbound(self, projectId, mirrorSources, allLabels, mirrorBy, *args, **kwargs):
        inputKwargs = {'projectId': projectId,
            'mirrorSources': mirrorSources, 'allLabels': allLabels}

        if not self._getErrors():
            project =  self.client.getProject(projectId)
            label = project.getLabel()
            labelList = [label]
            recurse = mirrorBy == 'group'
            outboundMirrorId = self.client.addOutboundMirror(projectId,
                    labelList, allLabels, recurse)
            matchTroveList = []
            if mirrorBy == 'group':
                if not mirrorSources:
                    matchTroveList = ["-.*:source", "-.*:debuginfo", '+%s' % kwargs['groups']]
                else:
                    matchTroveList = ['+%s' % kwargs['groups']]
            elif not mirrorSources:
                matchTroveList = mirror.EXCLUDE_SOURCE_MATCH_TROVES
            self.client.setOutboundMirrorMatchTroves(outboundMirrorId,
                               matchTroveList)
            self._redirect("http://%s%sadmin/outbound" %
                (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self.addOutbound(**inputKwargs)

    @intFields(id = -1)
    def addOutboundMirrorTarget(self, id, *args, **kwargs):
        om = self.client.getOutboundMirror(id)
        targets = [ getUrlHost(x[1]) for x in self.client.getOutboundMirrorTargets(id) ]
        project = self.client.getProject(om['sourceProjectId'])
        return self._write("admin/mirrortarget",
                projectName = project.name,
                targets = targets,
                outboundMirrorId = id, kwargs = kwargs)

    @intFields(outboundMirrorId = -1)
    @strFields(targetUrl = '', mirrorUser = '', mirrorPass = '')
    def processAddOutboundMirrorTarget(self, outboundMirrorId, targetUrl, mirrorUser, mirrorPass, *args, **kwargs):
        if not mirrorUser:
            self._addErrors("Missing Update Service Username")
        if not mirrorPass:
            self._addErrors("Missing Update Service Password")
        if not targetUrl:
            self._addErrors("Missing Update Service Hostname")

        inputKwargs = {'id': outboundMirrorId,
                       'targetUrl': targetUrl, 'mirrorUser': mirrorUser,
                       'mirrorPass': mirrorPass}

        urltype, mirrorUrl = urllib.splittype(targetUrl)
        if not urltype:
            mirrorUrl = '//' + mirrorUrl
        mirrorUrl, ignoreMe = urllib.splithost(mirrorUrl)

        if not self._getErrors():
            om = self.client.getOutboundMirror(outboundMirrorId)
            project = self.client.getProject(om['sourceProjectId'])
            targetHosts = [ getUrlHost(x[1]) for x in self.client.getOutboundMirrorTargets(outboundMirrorId) ]
            if mirrorUrl in targetHosts:
                self._addErrors("This outbound mirror is already configured to mirror to %s" % mirrorUrl)

        if not self._getErrors():
            servername = self.client.translateProjectFQDN(project.getFQDN())
            group = None
            for x in om['matchStrings'].split(' '):
                if x.startswith('+group'):
                    group = x.lstrip('+')
            if group:
                user = '%s-%s-%s' % (group, servername, mirrorUrl)
            else:
                user = '%s-%s' % (servername, mirrorUrl)
            sp = xmlrpclib.ServerProxy("https://%s:%s@%s:8003/rAA/xmlrpc/" % (mirrorUser, mirrorPass, mirrorUrl))
            passwd = self._updateMirror(user, servername, mirrorUrl, sp)

        if not self._getErrors():
            outboundMirrorTargetId = self.client.addOutboundMirrorTarget(outboundMirrorId, 'https://%s/conary/' % mirrorUrl, user, passwd)
            self._redirect("http://%s%sadmin/outbound" %
                (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self.addOutboundMirrorTarget(**inputKwargs)

    @intFields(id = -1)
    def removeOutboundMirrorTarget(self, id, *args, **kwargs):
        omt = self.client.getOutboundMirrorTarget(id)
        om = self.client.getOutboundMirror(omt['outboundMirrorId'])
        project = self.client.getProject(om['sourceProjectId'])
        message = 'Delete target %s for outbound mirrored project %s?' % \
                (getUrlHost(omt['url']), project.name)
        noLink = 'outbound'
        yesArgs = {'func': 'processRemoveOutboundMirrorTarget', 'id': id}
        return self._write('confirm', message=message, noLink=noLink,
                           yesArgs=yesArgs)

    @intFields(id = -1)
    def processRemoveOutboundMirrorTarget(self, id, *args, **kwargs):
        try:
            self.client.delOutboundMirrorTarget(id)
        except:
            self._addErrors("Failed to delete outbound mirror target")

        self._redirect("http://%s%sadmin/outbound" %
            (self.cfg.siteHost, self.cfg.basePath))

    @listFields(int, remove = [])
    @boolFields(confirmed = False)
    def removeOutbound(self, remove, confirmed, **yesArgs):
        if confirmed:
            remove = simplejson.loads(yesArgs['removeJSON'])
            for outboundMirrorId in remove:
                self.client.delOutboundMirror(int(outboundMirrorId))
            self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))
        else:
            if not remove:
                self._addErrors("No outbound mirrors to delete.")
                self._redirect("http://%s%sadmin/outbound" % (self.cfg.siteHost, self.cfg.basePath))
            message = 'Are you sure you want to remove the outbound mirror(s)?'
            noLink = 'outbound'
            yesArgs = {'func': 'removeOutbound', 'confirmed': 1,
                    'removeJSON': simplejson.dumps(remove)}
            return self._write('confirm', message=message, noLink=noLink,
                               yesArgs=yesArgs)

    def maintenance(self, *args, **kwargs):
        return self._write('admin/maintenance', kwargs = kwargs)

    @intFields(curMode = None)
    def toggleMaintLock(self, curMode, *args, **kwargs):
        mode = curMode ^ 1
        maintenance.setMaintenanceMode(self.cfg, mode)
        self._redirect("http://%s%sadmin/maintenance" % (self.cfg.siteHost, self.cfg.basePath))
