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

import logging
import json
from conary import conarycfg
from conary import conaryclient
from conary.repository import errors
from webob import exc as web_exc

from mint import maintenance
from mint.helperfuncs import getProjectText, configureClientProxies
from mint.scripts import mirror as mirrormod
from mint.web.webhandler import normPath, WebHandler
from mint.web.fields import strFields, intFields, listFields, boolFields

from conary import versions

from kid.parser import XML


log = logging.getLogger(__name__)


class AdminHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        if not self.auth.admin:
            raise web_exc.HTTPForbidden()

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        if not cmd:
            return self._frontPage
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            raise web_exc.HTTPNotFound()

        if not callable(method):
            raise web_exc.HTTPNotFound()

        return method

    def _frontPage(self, *args, **kwargs):
        return self._write('admin/frontPage', kwargs = kwargs)

    def _validateExternalProject(self, name, hostname, label, url,
                        externalUser, externalPass,
                        externalEntKey,
                        useMirror, authType,
                        additionalLabelsToMirror, allLabels, backupExternal):
        additionalLabels = []
        extLabel = ""
        pText = getProjectText().lower()

        # Validate simple parameters
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

        if self._getErrors():
            return None, None

        # Parse and check additional labels
        if useMirror == 'net' and additionalLabelsToMirror:
            for l in additionalLabelsToMirror.split():
                # skip a redundant label specification
                if l != label:
                    try:
                        versions.Label(l)
                        additionalLabels.append(l)
                    except versions.ParseError:
                        self._addErrors("Invalid additional label %s" % l)

        # Check authentication data
        if authType != 'none':
            if authType == 'userpass':
                if not externalUser:
                    self._addErrors("Missing username for local mirror authentication")
                if not externalPass:
                    self._addErrors("Missing password for local mirror authentication")
            elif authType == 'entitlement':
                if not externalEntKey:
                    self._addErrors('Missing entitlement key for local mirror authentication')
                else:
                    # Test that the entitlement is valid
                    cfg = conarycfg.ConaryConfiguration()
                    if url:
                        cfg.configLine('repositoryMap %s %s' % (extLabel.host,
                                                                url))

                    cfg.entitlement.addEntitlement(extLabel.host, externalEntKey)
                    cfg = configureClientProxies(cfg, False, self.cfg.proxy)
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
            inboundMirror = self.client.getInboundMirror(projectId)

            # set up the mirror, if requested
            if useMirror == 'net':
                localUrl = "http%s://%s%srepos/%s/" % (self.cfg.SSL and 's' or\
                           '', self.cfg.siteHost, self.cfg.basePath, 
                           hostname)

                # set the internal label to our authUser and authPass
                project.editLabel(labelId, str(extLabel), localUrl,
                    'userpass', self.cfg.authUser, self.cfg.authPass, '')

                if inboundMirror and editing:
                    mirrorId = inboundMirror['inboundMirrorId']
                    self.client.editInboundMirror(mirrorId, [str(extLabel)] +
                        additionalLabels, url, authType, externalUser,
                        externalPass, externalEntKey, allLabels)
                else:
                    self.client.addInboundMirror(projectId, [str(extLabel)] +
                        additionalLabels, url, authType, externalUser,
                        externalPass, externalEntKey, allLabels)
            # remove mirroring if requested
            elif useMirror == 'none' and inboundMirror and editing:
                self.client.delInboundMirror(inboundMirror['inboundMirrorId'])

            verb = editing and "Edited" or "Added"
            self._setInfo("%s external %s %s" % (verb, getProjectText().lower(), name))
            self._redirectHttp("admin/external")
        else:
            if editing:
                return self.editExternal(projectId = projectId, **kwargs)
            else:
                return self.addExternal(**kwargs)

    @strFields(authType = 'none')
    def addExternal(self, *args, **kwargs):
        kwargs.setdefault('authtype', 'none')
        return self._write('admin/addExternal',
                editing = False, mirrored = False, projectId = -1,
                kwargs = kwargs, initialKwargs = {})

    @intFields(projectId = None)
    def editExternal(self, projectId, *args, **kwargs):
        project = self.client.getProject(projectId)
        labelIdMap = self.client.getLabelsForProject(projectId)[0]
        label, labelId = labelIdMap.items()[0]
        labelInfo = self.client.getLabel(labelId)
        conaryCfg = project.getConaryConfig()

        initialKwargs = {}
        initialKwargs['name'] = project.name
        initialKwargs['hostname'] = project.hostname
        initialKwargs['label'] = label
        initialKwargs['backupExternal'] = project.backupExternal

        fqdn = versions.Label(label).getHost()
        initialKwargs['url'] = conaryCfg.repositoryMap[fqdn]

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

        # NB: It would be great to not have to reach around the XMLRPC layer
        # here, but the old way scales very poorly (>30s on rBO w/ 12000
        # projects).
        mirroredProjects = []
        for repos in self.client.server._server.reposMgr.iterRepositories(
                'external'):
            project = self.client.getProject(repos.projectId)
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
            mirrorData['projectUrl'] = project.getUrl(self.baseUrl)
            mirrorData['orderHTML'] = self._makeMirrorOrderingLinks("OutboundMirror", len(mirrors), order, i, outboundMirrorId)
            mirrorData['useReleases'] = int(useReleases)
            mirrorData['allLabels'] = allLabels
            if not allLabels:
                mirrorData['labels'] = label.split(' ')
            mirrorData['targets'] = [ (x[0], x[1]) for x in self.client.getOutboundMirrorTargets(outboundMirrorId) ]
            mirrorData['ordinal'] = i
            matchStrings = self.client.getOutboundMirrorMatchTroves(outboundMirrorId)
            mirrorData['groups'] = self.client.getOutboundMirrorGroups(outboundMirrorId)
            mirrorData['mirrorSources'] = not set(mirrormod.EXCLUDE_SOURCE_MATCH_TROVES).issubset(set(matchStrings)) and not (useReleases or mirrorData['groups'])
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
                           'mirrorSources': not set(mirrormod.EXCLUDE_SOURCE_MATCH_TROVES).issubset(set(obm['matchStrings'].split())),
                           'useReleases': int(obm['useReleases']),
                           'allLabels': obm['allLabels'],
                           'selectedLabels': json.dumps(obm['targetLabels'].split()),
                           'selectedGroups': json.dumps(obmg),
                           'mirrorBy': obmg and 'group' or 'label',
                           'selectedTargets': [x[0] for x in obmt],
                           'allTargets': allTargets})
        else:
            kwargs.update({'projectId': -1,
                           'mirrorSources': 0,
                           'useReleases': 1,
                           'allLabels': 1,
                           'selectedLabels': json.dumps([]),
                           'selectedGroups': json.dumps([]),
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
            self._redirectHttp("admin/outbound")

        inputKwargs = {}
        for key in ('projectId', 'mirrorSources', 'allLabels', 'id',
          'mirrorBy', 'selectedTargets', 'useReleases'):
            inputKwargs[key] = locals()[key]
        inputKwargs['selectedLabels'] = labelList
        inputKwargs['selectedGroups'] = groups

        matchTroveList = []
        if not useReleases:
            if not labelList and not allLabels:
                self._addErrors("No labels were selected")

            # compute the match troves expression
            if mirrorBy == 'group':
                if not groups:
                    self._addErrors("No groups were selected")
                else:
                    matchTroveList.extend(['+%s' % (g,) for g in groups])
            else:
                if not mirrorSources:
                    matchTroveList.extend(mirrormod.EXCLUDE_SOURCE_MATCH_TROVES)
                # make sure we include everything else if we are not in
                # mirror by group mode
                matchTroveList.extend(mirrormod.INCLUDE_ALL_MATCH_TROVES)

        if not self._getErrors():
            recurse = (mirrorBy == 'group')
            outboundMirrorId = self.client.addOutboundMirror(projectId,
                    labelList, allLabels, recurse, useReleases, id=id)
            self.client.setOutboundMirrorMatchTroves(outboundMirrorId,
                matchTroveList)
            self.client.setOutboundMirrorTargets(outboundMirrorId,
                    selectedTargets)
            self._redirectHttp("admin/outbound")
        else:
            return self.editOutbound(**inputKwargs)

    @listFields(int, remove = [])
    @boolFields(confirmed = False)
    def removeOutbound(self, remove, confirmed, **yesArgs):
        if confirmed:
            remove = json.loads(yesArgs['removeJSON'])
            for outboundMirrorId in remove:
                self.client.delOutboundMirror(int(outboundMirrorId))
            self._redirectHttp("admin/outbound")
        else:
            if not remove:
                self._addErrors("No outbound mirrors to delete.")
                self._redirectHttp("admin/outbound")
            message = 'Are you sure you want to remove the outbound mirror(s)?'
            noLink = 'outbound'
            yesArgs = {'func': 'removeOutbound', 'confirmed': 1,
                    'removeJSON': json.dumps(remove)}
            return self._write('confirm', message=message, noLink=noLink,
                               yesArgs=yesArgs)

    def maintenance(self, *args, **kwargs):
        return self._write('admin/maintenance', kwargs = kwargs)

    @intFields(curMode = None)
    def toggleMaintLock(self, curMode, *args, **kwargs):
        mode = curMode ^ 1
        maintenance.setMaintenanceMode(self.cfg, mode)
        self._redirectHttp("admin/maintenance")

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
            self._redirectHttp("admin/updateServices")

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
                    log.exception("Failed to add update service %s:", hostname)
                    self._addErrors("Failed to add Update Service: %s" % \
                            str(e))
                else:
                    self._setInfo("Update Service added")
            else:
                self.client.editUpdateService(id, description)
                self._setInfo("Update Service changed")

        if not self._getErrors():
            self._redirectHttp("admin/updateServices")
        else:
            return self.editUpdateService(**inputKwargs)

    @listFields(int, remove = [])
    @boolFields(confirmed = False)
    def removeUpdateServices(self, remove, confirmed, **yesArgs):
        if confirmed:
            remove = json.loads(yesArgs['removeJSON'])
            for updateServiceId in remove:
                self.client.delUpdateService(int(updateServiceId))
            self._setInfo("Update service(s) removed")
            self._redirectHttp("admin/updateServices")
        else:
            if not remove:
                self._addErrors("No update services to delete.")
                self._redirectHttp("admin/updateServices")
            message = 'Are you sure you want to remove the update service(s)?'
            noLink = 'updateServices'
            yesArgs = {'func': 'removeUpdateServices', 'confirmed': 1,
                    'removeJSON': json.dumps(remove)}
            return self._write('confirm', message=message, noLink=noLink,
                               yesArgs=yesArgs)
