import os

# conary
from deps import deps
import versions

#darby
import flavorutil
import stats

def thawPackage(pkgStr):
    """Create a packageId out of a str created by str(pkgId).  """
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
    return PkgId(name, version, flavor)

def PkgId(name, version, flavor):
    """Create a handy identifier out of the fields commonly used to 
       identify a package.  The identifier is guaranteed to be 
       unique for unique name, version, flavors, is hashable,
       has a unique string representation that works as a file 
       name, and has functions for comparing package identifiers.
       *** Note that sourceIds can have flavors, something not 
       commonly associated with source troves.  A source flavor 
       implies that this source will be loaded/cooked with the given
       flavor.
    """

    repr = makePkgIdRepr(name, version, flavor)
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _PkgId(name, version, flavor, repr=repr)

def SourceId(name, version, flavor):
    repr = makePkgIdRepr(name, version, flavor)
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _SourceId(name, version, flavor, repr=repr)

def TroveId(name, version, flavor):
    repr = makePkgIdRepr(name, version, flavor)
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _TroveId(name, version, flavor, repr=repr)


def ChangeSetId(name, version, flavor, file):
    repr = makePkgIdRepr(name, version, flavor)
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _ChangeSetId(name, version, flavor, file, repr=repr)


def makePkgIdRepr(name, version, flavor):
    versionStr = version.asString()
    # XXX not sure about why we have two different freezes here.
    if flavor:
        if isinstance(flavor, deps.DependencySet):
            flavorStr = flavor.freeze()
        else:
            flavorStr = flavor._freeze()
    else:
        flavorStr = '0'

    # the package's representation should be a valid filename
    return ','.join([name, versionStr.replace('/','#'), flavorStr])


class _PkgId:
    _hashcache = {}

    def __init__(self, name, version, flavor, repr):
        # XXX don't muck with these four variables!
        # They are used to hash PkgIds, and any change to them
        # will change the hash value of the object,
        # causing Bad Things to happen.  So don't do it.
        self.__name = name
        self.__version = version
        self.__flavor = flavor
        if not repr:
            repr = makePkgIdRepr(name, version, flavor)
        self.__repr = repr

        self._stats = stats.PackageStats(self)
        if self not in self._hashcache:
            self._hashcache[self] = self

    def getName(self):
        return self.__name

    def getVersion(self):
        return self.__version

    def setVersion(self, version):
        """ Sets the version of this packageID.  
            This is not smart.  It will cause problems if 
            this PkgId is used as a hash key anywhere, so be sure
            that it isn't before using this function. 
            Better to make a new copy with the new version,
            if feasible
        """
        # we will no longer match this old cache position
        del self._hashcache[self]
        self.__version = version
        self.__repr = makePkgIdRepr(self.getName(), self.getVersion(), 
                                    self.getFlavor())
        # now we match here
        self._hashcache[self] = self


    def getLabel(self):
        return self.__version.branch().label()

    def getVersionStr(self):
        return self.__version.asString()

    def getFlavor(self):
        return self.__flavor

    def getStats(self):
        return self._stats

    def setStats(self, stats):
        self._stats = stats

    def setBuildIndex(self, index):
        self._buildIndex = index

    def getBuildIndex(self):
        return self._buildIndex

    def prettyStr(self):
        """ print a slightly more readable form of the sourceId """
        return "%s (%s) (%s)" % (self.getName(), self.getVersionStr(), 
                                                            self.getFlavor())

    def __cmp__(self, other):
        """ when sorting, sort by trove name """
        return cmp(self.getName(), other.getName()) 

    def __repr__(self):
        return self.__repr

    def __str__(self):
        return self.__repr

    def __eq__(self, other):
        if isinstance(other, _PkgId):
            return self.__repr == other.__repr
        return False

    def __add__(self, other):
        """ Treat like a string for adding (useful for adding '.ccs)"""
        return self.__repr + other

    def __radd__(self, other):
        """ Treat like a string for adding (useful for adding .ccs)""" 
        return other + self.__repr

    def __hash__(self):
        """ hash Ids on their repr value, which is unique """
        return hash(self.__repr)

    def __getstate__(self):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        state = self.__dict__.copy()
        state['_version'] = self.getVersion().asString()
        state['_stats'] = None
        return state
        
    def __setstate__(self, state):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        self.__dict__.update(state)
        self._version = versions.VersionFromString(state['_version'])

