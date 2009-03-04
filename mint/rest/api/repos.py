from conary.conaryclient import cmdline
from conary import trove
from conary import versions

from restlib import response

from mint.rest.api import base
from mint.rest.api import models

class BaseReposController(base.BaseController):
    def getRepos(self, hostname):
        return self.db.productMgr.reposMgr.getRepositoryClient(hostname)

class RepositoryItemsController(BaseReposController):
    modelName = 'troveString'
    modelRegex = '.*\[.*\]'

    urls = {'images' : dict(GET='getImages')}

    def index(self, request, hostname):
        return response.Response('index')

    def _checkTrove(self, hostname, troveString):
        name, version, flavor = cmdline.parseTroveSpec(troveString)
        try:
            version = versions.VersionFromString(version)
        except Exception, e:
            raise NotImplementedError
        repos = self.getRepos(hostname)
        if not repos.hasTrove(name, version, flavor):
            raise NotImplementedError
        trv = models.Trove(hostname=hostname, 
                            name=name, version=version, flavor=flavor)
        return repos, trv

    
    def get(self, request, hostname, troveString):
        repos, trv = self._checkTrove(hostname, troveString)
        return trv

    def getImages(self, request, hostname, troveString):
        repos, trv = self._checkTrove(hostname, troveString)
        return self.db.listImagesForTrove(hostname, 
                                          trv.name, trv.version, trv.flavor)
    
class RepositoryController(BaseReposController):
    urls = {'search' : dict(GET='search'),
            'items' :  RepositoryItemsController}

    def index(self, request, hostname):
        return response.Response('Index.\n')
        
    def search(self, request, hostname):
        label = request.GET.get('label', None)
        searchType = request.GET.get('type', None)
        checkFnDict  = {'group'  : trove.troveIsGroup,
                        'source' : trove.troveIsSourceComponent,
                        'fileset' : trove.troveIsFileSet,
                        'package' : lambda x: (trove.troveIsCollection(x) 
                                               and not trove.troveIsGroup(x)),
                        None: None}
        if searchType not in checkFnDict:
            raise InvalidSearchType(searchType)
        checkFn = checkFnDict[searchType]
        troveDict = self.getRepos(hostname).getTroveVersionsByLabel(
                                {None : {versions.Label(label) : None}})
        troveList = []
        for name, versionDict in troveDict.iteritems():
            if checkFn and not checkFn(name):
                continue

            for version, flavorList in versionDict.iteritems():
                for flavor in flavorList:
                    trv = models.Trove(hostname=hostname, name=name, 
                                       version=version, flavor=flavor)
                    troveList.append(trv)
        return models.TroveList(troveList)
