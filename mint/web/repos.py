#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import base64
import difflib
import itertools
import os
import string
import sys
import traceback

from mimetypes import guess_type

from mod_python import apache

from urllib import quote, unquote

import simplejson


from mint import database
from mint import mint_error
from mint import userlevels
from mint import helperfuncs
from mint.session import SqlSession
from mint.web.templates import repos
from mint.web.fields import strFields, listFields, intFields
from mint.web.webhandler import WebHandler, normPath, HttpForbidden, HttpNotFound
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

class ConaryHandler(WebHandler):
    def _filterAuth(self, **kwargs):
        memberList = kwargs.get('memberList', [])
        if isinstance(memberList, str):
            memberList = [memberList]
        if self.cfg.authUser in memberList:
            return self._write("error", shortError="Invalid User Name",
                    error = "A user name you have selected is invalid.")
        if kwargs.get('userGroupName', None) == self.cfg.authUser:
            return self._write("error", shortError="Invalid Group Name",
                    error = "The group name you are attempting to edit is invalid.")
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
        admin = self.repServer.auth.check(self.authToken,admin=True)

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

    @strFields(key=None, owner="")
    def pgpChangeOwner(self, auth, owner, key):
        # The requiresAdmin decorator will not work with our authOveride
        # tuple, so check for admin here
        if not self.project:             
            raise database.ItemNotFound("project")
        if not self.auth.admin:
            raise mint_error.PermissionDenied

        if not owner or owner == '--Nobody--':
            owner = None
        self.repServer.changePGPKeyOwner(self.authToken, 0, owner, key)
        self._redirect('pgpAdminForm')

    @strFields(t = None, v = None, f = "")
    def files(self, t, v, f, auth):
        v = versions.ThawVersion(v)
        f = deps.ThawFlavor(f)
        parentTrove = self.repos.getTrove(t, v, f, withFiles = False)
        # non-source group troves only show contained troves
        if t.startswith('group-') and not t.endswith(':source'):
            troves = sorted(parentTrove.iterTroveList(strongRefs=True))
            return self._write("group_contents", troveName = t, troves = troves)
        fileIters = []
        # XXX: Needs to be optimized
        # the walkTroveSet() will request a changeset for every
        # trove in the chain.  then iterFilesInTrove() will
        # request it again just to retrieve the filelist.
        for trove in self.repos.walkTroveSet(parentTrove, withFiles = False):
            files = self.repos.iterFilesInTrove(
                trove.getName(),
                trove.getVersion(),
                trove.getFlavor(),
                withFiles = True,
                sortByPath = True)
            fileIters.append(files)
        fileIters = itertools.chain(*fileIters)

        deletedFiles = []
        if t.endswith(':source'):
            if parentTrove.version.v.hasParentVersion():
                parentIters = []
                tr = self.repos.getTrove(t, parentTrove.version.v.parentVersion(), f)
                files = self.repos.iterFilesInTrove(
                    tr.getName(),
                    tr.getVersion(),
                    tr.getFlavor(),
                    withFiles = True,
                sortByPath = True)
                parentIters = files
                
                fileIters = [x for x in fileIters]
                deletedFiles = [x for x in parentIters if x[1] not in [y[1] for y in fileIters]]
        return self._write("files",
            troveName = t,
            fileIters = fileIters, deletedFiles=deletedFiles)

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
        except database.ItemNotFound:
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
            verList=simplejson.dumps(labels), selectedLabel = simplejson.dumps(str(reqVer.trailingLabel())), parentType=parentType, lineage=simplejson.dumps(lineage))

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
    @strFields(userGroupName = None)
    def deleteGroup(self, auth, userGroupName):
        self.repServer.auth.deleteGroup(userGroupName)
        self._filterAuth(userGroupName=userGroupName) or self._redirect("userlist")

    @ownerOnly
    @strFields(userGroupName = "")
    def addPermForm(self, auth, userGroupName):
        groups = self.repServer.auth.getGroupList()
        labels = self.repServer.auth.getLabelList()
        troves = self.repServer.auth.getItemList()

        return self._write("permission", operation='Add', group=userGroupName, trove=None,
            label=None, groups=groups, labels=labels, troves=troves,
            writeperm=None, capped=None, admin=None, remove=None)

    @ownerOnly
    @strFields(group = None, label = "", trove = "",
               writeperm = "off", capped = "off", admin = "off", remove = "off")
    def addPerm(self, auth, group, label, trove,
                writeperm, capped, admin, remove):
        writeperm = (writeperm == "on")
        capped = (capped == "on")
        admin = (admin == "on")
        remove = (remove== "on")

        try:
            self.repServer.addAcl(self.authToken, 0, group, trove, label,
               writeperm, capped, admin, remove = remove)
        except errors.PermissionAlreadyExists, e:
            return self._write("error", shortError="Duplicate Permission",
                error = "Permissions have already been set for %s, please go back and select a different User, Label or Trove." % str(e))

        self._redirect("userlist")

    @ownerOnly
    def addGroupForm(self, auth):
        users = self.repServer.auth.userAuth.getUserList()
        return self._write("add_group", modify = False, userGroupName = None, users = users, members = [], canMirror = False)

    @ownerOnly
    @strFields(userGroupName = None)
    def manageGroupForm(self, auth, userGroupName):
        users = self.repServer.auth.userAuth.getUserList()
        members = set(self.repServer.auth.getGroupMembers(userGroupName))
        canMirror = self.repServer.auth.groupCanMirror(userGroupName)

        return self._filterAuth(auth=auth, userGroupName=userGroupName) or self._write("add_group", userGroupName = userGroupName, users = users, members = members, canMirror = canMirror, modify = True)

    @ownerOnly
    @strFields(userGroupName = None, newUserGroupName = None)
    @listFields(str, memberList = [])
    @intFields(canMirror = False)
    def manageGroup(self, auth, userGroupName, newUserGroupName, memberList,
                    canMirror):
        if userGroupName != newUserGroupName:
            try:
                self.repServer.auth.renameGroup(userGroupName, newUserGroupName)
            except errors.GroupAlreadyExists:
                return self._write("error", shortError="Invalid Group Name",
                    error = "The group name you have chosen is already in use.")

            userGroupName = newUserGroupName

        self.repServer.auth.updateGroupMembers(userGroupName, memberList)
        self.repServer.auth.setMirror(userGroupName, canMirror)

        self._filterAuth(memberList=memberList, userGruopName=userGroupName) or self._redirect("userlist")

    @ownerOnly
    @strFields(newUserGroupName = None)
    @listFields(str, memberList = [])
    @intFields(canMirror = False)
    def addGroup(self, auth, newUserGroupName, memberList, canMirror):
        try:
            self.repServer.auth.addGroup(newUserGroupName)
        except errors.GroupAlreadyExists:
            return self._write("error", shortError="Invalid Group Name",
                error = "The group name you have chosen is already in use.")

        self.repServer.auth.updateGroupMembers(newUserGroupName, memberList)
        self.repServer.auth.setMirror(newUserGroupName, canMirror)

        self._filterAuth(memberList=memberList) or self._redirect("userlist")

    @ownerOnly
    @strFields(group = None, label = None, item = None)
    def deletePerm(self, auth, group, label, item):
        # labelId and itemId are optional parameters so we can't
        # default them to None: the fields decorators treat that as
        # required, so we need to reset them to None here:
        if not label or label == "ALL":
            label = None
        if not item or item == "ALL":
            item = None

        self.repServer.auth.deleteAcl(group, label, item)
        self._redirect("userlist")

    @ownerOnly
    @strFields(group = None, label = "", trove = "")
    @intFields(writeperm = None, capped = None, admin = None, remove = None)
    def editPermForm(self, auth, group, label, trove, writeperm, capped, admin,
                     remove):
        groups = self.repServer.auth.getGroupList()
        labels = self.repServer.auth.getLabelList()
        troves = self.repServer.auth.getItemList()

        #remove = 0
        return self._write("permission", operation='Edit', group=group, label=label,
            trove=trove, groups=groups, labels=labels, troves=troves,
            writeperm=writeperm, capped=capped, admin=admin, remove=remove)

    @ownerOnly
    @strFields(group = None, label = "", trove = "",
               oldlabel = "", oldtrove = "",
               writeperm = "off", capped = "off", admin = "off", remove = "off")
    def editPerm(self, auth, group, label, trove, oldlabel, oldtrove,
                writeperm, capped, admin, remove):
        writeperm = (writeperm == "on")
        capped = (capped == "on")
        admin = (admin == "on")
        remove = (remove == "on")

        try:
            self.repServer.editAcl(auth, 0, group, oldtrove, oldlabel, trove,
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
        except database.ItemNotFound:
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

        localMirror = self.client.isLocalMirror(self.project.id)
        if self.project.external and not localMirror:
            overrideAuth = False
        else:
            # try as a specified user, if fails, fall back to anonymous
            overrideAuth = True
            if not self.repServer.auth.check((self.authToken[0], self.authToken[1], None, None)):
                self.authToken = ('anonymous', 'anonymous', None, None)

        cfg = self.project.getConaryConfig(overrideAuth = overrideAuth,
                                           newUser = self.authToken[0],
                                           newPass = self.authToken[1])
        conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
        if os.path.exists(conarycfgFile):
            cfg.read(conarycfgFile)

        self.authToken = (self.authToken[0], self.authToken[1], None, None)

        cfg = helperfuncs.configureClientProxies(cfg,
                self.cfg.useInternalConaryProxy, self.cfg.proxy)

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

        if self.auth.admin:
            # if we are admin, we have the right to touch any repo, but that
            # particular repo might not know our credentials (not a project
            # member)... so use the auth user.
            saveToken = self.authToken
            self.authToken = (self.cfg.authUser, self.cfg.authPass, None, None)
        try:
            d['auth'] = self.authToken
            try:
                output = method(**d)
            except errors.OpenError, e:
                self._addErrors(str(e))
                self._redirect("http://%s%sproject/%s/" % (self.cfg.projectSiteHost,
                    self.cfg.basePath, self.project.hostname))
            except conaryerrors.InvalidRegex, e:
                return self._write("error",
                                   shortError = "Invalid Regular Expression",
                                   error = str(e))
            except mint_error.PermissionDenied:
                raise HttpForbidden
        finally:
            # carefully restore old credentials so that this code can work
            # outside of mod-python environments.
            if self.auth.admin:
                self.authToken = saveToken
        return output

    def _write(self, templateName, **values):
        return WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)