class _SourceId(_PkgId):
    def __init__(self, name, version, flavor, repr=repr):
        _PkgId.__init__(self, name, version, flavor, repr=repr)
        self._recipeClass = None
        self._usedFlags = {}
        self._troveIds = {}

    def setUsedFlags(self, usedFlags):
        """store the flags that were used when this package was loaded"""
        self._usedFlags = usedFlags

    def getUsedFlags(self):
        """retrieve the flags that were used when this package was loaded"""
        return self._usedFlags

    def setRecipeClass(self, recipeClass):
        """ store the recipeClass associated with this sourceId """
        self._recipeClass = recipeClass

    def getRecipeClass(self):
        """ retrieve the recipeClass associated with this sourceId """
        return self._recipeClass 

    
    def addTroveId(self, troveId):
        """ note that the given trove could have been derived from 
            a source trove with this source id 
        """
        self._troveIds[troveId] = True

    def getTroveIds(self):
        """ Return troves that could have been built with this 
            source trove
        """
        return self._troveIds.keys()

    def __getstate__(self):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        state = _PkgId.__getstate__(self)
        if '_recipeClass' in state:
            del state['_recipeClass']
        if '_usedFlags' in state:
            del state['_usedFlags']
        return state


class _TroveId(_PkgId):
    def __init__(self, name, version, flavor, repr=repr):
        _PkgId.__init__(self, name, version, flavor, repr=repr)
        
    def builtFrom(self, sourceId):
        """ returns True if cooking sourceId could result in the
            given package """
        v = self.getVersion().getSourceBranch()
        pv = sourceId.getVersion().getSourceBranch()
        v.trailingVersion().buildCount = None
        # XXXXXXXXX big hack to deal with the fact that
        # icecream version numbers are out of whack
        if pv == v or sourceId.getName() == 'icecream':
            if self.flavorIsFrom(sourceId):
                return True
        return False

    # XXX move to changesetId subPackage
    def flavorIsFrom(self, sourceId):
        """ return True if if our flavor does not directly contradict
            the flavors listed in sourceId """
        if sourceId.getFlavor() is None:
            return True
        # this should cover Arch 
        if not self.getFlavor().satisfies(sourceId.getFlavor()):
            return False
        builtFlags = flavorutil.getFlavorUseFlags(self.getFlavor())
        srcFlags = flavorutil.getFlavorUseFlags(sourceId.getFlavor())
        builtUse = builtFlags['Use']
        srcUse = srcFlags['Use']
        
        # only return false if it actually negates the flag value
        # -- it's possible that although a flag is specified for the trove,
        # the flag is never used during the building of this trove
        for flag, value in srcUse.iteritems():
            if flag in builtUse and builtUse[flag] != value:
                return False
        try:
            srcLocal = srcFlags['Flags'][sourceId.getName()]
            builtLocal = builtFlags['Flags'][sourceId.getName()]
        except KeyError:
            # if either of these doesn't mention any local flags,
            # then it's impossible for them to have a contradiction
            # between them
            return True
        for flag, value in srcLocal.iteritems():
            if flag in builtLocal and builtLocal[flag] != value:
                return False
        return True


class _ChangeSetId(_TroveId):
    
    def __init__(self, name, version, flavor, path, repr=repr):
        _TroveId.__init__(self, name, version, flavor, repr=repr)
        self._path = path

    def getPath(self):
        return self._path

    def rename(self, newPath):
        os.rename(self._path, newPath)
        self._path = newPath


    
