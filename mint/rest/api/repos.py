#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
import mimetypes
from StringIO import StringIO

from conary import trove
from conary import versions
from conary.conaryclient import cmdline
from conary.lib import sha1helper

from smartform import descriptor
from smartform import descriptor_errors

from restlib import response

from mint.rest import errors
from mint.rest.api import base
from mint.rest.api import models

class BaseReposController(base.BaseController):
    def getRepos(self, hostname):
        return self.db.productMgr.reposMgr.getRepositoryClientForProduct(
                                                                    hostname)

    def _getTuple(self, troveString):
        try:
            name, version, flavor = cmdline.parseTroveSpec(troveString)
        except cmdline.TroveSpecError, e:
            raise errors.InvalidTroveSpec("Error parsing trove %s: %s" %
                (troveString, str(e)))

        try:
            version = versions.VersionFromString(version)
        except versions.ParseError, e:
            raise errors.InvalidVersion("Error parsing version %s: %s" %
                (version, str(e)))

        return name, version, flavor

    def _checkTrove(self, hostname, troveString):
        name, version, flavor = self._getTuple(troveString)
        repos = self.getRepos(hostname)
        if not repos.hasTrove(name, version, flavor):
            raise errors.TroveNotFound(troveString)
        trv = models.Trove(hostname=hostname, 
                            name=name, version=version, flavor=flavor)
        return repos, trv

class RepositoryFilesController(BaseReposController):
    modelName = 'pathHash'
    
    urls = {'contents' : 'contents' }

    def _getFileInfo(self, hostname, troveString, pathHash):
        repos = self.getRepos(hostname)
        name, version, flavor = self._getTuple(troveString)
        try:
            trv = repos.getTrove(name, version, flavor, withFiles=True)
        except errors.TroveNotFound:
            raise NotImplementedError
        pathHash = sha1helper.md5FromString(pathHash)
        for pathId, path, fileId, fileVersion in trv.iterFileList():
            if pathHash == sha1helper.md5String(path):
                break
        else:
            raise NotImplementedError
        fileObj = repos.getFileVersion(pathId, fileId, fileVersion)
        return repos, path, fileVersion, fileObj

    def contents(self, request, hostname, troveString, pathHash):
        repos, path, ver, fileObj = self._getFileInfo(hostname, troveString, 
                                                 pathHash)

        headers = {}
        contents = repos.getFileContents([(fileObj.fileId(), 
                                           ver)])[0]
        if fileObj.flags.isConfig():
            content_type = "text/plain"
        else:
            typeGuess = mimetypes.guess_type(path)

            headers["Content-Disposition"] = "attachment; filename=%s;" % path
            if typeGuess[0]:
                content_type = typeGuess[0]
            else:
                content_type = "application/octet-stream"
        headers["Content-Length"] = fileObj.sizeString()
        return response.Response(contents.get().read(), 
                                 content_type=content_type,
                                 headers=headers)


    def get(self, request, hostname, troveString, pathHash):
        repos, path, ver, fileObj = self._getFileInfo(hostname, troveString, 
                                                      pathHash)
        flags = fileObj.flags
        return models.TroveFile(hostname=hostname,
                        trove=troveString,
                        pathId=sha1helper.md5ToString(fileObj.pathId()), 
                        pathHash=pathHash, 
                        path=path, 
                        fileVersion=ver, 
                        fileId=sha1helper.sha1ToString(fileObj.fileId()), 
                        tags=','.join(fileObj.tags()),
                        isConfig=flags.isConfig(),
                        isInitialContents=flags.isInitialContents(),
                        isSource=flags.isSource(),
                        isAutoSource=flags.isAutoSource(),
                        isTransient=flags.isTransient(),
                        size=fileObj.contents.size(),
                        sha1=sha1helper.sha1ToString(fileObj.contents.sha1()),
                        permissions=fileObj.inode.permsString(),
                        mtime=fileObj.inode.mtime(),
                        owner=fileObj.inode.owner(),
                        group=fileObj.inode.group(),
                        provides=fileObj.provides(),
                        requires=fileObj.requires())


