from deps import deps
import stats
import versions

def thawPackage(pkgStr):
    id =  _PkgId._hashcache.get(pkgStr, None)
    if id:
        return id
    else:
        (name, value, flavor) = pkgStr.split(',', 2)
    if flavor == '0':
        flavor = None
    else:
        flavor = deps.ThawDependency(flavor)
    version = versions.VersionFromString(value.replace('#', '/'))
    return PkgId(name, version, flavor, justName = True)

def PkgId(recipeClassOrStr, version, flavor, justName=False):
    if justName:
        name = recipeClassOrStr
        recipeClass = None
    else:
        recipeClass = recipeClassOrStr
        name = recipeClass.name
    versionStr = version.asString()
    if flavor:
        if isinstance(flavor, deps.DependencySet):
            flavorStr = flavor.freeze()
        else:
            flavorStr = flavor._freeze()
    else:
        flavorStr = '0'
    repr = ','.join([name, versionStr.replace('/','#'), flavorStr])
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _PkgId(name, version, flavor, recipeClass, versionStr, repr)




class _PkgId:
    _hashcache = {}
    def __init__(self, name, version, flavor, recipeClass, versionStr, repr):
        self.name = name
        self.version = version
        self.flavor = flavor
        self.recipeClass = recipeClass
        self.stats = stats.PackageStats(self)
        self.versionStr = versionStr
        self._repr = repr
        self.usedFlags = {}
        self.cspkgs = {}
        if recipeClass: 
            self._hashcache[self] = self

    def prettyStr(self):
        return "%s (%s) (%s)" % (self.name, self.version.asString(), self.flavor)

    def __cmp__(self, other):
        return cmp(self.name, other.name) 

    def __repr__(self):
        return self._repr

    def __str__(self):
        return self._repr

    def __eq__(self, other):
        if isinstance(other, _PkgId):
            return self._repr == other._repr
        return False

    def __add__(self, other):
        """ Treat like a string for adding """
        return self._repr + other

    def __radd__(self, other):
        """ Treat like a string for adding """
        return other + self._repr

    def __hash__(self):
        return hash(self._repr)
