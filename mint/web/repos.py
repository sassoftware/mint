#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import difflib
import itertools
import os
import string
import sys

from mimetypes import guess_type

from urllib import quote, unquote

import json


from mint import userlevels
from mint import helperfuncs
from mint.mint_error import *
from mint.web import productversion
from mint.web.templates import repos
from mint.web.fields import strFields, listFields, intFields
from mint.web.webhandler import (WebHandler, normPath, HttpForbidden,
        HttpNotFound, HttpBadRequest)
from mint.web.decorators import ownerOnly

from conary import checkin
from conary import conaryclient
from conary.deps import deps
from conary.lib import sha1helper
from conary import versions
from conary.repository import errors
from conary.repository.shimclient import ShimNetClient
from conary import conarycfg
from conary import errors as conaryerrors
from conary.trove import Trove

class ConaryHandler(WebHandler, productversion.ProductVersionView):
    def _filterAuth(self, **kwargs):
        memberList = kwargs.get('memberList', [])
        if isinstance(memberList, str):
            memberList = [memberList]
        if self.cfg.authUser in memberList:
            return self._write("error", shortError="Invalid User Name",
                    error = "A user name you have selected is invalid.")
        if kwargs.get('roleName', None) == self.cfg.authUser:
            return self._write("error", shortError="Invalid Role Name",
                    error = "The role name you are attempting to edit is invalid.")
        return None

    @strFields(search = '')
    def getOpenPGPKey(self, auth, search, **kwargs):
        from conary.lib.openpgpfile import KeyNotFound
        # This function mimics limited key server behavior. The keyserver line
        # for a gpg command must be formed manually--because gpg doesn't
        # automatically know how to talk to limited key servers.
        # A correctly formed gpg command looks like:
        # 'gpg --keyserver=REPO_MAP/getOpenPGPKey?search=KEY_ID --recv-key KEY_ID'
        # example: 'gpg --keyserver=http://admin:111111@localhost/conary/getOpenPGPKey?search=F7440D78FE813C882212C2BF8AC2828190B1E477 --recv-key F7440D78FE813C882212C2BF8AC2828190B1E477'
        # repositories that allow anonymous users do not require userId/passwd
        try:
            keyData = self.repServer.getAsciiOpenPGPKey(self.authToken, 0, search)
        except KeyNotFound:
            return self._write("error", shortError = "Key Not Found", error = "OpenPGP Key %s is not in this repository" %search)
        return self._write("pgp_get_key", keyId = search, keyData = keyData)

    def pgpAdminForm(self, auth):
        admin = self.repServer.auth.authCheck(self.authToken, admin=True)

        if admin:
            users = self.repServer.auth.userAuth.getUserList()
            users.append('--Nobody--')
        else:
            users = [ self.authToken[0] ]

        # build a dict of useful information about each user's OpenPGP Keys
        # xml-rpc calls must be made before kid template is invoked
        openPgpKeys = {}
        for user in users:
            keys = []
            if user == '--Nobody--':
                userLookup = None
            else:
                userLookup = user

            for fingerprint in self.repServer.listUsersMainKeys(self.authToken, 0, userLookup):
                keyPacket = {}
                keyPacket['fingerprint'] = fingerprint
                keyPacket['subKeys'] = self.repServer.listSubkeys(self.authToken, 0, fingerprint)
                keyPacket['uids'] = self.repServer.getOpenPGPKeyUserIds(self.authToken, 0, fingerprint)
                keys.append(keyPacket)
            openPgpKeys[user] = keys

        return self._write("pgp_admin", users = users, admin=admin, openPgpKeys = openPgpKeys)

    def pgpAdminFormUI(self, auth):
        admin = self.repServer.auth.authCheck(self.authToken, admin=True)

        if admin:
            users = self.repServer.auth.userAuth.getUserList()
            users.append('--Nobody--')
        else:
            users = [ self.authToken[0] ]

        # build a dict of useful information about each user's OpenPGP Keys
        # xml-rpc calls must be made before kid template is invoked
        openPgpKeys = {}
        for user in users:
            keys = []
            if user == '--Nobody--':
                userLookup = None
            else:
                userLookup = user

            for fingerprint in self.repServer.listUsersMainKeys(self.authToken, 0, userLookup):
                keyPacket = {}
                keyPacket['fingerprint'] = fingerprint
                keyPacket['subKeys'] = self.repServer.listSubkeys(self.authToken, 0, fingerprint)
                keyPacket['uids'] = self.repServer.getOpenPGPKeyUserIds(self.authToken, 0, fingerprint)
                keys.append(keyPacket)
            openPgpKeys[user] = keys

        return self._write("pgp_adminUI", users = users, admin=admin, openPgpKeys = openPgpKeys)

    @strFields(key=None, owner="")
    def pgpChangeOwner(self, auth, owner, key):
        # The requiresAdmin decorator will not work with our authOveride
        # tuple, so check for admin here
        if not self.project:
            raise ItemNotFound("project")
        if not self.auth.admin:
            raise PermissionDenied

        if not owner or owner == '--Nobody--':
            owner = None
        self.repServer.changePGPKeyOwner(self.authToken, 0, owner, key)
        self._redirect('pgpAdminForm')

    @strFields(t = None, v = None, f = "")
    def files(self, t, v, f, auth):
        try:
            v = versions.ThawVersion(v)
            f = deps.ThawFlavor(f)
        except (conaryerrors.ParseError, ValueError):
            raise HttpBadRequest

        try:
            parentTrove = self.repos.getTrove(t, v, f, withFiles = False)
        except errors.TroveMissing:
            raise HttpNotFound

        # non-source group troves only show contained troves
        if t.startswith('group-') and not t.endswith(':source'):
            troves = sorted(parentTrove.iterTroveList(strongRefs=True))
            return self._write("group_contents", troveName = t, troves = troves)
        fileIters = []
        # XXX: Needs to be optimized
        # the walkTroveSet() will request a changeset for every
        # trove in the chain.  then iterFilesInTrove() will
        # request it again just to retrieve the filelist.
        for trove in self.repos.walkTroveSet(parentTrove, withFiles = False, asTuple = False):
            files = self.repos.iterFilesInTrove(
                trove.getName(),
                trove.getVersion(),
                trove.getFlavor(),
                withFiles = True,
                sortByPath = True)
            fileIters.append(files)
        fileIters = itertools.chain(*fileIters)

        return self._write("files",
            troveName = t,
            fileIters = fileIters)

    @strFields(t=None, v='', f='')
    def licenseCryptoReport(self, t, v, f, auth):
        try:
            tr = unquote(t)
            ver = versions.VersionFromString(unquote(v))
            fl = deps.parseFlavor(unquote(f))
        except:
            raise HttpBadRequest

        try:
            data = self._getLicenseAndCrypto(tr, ver, fl)
        except errors.TroveNotFound:
            raise HttpNotFound
        except Exception, err:
            return self._write("error",
                    error=('An error occurred while generating '
                        'the report: %s' % str(err)))


        return self._write('lic_crypto_report', troves=data, troveName=t)

    def _getLicenseAndCrypto(self, tr, ver, fl):
        groupCs = self.repos.createChangeSet([(tr, (None, None), (ver, fl),
                                               True)], withFiles=False,
                                             withFileContents=False, 
                                             recurse=True)
        data = []
        for cs in groupCs.iterNewTroveList():
            tr = Trove(cs, skipIntegrityChecks=True)
            if ':' in tr.getName():
                continue
            md = tr.getMetadata()
            licenses = []
            crypto = []
            for l, info in ((licenses, md['licenses']),
                            (crypto, md['crypto'])):
                if not info:
                    continue
                for x in info:
                    if x.startswith('rpath.com/'):
                        l.append('<a href="http://%s">%s</a>'
                                 %(x, os.path.basename(x)))
                    else:
                        l.append(x)
            data.append((tr.getName(), tr.getVersion(), tr.getFlavor(),
                         licenses, crypto))

        data.sort(cmp=lambda x,y: cmp(x[0], y[0]))
        return data

    def _recurseLineage(self, troveName, version, lineage):
        selectedVer = None
        # If the trove has a parent version, use that
        if version.hasParentVersion():
            selectedVer = version.parentVersion()
        # else use the parent of the source
        elif version.getSourceVersion().hasParentVersion():
            selectedVer = version.getSourceVersion().parentVersion()
        else:
            # else find the most recent unmodified shadow on this branch wrt 
            # the current trove and select its parent
            compBranch = version.getSourceVersion().branch()
            if not troveName[1]:
                trSrc = troveName[0]
            else:
                trSrc = troveName[1]
            troveVersions = self.repos.getTroveVersionsByBranch({trSrc: {compBranch: [None]}})
            if troveVersions.has_key(trSrc):
                sortedVersions = sorted(troveVersions[trSrc].keys(), reverse=True)
            else:
                sortedVersions = []

            troveMatch = False
            for ver in sortedVersions:
                if version.getSourceVersion() == ver:
                    troveMatch = True
                if not troveMatch:
                    continue
                if ver.isUnmodifiedShadow() and ver.hasParentVersion():
                    selectedVer = ver.parentVersion()
                    break

        if selectedVer:
            if selectedVer.isSourceVersion():
                trName = troveName[1] or troveName[0]
            else:
                trName = troveName[0]
            link = self._calculateLink(selectedVer, trName)
            formattedVersion, branch = self._formatForDisplay(selectedVer)
            lineage.append((formattedVersion, branch, link)) 
            return self._recurseLineage(troveName, selectedVer, lineage)
        else:
            return lineage

    def _formatForDisplay(self, version):
        if versions.Label(self.project.getLabel()).getHost() == version.getHost():
            shortVersion = '%s:%s/%s' % (version.trailingLabel().getNamespace(),
                                   version.trailingLabel().getLabel(),
                                   str(version.trailingRevision().getVersion()))
        else:
            shortVersion =  '%s/%s' % (version.trailingLabel(), 
                                  str(version.trailingRevision().getVersion()))
        return helperfuncs.splitVersionForDisplay(str(version)), shortVersion
        
    def _calculateLink(self, extVer, troveName):
        hostname = ''
        try:
            proj = self.client.getProjectByFQDN(extVer.getHost())
            hostname = proj.getHostname()
        except ItemNotFound:
            pass

        if hostname:
            return "../%s/troveInfo?t=%s;v=%s" % (hostname, troveName, quote(extVer.asString()))
        else:
            return ''
            
    @strFields(t = None, v = "")
    def troveInfo(self, t, v, auth):
        t = unquote(t)
        leaves = {}
        for serverName in self.serverNameList:
            newLeaves = self.repos.getTroveVersionList(serverName, {t: [None]})
            leaves.update(newLeaves)
        if t not in leaves:
            return self._write("error",
                               error = '%s was not found on this server.' %t)

        versionList = sorted(leaves[t].keys(), reverse = True)

        if not v:
            reqVer = versionList[0]
        else:
            try:
                reqVer = versions.ThawVersion(v)
            except (versions.ParseError, ValueError):
                try:
                    reqVer = versions.VersionFromString(v)
                except:
                    return self._write("error",
                                       error = "Invalid version: %s" %v)

        try:
            query = [(t, reqVer, x) for x in leaves[t][reqVer]]
        except KeyError:
            return self._write("error",
                               error = "Version %s of %s was not found on this server."
                               %(reqVer, t))
        troves = self.repos.getTroves(query, withFiles = False)

        # Find out if this trove is a clone or a shadow
        trove = troves[0]
        parentType = None
        lineage = []
        if trove.troveInfo.clonedFrom() and '@LOCAL:' not in trove.troveInfo.clonedFrom().asString():
            extVer = trove.troveInfo.clonedFrom()
            link = self._calculateLink(extVer, trove.getName())
            longV, shortV = self._formatForDisplay(extVer)
            lineage = [(longV, shortV, link)]
            parentType = 'Cloned from'
        elif trove.version.v.isShadow():
            lineage = self._recurseLineage((trove.getName(), trove.getSourceName()), trove.version.v, [])
            parentType = 'Shadowed from'

        # Build a version list for loading into a treeview
        labels = {}
        for ver in versionList:
            revs = labels.get(str(ver.trailingLabel()), [])
            cssClass = ''
            if ver == reqVer:
                cssClass = 'bold'
            if ver.isShadow():
                cssClass += 'shadow'
            revs.append([str(ver.trailingRevision()), 'troveInfo?t=%s;v=%s' % (quote(t), quote(ver.freeze())), cssClass])
            labels[str(ver.trailingLabel())] = revs

        return self._write("trove_info", troveName = t, troves = troves,
            verList=json.dumps(labels), selectedLabel = json.dumps(str(reqVer.trailingLabel())), parentType=parentType, lineage=json.dumps(lineage))

    @strFields(char = '')
    def browse(self, char, auth):
        defaultPage = False
        if not char:
            char = 'A'
            defaultPage = True
        # since the repository is multihomed and we're not doing any
        # label filtering, a single call will return all the available
        # troves. We use the first repository name here because we have to
        # pick one,,,
        troves = self.repos.troveNamesOnServer(self.serverNameList[0])

        # keep a running total of each letter we see so that the display
        # code can skip letters that have no troves
        totals = dict.fromkeys(list(string.digits) + list(string.uppercase), 0)
        packages = []
        components = {}

        # In order to jump to the first letter with troves if no char is specified
        # We have to iterate through troves twice.  Since we have hundreds of troves,
        # not thousands, this isn't too big of a deal.  In any case this will be
        # removed soon when we move to a paginated browser
        for trove in troves:
            totals[trove[0].upper()] += 1
        if defaultPage:
            for x in string.uppercase:
                if totals[x]:
                    char = x
                    break

        if char in string.digits:
            char = '0'
            filter = lambda x: x[0] in string.digits
        else:
            filter = lambda x, char=char: x[0].upper() == char

        for trove in troves:
            if not filter(trove):
                continue
            if ":" not in trove:
                packages.append(trove)
            else:
                package, component = trove.split(":")
                l = components.setdefault(package, [])
                l.append(component)

        # add back troves that do not have a parent package container
        # to the package list
        noPackages = set(components.keys()) - set(packages)
        for x in noPackages:
            for component in components[x]:
                packages.append(x + ":" + component)

        return self._write("browse", packages = sorted(packages),
                           components = components, char = char, totals = totals)

    @strFields(path = None, pathId = None, fileId = None, fileV = None)
    def getFile(self, path, pathId, fileId, fileV, auth):
        pathId = sha1helper.md5FromString(pathId)
        fileId = sha1helper.sha1FromString(fileId)
        ver = versions.VersionFromString(fileV)

        fileObj = self.repos.getFileVersion(pathId, fileId, ver)
        contents = self.repos.getFileContents([(fileId, ver)])[0]

        if fileObj.flags.isConfig():
            self.req.content_type = "text/plain"
        else:
            typeGuess = guess_type(path)

            self.req.headers_out["Content-Disposition"] = "attachment; filename=%s;" % path
            if typeGuess[0]:
                self.req.content_type = typeGuess[0]
            else:
                self.req.content_type = "application/octet-stream"

        self.req.headers_out["Content-Length"] = fileObj.sizeString()
        return contents.get().read()

    @ownerOnly
    def userlist(self, auth):
        return self._write("user_admin", netAuth = self.repServer.auth)

    @ownerOnly
    @strFields(roleName = None)
    def deleteRole(self, auth, roleName):
        self.repServer.auth.deleteRole(roleName)
        self._filterAuth(roleName=roleName) or self._redirect("userlist")

    @ownerOnly
    @strFields(roleName = "")
    def addPermForm(self, auth, roleName):
        roles = self.repServer.auth.getRoleList()
        labels = self.repServer.auth.getLabelList()
        troves = self.repServer.auth.getItemList()

        return self._write("permission", operation='Add', role=roleName, trove=None,
            label=None, roles=roles, labels=labels, troves=troves,
            writeperm=None, capped=None, admin=None, remove=None)

    @ownerOnly
    @strFields(role = None, label = "", trove = "",
               writeperm = "off", capped = "off", admin = "off", remove = "off")
    def addPerm(self, auth, role, label, trove,
                writeperm, capped, admin, remove):
        writeperm = (writeperm == "on")
        capped = (capped == "on")
        admin = (admin == "on")
        remove = (remove== "on")

        try:
            self.repServer.addAcl(self.authToken, 0, role, trove, label,
               writeperm, remove)
        except errors.PermissionAlreadyExists, e:
            return self._write("error", shortError="Duplicate Permission",
                error = "Permissions have already been set for %s, please go back and select a different User, Label or Trove." % str(e))

        self._redirect("userlist")

    @ownerOnly
    def addRoleForm(self, auth):
        users = self.repServer.auth.userAuth.getUserList()
        return self._write("add_role", modify = False, roleName = None, users = users, members = [], canMirror = False)

    @ownerOnly
    @strFields(roleName = None)
    def manageRoleForm(self, auth, roleName):
        users = self.repServer.auth.userAuth.getUserList()
        members = set(self.repServer.auth.getRoleMembers(roleName))
        canMirror = self.repServer.auth.roleCanMirror(roleName)

        return self._filterAuth(auth=auth, roleName=roleName) or self._write("add_role", roleName = roleName, users = users, members = members, canMirror = canMirror, modify = True)

    @ownerOnly
    @strFields(roleName = None, newRoleName = None)
    @listFields(str, memberList = [])
    @intFields(canMirror = False)
    def manageRole(self, auth, roleName, newRoleName, memberList,
                    canMirror):
        if roleName != newRoleName:
            try:
                self.repServer.auth.renameRole(roleName, newRoleName)
            except errors.RoleAlreadyExists:
                return self._write("error", shortError="Invalid Role Name",
                    error = "The role name you have chosen is already in use.")

            roleName = newRoleName

        self.repServer.auth.updateRoleMembers(roleName, memberList)
        self.repServer.auth.setMirror(roleName, canMirror)

        self._filterAuth(memberList=memberList, roleName=roleName) or self._redirect("userlist")

    @ownerOnly
    @strFields(newRoleName = '')
    @listFields(str, memberList = [])
    @intFields(canMirror = False)
    def addRole(self, auth, newRoleName, memberList, canMirror):
        if not newRoleName or newRoleName.isspace():
            return self._write("error", shortError="Invalid Role Name",
                error = "Please enter a valid role name.")

        try:
            self.repServer.auth.addRole(newRoleName)
        except errors.RoleAlreadyExists:
            return self._write("error", shortError="Invalid Role Name",
                error = "The role name you have chosen is already in use.")

        self.repServer.auth.updateRoleMembers(newRoleName, memberList)
        self.repServer.auth.setMirror(newRoleName, canMirror)

        self._filterAuth(memberList=memberList) or self._redirect("userlist")

    @ownerOnly
    @strFields(role = None, label = None, item = None)
    def deletePerm(self, auth, role, label, item):
        # labelId and itemId are optional parameters so we can't
        # default them to None: the fields decorators treat that as
        # required, so we need to reset them to None here:
        if not label or label == "ALL":
            label = None
        if not item or item == "ALL":
            item = None

        self.repServer.auth.deleteAcl(role, label, item)
        self._redirect("userlist")

    @ownerOnly
    @strFields(role = None, label = "", trove = "")
    @intFields(writeperm = None, remove = None)
    def editPermForm(self, auth, role, label, trove, writeperm, remove):
        roles = self.repServer.auth.getRoleList()
        labels = self.repServer.auth.getLabelList()
        troves = self.repServer.auth.getItemList()

        #remove = 0
        return self._write("permission", operation='Edit', role=role, label=label,
            trove=trove, roles=roles, labels=labels, troves=troves,
            writeperm=writeperm, remove=remove)

    @ownerOnly
    @strFields(role = None, label = "", trove = "",
               oldlabel = "", oldtrove = "",
               writeperm = "off", remove = "off")
    def editPerm(self, auth, role, label, trove, oldlabel, oldtrove,
                writeperm, remove):
        writeperm = (writeperm == "on")
        capped = (capped == "on")
        admin = (admin == "on")
        remove = (remove == "on")

        try:
            self.repServer.editAcl(auth, 0, role, oldtrove, oldlabel, trove,
               label, writeperm, capped, admin, canRemove = remove)
        except errors.PermissionAlreadyExists, e:
            return self._write("error", shortError="Duplicate Permission",
                error = "Permissions have already been set for %s, please go back and select a different User, Label or Trove." % str(e))

        self._redirect("userlist")

    def _calcSideBySide(self, diff):
        """
        Parse the results of a difflib.ndiff into a side-by-side comparision.
        """
        aligned = True

        # Contents of the left and right columns
        leftFile = []
        rightFile = []

        # Lines that differ between the two files
        diffedLines = []

        # Line numbers for both files
        leftLineNums = []
        rightLineNums = []
        leftLineCount = 1

        rightLineCount = 1

        for line in diff:
            key = line[0]
            if key == '-':
                if not aligned:
                    rightFile.append('')
                    rightLineNums.append('')
                leftFile.append(line[2:])
                diffedLines.append(len(leftFile) - 1)
                leftLineNums.append(leftLineCount)
                leftLineCount += 1
                aligned = False
            elif key == '+':
                if aligned:
                    leftFile.append('')
                    leftLineNums.append('')
                rightFile.append(line[2:])
                diffedLines.append(len(rightFile) - 1)
                rightLineNums.append(rightLineCount)
                rightLineCount += 1
                aligned = True
            elif key == ' ':
                if not aligned:
                    rightFile.append('')
                    rightLineNums.append('')
                leftFile.append(line[2:])
                rightFile.append(line[2:])
                leftLineNums.append(leftLineCount)
                leftLineCount += 1
                rightLineNums.append(rightLineCount)
                rightLineCount += 1
                aligned = True
            # Ignore lines starting with ?
        if not aligned:
            rightFile.append('')
            rightLineNums.append('')

        return dict(leftFile=leftFile, rightFile=rightFile, diffedLines=list(set(diffedLines)), leftLineNums=leftLineNums, rightLineNums=rightLineNums)

    
    @strFields(t=None, v=None, path=None, pathId=None, fileId=None)
    def diffShadow(self, t, v, path, pathId, fileId, auth):
        ver = versions.VersionFromString(v)
        if ver.hasParentVersion():
            pv = ver.parentVersion()
        else:
            pv = ''
            compBranch = ver.branch()
            troveVersions = self.repos.getTroveVersionsByBranch({t: {compBranch: [None]}})
            if troveVersions.has_key(t):
                sortedVersions = sorted(troveVersions[t].keys(), reverse=True)
            else:
                sortedVersions = []

            matchTrove = False
            for x in sortedVersions:
                if x == ver:
                    matchTrove = True
                if not matchTrove:
                    continue
                if x.isUnmodifiedShadow() and x.hasParentVersion():
                    pv = x.parentVersion()
                    break
            if not pv:
                return self._write("error", shortError="Trove has no parent",
                    error = "This trove has no parent version.")
        
        # Try to load the diff from cache first
        cacheFileName = fileId + v.replace('/', '_')
        try:
            fd = open(os.path.join(self.cfg.diffCacheDir, cacheFileName))
            res = []
            for line in fd:
                res.append(line)
            fd.close()
        except IOError:
            #Otherwise, calculate and cache it
            fId = sha1helper.sha1FromString(fileId)
            fc = self.repos.getFileContents([(fId, ver)])[0]
            newFile = fc.get().read()

            if not checkin.cfgRe.match(path):
                for char in newFile:
                    if char not in string.printable:
                        return self._write('shadow_diff', diffinfo=None,
                            newV=ver, oldV=pv, path=path, t=t, 
                            contents=["This file contains unprintable characters."], 
                            message= "%s contains unprintable characters and cannot be displayed." % path)

            files = self.repos.iterFilesInTrove(t, pv, deps.parseFlavor(''))
            oldFile = ''
            for pathId2, path2, fileId2, version2 in files:
                if path2 == path:
                    fc = self.repos.getFileContents([(fileId2, version2)])[0]
                    oldFile = fc.get().read()
                    break

            if not oldFile:
                return self._write('shadow_diff', diffinfo=None, newV=ver, oldV=pv, path=path, t=t, contents=newFile.splitlines(), message="%s was created on the current branch.  No version exists on the parent." % path)
            if oldFile == newFile:
                return self._write('shadow_diff', diffinfo=None, newV=ver, oldV=pv, path=path, t=t, contents=newFile.splitlines(), message="File contents are identical on both branches.")
            res = list(difflib.ndiff(oldFile.splitlines(), newFile.splitlines()))
            try:
                fd = open(os.path.join(self.cfg.diffCacheDir, cacheFileName), 'w')
                for line in res:
                    fd.write(line + '\n')
                fd.close()
            except IOError:
                # We can't create a cache file for some reason
                pass

        # Format the diff
        diffinfo = self._calcSideBySide(res)

        return self._write('shadow_diff', diffinfo=diffinfo, newV=ver, oldV=pv, path=path, t=t)



    # FIXME the dependency on conary.repository.netrepos.NetworkRepositoryServer
    # needs to be removed in favor of 
    # conary.repository.netclient.NetworkRepositoryClient
    #
    # repServer is a NetworkRepositoryServer instance and is used by 
    # most the the PGP and repository permissions methods
    def __init__(self, req, cfg, repServer = None):
        protocol = 'http'
        port = 80

        if repServer:
            self.repServer = repServer
            self.troveStore = self.repServer.troveStore
        if 'mint.web.templates.repos' in sys.modules:
            self.reposTemplatePath = os.path.dirname(sys.modules['mint.web.templates.repos'].__file__)

    def handle(self, context):
        self.__dict__.update(**context)

        path = self.req.uri[len(self.cfg.basePath):].split("/")
        if len(path) < 3:
            raise HttpNotFound
        self.cmd = path[2]
        try:
            if path[0] == "repos":
                self.project = self.client.getProjectByHostname(path[1])
                serverName = self.project.getLabel().split("@")[0]
            else:
                serverName = self.req.hostname
                self.project = self.client.getProjectByFQDN(serverName)
        except ItemNotFound:
            raise HttpNotFound

        self.serverNameList = [serverName]

        self.userLevel = self.project.getUserLevel(self.auth.userId)
        self.isOwner  = (self.userLevel == userlevels.OWNER) or self.auth.admin
        self.isWriter = (self.userLevel in userlevels.WRITERS) or self.auth.admin
        self.isRemoteRepository = self.project.external

        self.basePath += "repos/%s" % self.project.getHostname()
        self.basePath = normPath(self.basePath)

        return self._handle

    def _handle(self, *args, **kwargs):
        """Handle either an HTTP POST or GET command."""

        if self.auth.admin:
            # if we are admin, we have the right to touch any repo, but that
            # particular repo might not know our credentials (not a project
            # member)... so use the auth user.
            saveToken = self.authToken
            self.authToken = (self.cfg.authUser, self.cfg.authPass, [])
        else:
            self.authToken = (self.authToken[0], self.authToken[1], [])

        localMirror = self.client.isLocalMirror(self.project.id)
        if self.project.external and not localMirror:
            overrideAuth = False
        else:
            # try as a specified user, if fails, fall back to anonymous
            overrideAuth = True
            if not self.repServer.auth.check((self.authToken[0], self.authToken[1], [])):
                self.authToken = ('anonymous', 'anonymous', [])

        cfg = self.project.getConaryConfig(overrideAuth = overrideAuth,
                                           newUser = self.authToken[0],
                                           newPass = self.authToken[1])
        conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
        if os.path.exists(conarycfgFile):
            cfg.read(conarycfgFile)
        cfg = helperfuncs.configureClientProxies(cfg,
                self.cfg.useInternalConaryProxy, self.cfg.proxy,
                self.client.getProxies()[0])

        if 'repServer' not in self.__dict__:
            self.repos = conaryclient.ConaryClient(cfg).getRepos()
        else:
            self.repos = ShimNetClient(self.repServer, 'http', 80,
                                       self.authToken, cfg.repositoryMap,
                                       cfg.user,
                                       conaryProxies=conarycfg.getProxyFromConfig(cfg))

        try:
            method = self.__getattribute__(self.cmd)
        except AttributeError:
            raise HttpNotFound

        d = self.fields
        d['auth'] = self.authToken

        self.setupView()

        try:
            d['auth'] = self.authToken
            try:
                output = method(**d)
            except errors.OpenError, e:
                self._addErrors(str(e))
                self._redirectHttp('project/%s/' % (self.project.hostname,))
            except conaryerrors.InvalidRegex, e:
                return self._write("error",
                                   shortError = "Invalid Regular Expression",
                                   error = str(e))
            except PermissionDenied:
                raise HttpForbidden
        finally:
            # carefully restore old credentials so that this code can work
            # outside of mod-python environments.
            if self.auth.admin:
                self.authToken = saveToken
            # roll back any hanging transaction
            if self.cfg.debugMode:
                if self.__dict__.has_key('repServer'):
                    self.repServer.db.rollback()
        return output

    def _write(self, templateName, **values):
        return WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)