class RepositoryItemsController(BaseReposController):
    modelName = 'troveString'
    modelRegex = '.*\[.*\]'

    urls = {'images' : dict(GET='getImages'),
            'files'  : RepositoryFilesController }


    def get(self, request, hostname, troveString):
        repos = self.getRepos(hostname)
        name, version, flavor = self._getTuple(troveString)
        trv = repos.getTrove(name, version, flavor, withFiles=True)
        fileList = []
        for pathId, path, fileId, fileVersion in trv.iterFileList():
            pathHash = sha1helper.md5String(path)
            fileList.append(models.TroveFile(
                        hostname=hostname,
                        pathId=sha1helper.md5ToString(pathId), 
                        pathHash=sha1helper.md5ToString(pathHash), 
                        path=path, 
                        fileId=sha1helper.sha1ToString(fileId), 
                        trove=troveString,
                        fileVersion=fileVersion))
        troveModel = models.Trove(hostname=hostname, 
                                  name=name, version=version, flavor=flavor,
                                  files=fileList)
        return troveModel

    def getImages(self, request, hostname, troveString):
        #repos, trv = self._checkTrove(hostname, troveString)
        name, version, flavor = self._getTuple(troveString)
        return self.db.listImagesForTrove(hostname, 
                name, version, flavor)

    
class RepositoryController(BaseReposController):
    urls = {'search'   : dict(GET='search'),
            'items'    : RepositoryItemsController,
            'files' : RepositoryFilesController,
           }

    def search(self, request, hostname):
        name = request.GET.get('name', None)
        label = request.GET.get('label', None)
        latest = request.GET.get('latest', False)
        searchType = request.GET.get('type', None)
        checkFnDict  = {'group'  : trove.troveIsGroup,
                        'source' : trove.troveIsSourceComponent,
                        'fileset' : trove.troveIsFileSet,
                        'package' : lambda x: (trove.troveIsCollection(x) 
                                               and not trove.troveIsGroup(x)),
                        None: None}
        if searchType not in checkFnDict:
            # XXX We probably want to use exceptions instead of direct maps to
            # an error code
            #raise errors.InvalidSearchType(searchType)
            return response.Response('Invalid search type %s' % searchType,
                                     status = 400)

        checkFn = checkFnDict[searchType]
        repos = self.getRepos(hostname)
        if latest:
            queryFn = repos.getTroveLatestByLabel
        else:
            queryFn = repos.getTroveVersionsByLabel

        if not label:
            return response.Response('Label not specified', status = 400)

        try:
            label = versions.Label(label)
        except versions.ParseError, e:
            return response.Response(
                'Error parsing label %s: %s' % (label, e), status = 400)

        troveDict = queryFn({name : {label : None}})
        troveList = []
        for name, versionDict in troveDict.iteritems():
            if checkFn and not checkFn(name):
                continue

            for version, flavorList in versionDict.iteritems():
                timeStamp = version.timeStamps()[-1]
                trailingVersion = version.trailingRevision().asString()
                label = version.trailingLabel()
                for flavor in flavorList:
                    imageCount = len(self.db.listImagesForTrove(hostname,
                        name, version, flavor).images)
                    trv = models.Trove(hostname=hostname, name=name, 
                               version=version, flavor=flavor,
                               timeStamp=timeStamp,
                               trailingVersion=trailingVersion,
                               label=label, imageCount=imageCount)
                    # This may be a group, check it for config descriptors
                    if name.startswith('group-'):
                        desc = self._getConfigDescriptor(name, version, flavor)
                        trv.configuration_descriptor = desc
                    troveList.append(trv)
        troveList = sorted(troveList, key = lambda x: x.timeStamp)
        return models.TroveList(troveList)

    ###
    # The following two functions were mostly copied from
    # django_rest/rbuilder/inventory/managers/versionmgr.py.
    # If you change them make sure to update in both places.
    ###

    def _getConfigDescriptor(self, name, version, flavor):
        desc = descriptor.ConfigurationDescriptor()
        desc.setDisplayName('Configuration Descriptor')
        desc.addDescription('Configuration Descriptor')

        newFields = self._getTroveConfigDescriptor(name, version, flavor)

        if not newFields:
            return ''

        fields = desc.getDataFields()
        fields.extend(newFields)

        out = StringIO()
        desc.serialize(out, validate=False)
        out.seek(0)

        return out.read()

    def _getTroveConfigDescriptor(self, name, version, flavor):
        repos = self.getRepos(version.getHost())

        trvList = repos.getTroves([(name, version, flavor)])

        referencedByDefault = []
        for trv in trvList:
            referencedByDefault += [ nvf for nvf, byDefault, strongRef in
                trv.iterTroveListInfo() if byDefault ]

        # Get properties sorted by package name.
        properties = repos.getTroveInfo(trove._TROVEINFO_TAG_PROPERTIES,
            sorted(referencedByDefault, cmp=lambda x, y: cmp(x[0], y[0])))

        configFields = []
        for propSet in properties:
            if propSet is None:
                continue
            for property in propSet.iter():
                xml = property.definition()
                desc = descriptor.BaseDescriptor()

                try:
                    desc.parseStream(StringIO(xml))

                # Ignore any descriptors that don't parse.
                except descriptor_errors.Error:
                    continue

                configFields.extend(desc.getDataFields())

        return configFields
