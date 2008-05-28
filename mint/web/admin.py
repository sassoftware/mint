#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#

import os
import sys
import BaseHTTPServer
import xmlrpclib
import urllib
import socket
import md5

from conary import conarycfg
from conary import conaryclient
from conary.repository import errors

from mod_python import apache

from mint import users
from mint import maintenance
from mint import mirror
from mint.helperfuncs import getUrlHost, getProjectText
from mint.mint_error import *
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
        self.req.headers_out.add('Content-Disposition', "attachment; filename=%s.pdf" % (kwargs['reportName']))
        return pdfData

    def _validateExternalProject(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntKey,
                        useMirror, authType,
                        additionalLabelsToMirror, allLabels, backupExternal):
        additionalLabels = []
        extLabel = ""
        pText = getProjectText().lower()
        if not name:
            self._addErrors("Missing %s title"%pText)
        if not hostname:
            self._addErrors("Missing %s name"%pText)
        if not label:
            self._addErrors("Missing %s label"%pText)
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
                    self._addErrors('Missing entitlement key for local mirror authentication')
                if externalEntKey:
                    # Test that the entitlement is valid
                    cfg = conarycfg.ConaryConfiguration()
                    if url:
                        cfg.configLine('repositoryMap %s %s' % (extLabel.host,
                                                                url))

                    cfg.entitlement.addEntitlement(extLabel.host, externalEntKey)
                    nc = conaryclient.ConaryClient(cfg).getRepos()
                    try:
                        # use 2**64 to ensure we won't make the server do much
                        nc.getNewTroveList(extLabel.host, '4611686018427387904')
                    except errors.InsufficientPermission:
                        self._addErrors("Entitlement does not grant mirror access to external repository")
                    except errors.OpenError, e:
                        if url:
                            self._addErrors("Error contacting remote repository. Please ensure entitlement and repository URL are correct. (%s)" % str(e))
                        else:
                            self._addErrors("Error contacting remote repository. Please ensure entitlement is correct. (%s)" % str(e) )

        if additionalLabelsToMirror and allLabels:
            self._addErrors("Do not request additional labels and all labels to be mirrored: these options are exclusive.")
        return additionalLabels, extLabel

    @strFields(name = '', hostname = '', label = '', url = '',\
        externalUser = '', externalPass = '', externalEntKey = '',\
        authType = 'none',\
        additionalLabelsToMirror = '', useMirror = 'none')
    @intFields(projectId = -1)
    @boolFields(allLabels = False, backupExternal=False)
    def processAddExternal(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntKey,
                        useMirror, authType, additionalLabelsToMirror,
                        projectId, allLabels, backupExternal, *args, **kwargs):


        # strip extraneous whitespace
        externalEntKey = externalEntKey.strip()

        kwargs = {'name': name, 'hostname': hostname, 'label': label,
            'url': url, 'authType': authType, 'externalUser': externalUser,
            'externalPass': externalPass,
            'externalEntKey': externalEntKey,
            'useMirror': useMirror,
            'additionalLabelsToMirror': additionalLabelsToMirror,
            'allLabels': allLabels,
            'backupExternal': backupExternal,
            }

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
            project.setBackupExternal(backupExternal)

            labelIdMap = self.client.getLabelsForProject(projectId)[0]
            label, labelId = labelIdMap.items()[0]

            if not url and not externalAuth:
                url = "http://%s/conary/" % extLabel.getHost()
            elif not url and externalAuth:
                url = "https://%s/conary/" % extLabel.getHost()

            if not authType in ('none', 'userpass', 'entitlement'):
                raise RuntimeError, "Invalid authentication type specified"

            # set up the authentication
            project.editLabel(labelId, str(extLabel), url,
                authType, externalUser, externalPass, externalEntKey)

            mirror = self.client.getInboundMirror(projectId)
            # set up the mirror, if requested
            if useMirror == 'net':
                localUrl = "http%s://%s%srepos/%s/" % (self.cfg.SSL and 's' or\
                           '', self.cfg.projectSiteHost, self.cfg.basePath, 
                           hostname)

                # set the internal label to our authUser and authPass
                project.editLabel(labelId, str(extLabel), localUrl,
                    'userpass', self.cfg.authUser, self.cfg.authPass, '')

                if mirror and editing:
                    mirrorId = mirror['inboundMirrorId']
                    self.client.editInboundMirror(mirrorId, [str(extLabel)] +
                        additionalLabels, url, authType, externalUser,
                        externalPass, externalEntKey, allLabels)
                else:
                    self.client.addInboundMirror(projectId, [str(extLabel)] +
                        additionalLabels, url, authType, externalUser,
                        externalPass, externalEntKey, allLabels)
                    self.client.addRemappedRepository(hostname + "." + self.cfg.siteDomainName, extLabel.getHost())
            # remove mirroring if requested
            elif useMirror == 'none' and mirror and editing:
                self.client.delInboundMirror(mirror['inboundMirrorId'])
                self.client.delRemappedRepository(hostname + "." + self.cfg.siteDomainName)

            verb = editing and "Edited" or "Added"
            self._setInfo("%s external %s %s" % (verb, getProjectText().lower(), name))
            self._redirect("http://%s%sadmin/external" %
                (self.cfg.siteHost, self.cfg.basePath))
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
            self.client.getProjectByHostname('rap')
        except ItemNotFound:
            firstTime = True
            kwargs.setdefault('name', 'rPath Appliance Platform - Linux Service')
            kwargs.setdefault('hostname', 'rap')
            kwargs.setdefault('url', 'https://rap.rpath.com/conary/')
            kwargs.setdefault('label', 'rap.rpath.com@rpath:linux-1')
            kwargs.setdefault('allLabels', 0)
            kwargs.setdefault('backupExternal', 0)
        else:
            firstTime = False

        return self._write('admin/addExternal', firstTime = firstTime,
                editing = False, mirrored = False, projectId = -1,
                kwargs = kwargs, initialKwargs = {})

    @intFields(projectId = None)
    def editExternal(self, projectId, *args, **kwargs):
        project = self.client.getProject(projectId)
        labelInfo = self.client.getLabel(projectId)
        label = labelInfo['label']
        conaryCfg = project.getConaryConfig()

        initialKwargs = {}
        initialKwargs['name'] = project.name
        initialKwargs['hostname'] = project.hostname
        initialKwargs['label'] = label
        initialKwargs['backupExternal'] = project.backupExternal

        fqdn = versions.Label(label).getHost()
        initialKwargs['url'] = conaryCfg.repositoryMap[fqdn]
        userMap = conaryCfg.user.find(fqdn)

        initialKwargs['authType'] = labelInfo['authType']
        initialKwargs['externalUser'] = labelInfo['username']
        initialKwargs['externalPass'] = labelInfo['password']
        initialKwargs['externalEntKey'] = labelInfo['entitlement']

        initialKwargs['useMirror'] = 'none'
        mirrored = False
        mirror = self.client.getInboundMirror(projectId)
        if mirror:
            labels = mirror['sourceLabels'].split()
            if label in labels:
                labels.remove(label)

            initialKwargs['url'] = mirror['sourceUrl']
            initialKwargs['authType'] = mirror['sourceAuthType']
            initialKwargs['externalUser'] = mirror['sourceUsername']
            initialKwargs['externalPass'] = mirror['sourcePassword']
            initialKwargs['externalEntKey'] = mirror['sourceEntitlement']
            initialKwargs['additionalLabelsToMirror'] = " ".join(labels)
            initialKwargs['allLabels'] = mirror['allLabels']
            initialKwargs['useMirror'] = 'net'
            mirrored = True

        return self._write('admin/addExternal', firstTime = False,
            editing = True, mirrored = mirrored, kwargs = kwargs,
            initialKwargs = initialKwargs, projectId = projectId)


    def external(self, auth):
        pText = getProjectText().title()
        regColumns = ['%s Name'%pText, 'Mirrored']
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
        mirrorColumns = ['Mirrored %s Name'%pText, 'Order']
        mirrorRows = []
        for i, (project, mirrored) in enumerate(mirroredProjects):
            orderHtml = self._makeMirrorOrderingLinks("InboundMirror",
                len(mirroredProjects), mirrored['mirrorOrder'], i, mirrored['inboundMirrorId'])
            data = [('editExternal?projectId=%s' % project.id, project.name), orderHtml]
            mirrorRows.append({'columns': data})

        return self._write('admin/external',
            regColumns = regColumns, regRows = regRows,
            mirrorColumns = mirrorColumns, mirrorRows = mirrorRows)

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
    @strFields(title='')
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
        for i, (outboundMirrorId, projectId, label, allLabels, recurse, \
          matchStrings, order, fullSync, useReleases) in enumerate(mirrors):
            project = self.client.getProject(projectId)
            mirrorData = {}
            mirrorData['id'] = outboundMirrorId
            mirrorData['projectName'] = project.name
            mirrorData['projectUrl'] = project.getUrl()
            mirrorData['orderHTML'] = self._makeMirrorOrderingLinks("OutboundMirror", len(mirrors), order, i, outboundMirrorId)
            mirrorData['useReleases'] = int(useReleases)
            mirrorData['allLabels'] = allLabels
            if not allLabels:
                mirrorData['labels'] = label.split(' ')
            mirrorData['targets'] = [ (x[0], x[1]) for x in self.client.getOutboundMirrorTargets(outboundMirrorId) ]
            mirrorData['ordinal'] = i
            matchStrings = self.client.getOutboundMirrorMatchTroves(outboundMirrorId)
            mirrorData['groups'] = self.client.getOutboundMirrorGroups(outboundMirrorId)
            mirrorData['mirrorSources'] = not set(mirror.EXCLUDE_SOURCE_MATCH_TROVES).issubset(set(matchStrings))
            rows.append(mirrorData)

        return self._write('admin/outbound', rows = rows)

    @intFields(id=-1)
    def editOutbound(self, id, *args, **kwargs):
        projects = self.client.getProjectsList()
        allTargets = self.client.getUpdateServiceList()
        isNew = (id == -1)
        if not isNew:
            obm = self.client.getOutboundMirror(id)
            obmg = self.client.getOutboundMirrorGroups(id)
            obmt = self.client.getOutboundMirrorTargets(id)
            kwargs.update({'projectId': obm['sourceProjectId'],
                           'mirrorSources': not set(mirror.EXCLUDE_SOURCE_MATCH_TROVES).issubset(set(obm['matchStrings'].split())),
                           'useReleases': int(obm['useReleases']),
                           'allLabels': obm['allLabels'],
                           'selectedLabels': simplejson.dumps(obm['targetLabels'].split()),
                           'selectedGroups': simplejson.dumps(obmg),
                           'mirrorBy': obmg and 'group' or 'label',
                           'selectedTargets': [x[0] for x in obmt],
                           'allTargets': allTargets})
        else:
            kwargs.update({'projectId': -1,
                           'mirrorSources': 0,
                           'useReleases': 1,
                           'allLabels': 1,
                           'selectedLabels': simplejson.dumps([]),
                           'selectedGroups': simplejson.dumps([]),
                           'mirrorBy': 'label',
                           'selectedTargets': [],
                           'allTargets': allTargets})
        return self._write('admin/editOutbound', isNew=isNew, id=id, projects = projects, kwargs = kwargs)


    @intFields(projectId = None, id = -1)
    @boolFields(mirrorSources=False, allLabels=False, useReleases=True)
    @listFields(str, labelList=[])
    @listFields(str, groups=[])
    @listFields(int, selectedTargets=[])
    @strFields(mirrorBy = 'label', action = "Cancel")
    def processEditOutbound(self, projectId, mirrorSources, allLabels,
            labelList, id, mirrorBy, groups, action, selectedTargets,
            useReleases, *args, **kwargs):

        if action == "Cancel":
            self._redirect("http://%s%sadmin/outbound" %
                (self.cfg.siteHost, self.cfg.basePath))

        inputKwargs = {}
        for key in ('projectId', 'mirrorSources', 'allLabels', 'id',
          'mirrorBy', 'selectedTargets', 'useReleases'):
            inputKwargs[key] = locals()[key]
        inputKwargs['selectedLabels'] = labelList
        inputKwargs['selectedGroups'] = groups

        if not useReleases:
            if not labelList and not allLabels:
                self._addErrors("No labels were selected")

            # compute the match troves expression
            matchTroveList = []
            if not mirrorSources:
                matchTroveList.extend(mirror.EXCLUDE_SOURCE_MATCH_TROVES)
            if mirrorBy == 'group':
                if not groups:
                    self._addErrors("No groups were selected")
                else:
                    matchTroveList.extend(['+%s' % (g,) for g in groups])
            else:
                # make sure we include everything else if we are not in
                # mirror by group mode
                matchTroveList.extend(mirror.INCLUDE_ALL_MATCH_TROVES)

        if not self._getErrors():
            project = self.client.getProject(projectId)
            recurse = (mirrorBy == 'group')
            outboundMirrorId = self.client.addOutboundMirror(projectId,
                    labelList, allLabels, recurse, useReleases, id=id)
            if not useReleases:
                self.client.setOutboundMirrorMatchTroves(outboundMirrorId,
                    matchTroveList)
            self.client.setOutboundMirrorTargets(outboundMirrorId,
                    selectedTargets)
            self._redirect("http://%s%sadmin/outbound" %
                (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self.editOutbound(**inputKwargs)

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

    def updateServices(self, *args, **kwargs):
        updateServices = self.client.getUpdateServiceList()
        return self._write('admin/updateServices',
                updateServices = updateServices)

    @intFields(id = -1)
    def editUpdateService(self, id, *args, **kwargs):
        isNew = (id == -1)
        if not isNew:
            kwargs.update(self.client.getUpdateService(id))
        else:
            kwargs.setdefault('id', -1)
            kwargs.setdefault('hostname', '')
            kwargs.setdefault('adminUser', '')
            kwargs.setdefault('adminPassword', '')
            kwargs.setdefault('description', '')

        return self._write('admin/editUpdateService', id=id, isNew = isNew,
                kwargs = kwargs)

    @intFields(id = -1)
    @strFields(hostname = '', adminUser = '', adminPassword = '',
            description = '', action = 'Cancel')
    def processEditUpdateService(self, id, hostname, adminUser, adminPassword,
            description, action, *args, **kwargs):

        if action == "Cancel":
            self._redirect("http://%s%sadmin/updateServices" %
                    (self.cfg.siteHost, self.cfg.basePath))

        inputKwargs = {'hostname': hostname,
            'adminUser': adminUser,
            'adminPassword': adminPassword,
            'description': description}

        # these are only necessary during a first time setup of an update
        # service
        if not hostname and id == -1:
            self._addErrors('No hostname specified')
        if not adminUser and id == -1:
            self._addErrors('No username specified')
        if not adminPassword and id == -1:
            self._addErrors('No password specified')

        if not self._getErrors():
            if id == -1:
                try:
                    self.client.addUpdateService(hostname, adminUser,
                            adminPassword, description)
                except Exception, e:
                    self._addErrors("Failed to add Update Service: %s" % \
                            str(e))
                else:
                    self._setInfo("Update Service added")
            else:
                self.client.editUpdateService(id, description)
                self._setInfo("Update Service changed")

        if not self._getErrors():
            self._redirect("http://%s%sadmin/updateServices" %
                (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self.editUpdateService(**inputKwargs)

    @listFields(int, remove = [])
    @boolFields(confirmed = False)
    def removeUpdateServices(self, remove, confirmed, **yesArgs):
        if confirmed:
            remove = simplejson.loads(yesArgs['removeJSON'])
            for updateServiceId in remove:
                self.client.delUpdateService(int(updateServiceId))
            self._setInfo("Update service(s) removed")
            self._redirect("http://%s%sadmin/updateServices" %
                    (self.cfg.siteHost, self.cfg.basePath))
        else:
            if not remove:
                self._addErrors("No update services to delete.")
                self._redirect("http://%s%sadmin/updateServices" %
                        (self.cfg.siteHost, self.cfg.basePath))
            message = 'Are you sure you want to remove the update service(s)?'
            noLink = 'updateServices'
            yesArgs = {'func': 'removeUpdateServices', 'confirmed': 1,
                    'removeJSON': simplejson.dumps(remove)}
            return self._write('confirm', message=message, noLink=noLink,
                               yesArgs=yesArgs)

