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
    return PkgId(name, version, flavor, justName = True)

def PkgId(name, version, flavor, justName=True):
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
    repr = ','.join([name, versionStr.replace('/','#'), flavorStr])

    # look to see if this package already exists in the cache
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _PkgId(name, version, flavor, None, versionStr, repr)

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
        self.csIds = {}
        # if there isn't a key for ourselves,
        # (and there shouldn't be, since we are here)
        if self not in self._hashcache:
            self._hashcache[self] = self


    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

    def getVersionStr(self):
        return self.versionStr

    def getFlavor(self):
        return self.flavor

    def getStats(self):
        return self.stats

    def prettyStr(self):
        """ print a slightly more readable form of the sourceId """
        return "%s (%s) (%s)" % (self.name, self.version.asString(), self.flavor)

    # XXX move to sourceId subclass
    def setUsedFlags(self, usedFlags):
        """store the flags that were used when this package was loaded"""
        self.usedFlags = usedFlags

    # XXX move to sourceId subclass
    def setRecipeClass(self, recipeClass):
        """ store the recipeClass associated with this sourceId """
        self.recipeClass = recipeClass

    # XXX move to sourceId subclass
    def addChangeSet(self, csId):
        """ note that the given changeset could have been derived from 
            a trouve with this source id 
        """
        self.csIds[csId] = True

    def getChangeSetIds(self):
        return self.csIds.keys()

    # XXX move the csId subclass __init__
    def setChangeSetFile(self, path):
        self.file = path

    # XXX move to csId subclass
    def builtFrom(self, sourceId):
        """ returns True if cooking sourceId could result in the
            given package """
        v = self.version.getSourceBranch()
        pv = sourceId.version.getSourceBranch()
        v.trailingVersion().buildCount = None
        # XXXXXXXXX big hack to deal with the fact that
        # icecream version numbers are out of whack
        if pv == v or sourceId.name == 'icecream':
            if self.flavorIsFrom(sourceId):
                return True
        return False

    # XXX move to changesetId subPackage
    def flavorIsFrom(self, sourceId):
        """ return True if if our flavor does not directly contradict
            the flavors listed in sourceId """
        if sourceId.flavor is None:
            return True
        # this should cover Arch 
        if not self.flavor.satisfies(sourceId.flavor):
            return False
        builtFlags = flavorutil.getFlavorUseFlags(self.flavor)
        srcFlags = flavorutil.getFlavorUseFlags(sourceId.flavor)
        builtUse = builtFlags['Use']
        srcUse = srcFlags['Use']
        
        # only return false if it actually negates the flag value
        # -- it's possible that although a flag is specified for the trove,
        # the flag is never used during the building of this trove
        for flag, value in srcUse.iteritems():
            if flag in builtUse and builtUse[flag] != value:
                return False
        try:
            srcLocal = srcFlags['Flags'][sourceId.name]
            builtLocal = builtFlags['Flags'][sourceId.name]
        except KeyError:
            # if either of these doesn't mention any local flags,
            # then it's impossible for them to have a contradiction
            # between them
            return True
        for flag, value in srcLocal.iteritems():
            if flag in builtLocal and builtLocal[flag] != value:
                return False
        return True

           
    def __cmp__(self, other):
        """ when sorting, sort by trove name """
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
        """ Treat like a string for adding (useful for adding '.ccs)"""
        return self._repr + other

    def __radd__(self, other):
        """ Treat like a string for adding (useful for adding .ccs)""" 
        return other + self._repr

    def __hash__(self):
        """ hash Ids on their repr value, which is unique """
        return hash(self._repr)

    def __getstate__(self):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        print "Getting %s's state" % self
        state = self.__dict__.copy()
        if 'recipeClass' in state:
            del state['recipeClass']
        if 'usedFlags' in state:
            del state['usedFlags']
        del state['version']
        if self.flavor:
            state['flavor'] = self.flavor.freeze()
        state['stats'] = None
        return state
        
    def __setstate__(self, state):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        self.__dict__.update(state)
        self.version = versions.VersionFromString(self.versionStr)
        if self.flavor is not None:
            self.flavor = deps.ThawDependency(self.flavor)
