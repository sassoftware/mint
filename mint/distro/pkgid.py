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

def TroveId(name, version, flavor, trove=None):
    repr = makePkgIdRepr(name, version, flavor)
    if repr in _PkgId._hashcache:
        return _PkgId.hashcache[repr]
    else:
        return _TroveId(name, version, flavor, repr=repr, trove=trove)

def TroveIdFromTrove(theTrove):
    return TroveId(theTrove.getName(), theTrove.getVersion(), 
                            theTrove.getFlavor(), trove=theTrove)



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

    def getFlavor(self):
        return self.__flavor

    def getTuple(self):
	return (self.__name, self.__version, self.__flavor)

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

    def unbranch(self, label):
        """ Create a SourceId or TroveId for this package 
            after removing the last branch from the current id.
        """
        if self.getBuildCount() is None:
            class_ = SourceId
        else:
            class_ = TroveId

        v = self.getVersion()
        assert(v.versions[-2] == label)
        vlist = v.versions[:-3] + [ v.versions[-1] ]
        unbranchedV = versions.Version(vlist)
        unbranchedId  = class_(self.getName(),
                               unbranchedV,
                               self.getFlavor())
        return unbranchedId

    def branch(self, newLabel):
        """ Create a SourceId or TroveId for this package after it 
            has been branched onto newLabel
        """
        branchV = self.getVersion().fork(newLabel, sameVerRel = 1)
        if self.getBuildCount() is None:
            class_ = SourceId
        else:
            class_ = TroveId
        branchedId  = class_(self.getName(),
                              branchV,
                              self.getFlavor())
        return branchedId

    def getBranch(self):
        return self.__version.branch()

    def getLabel(self):
        return self.__version.branch().label()

    def getHost(self):
        return self.__version.branch().label().getHost()

    def getSourceCount(self):
        return self.__version.trailingVersion().getRelease()

    def getBuildCount(self):
        return self.__version.trailingVersion().buildCount

    def getVersionStr(self):
        return self.__version.asString()

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
        """ when sorting, sort by trove name, then from earliest version to
            latest, then alphabetically by flavor
        """
        if self == other:
            return 0
        val = cmp(self.getName(), other.getName())
        if val != 0:
            return val
        v1 = self.getVersion()
        v2 = other.getVersion()
        if v2.isAfter(v1):
            return -1
        if v1 == v2:
            return cmp(str(self.getFlavor()), str(other.getFlavor()))
        return 1

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
        state['_PkgId__version'] = self.getVersion().asString()
        state['_stats'] = None
        return state
        
    def __setstate__(self, state):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        self.__dict__.update(state)
        self.__version = versions.VersionFromString(state['_PkgId__version'])

class _SourceId(_PkgId):
    def __init__(self, name, version, flavor, repr=repr):
        _PkgId.__init__(self, name, version, flavor, repr=repr)
        self._recipeClass = None
        self._usedFlags = {}
        self._troveId = None
        self._desVersionStr = None

    def setLocalFlags(self, localFlags):
        """store any local flags created by this package when loaded"""
        self._localFlags = localFlags

    def getLocalFlags(self):
        """get any local flags created by this package when loaded"""
        return self._localFlags
    
    def setUsedFlags(self, usedFlags):
        """store the flags that were used when this package was loaded"""
        self._usedFlags = usedFlags

    def setDesiredVersionStr(self, versionStr):
        """set the version string requested in the addTrove command that
            resulted in this SourceId """
        if self._desVersionStr is not None:
            raise RuntimeError, "Cannot set desired version str twice"
        self._desVersionStr = versionStr

    def getDesiredVersionStr(self):
        """get the version string requested in the addTrove command that
            resulted in this SourceId """
        return self._desVersionStr


    def getUsedFlags(self):
        """retrieve the flags that were used when this package was loaded"""
        return self._usedFlags

    def setRecipeClass(self, recipeClass):
        """ store the recipeClass associated with this sourceId """
        self._recipeClass = recipeClass

    def getRecipeClass(self):
        """ retrieve the recipeClass associated with this sourceId """
        return self._recipeClass 

    def removeTroveId(self):
        self._troveId = None
    
    def addTroveId(self, troveId, allowVersionMismatch=False, force=False):
        """ note that the given trove could have been derived from 
            a source trove with this source id 
        """
        if not troveId.builtFrom(self, 
                                   allowVersionMismatch=allowVersionMismatch):
            raise RuntimeError, ("Error: %s cannot be built from %s!" % 
                                                               (troveId, self))

        if self._troveId is None or force:
            self._troveId = troveId
        else:
            self._troveId = self.getBetterMatch(self._troveId, troveId)

    def addBranchedTroveId(self, troveId, branch, allowVersionMismatch=False,
                                                  force=False):
        """ note that the given trove could have been derived from 
            a source trove with this source id 
        """
        if not troveId.unbranch(branch).builtFrom(self, 
                                    allowVersionMismatch=allowVersionMismatch):
            raise RuntimeError, ("Error: %s cannot be built from %s!" % 
                                                               (troveId, self))
        if self._troveId is None or force:
            self._troveId = troveId
        else:
            self._troveId = self.getBetterMatch(self._troveId.unbranch(branch), 
                                                 troveId.unbranch(branch))

    def getBetterMatch(self, t1, t2):
        if t1 is None:
            return t2
        if t2 is None:
            return t1
        if t1.builtFrom(self):
            if t2.builtFrom(self):
                if t1.getVersion().isAfter(t2.getVersion()):
                    return t1
                elif t2.getVersion().isAfter(t2.getVersion()):
                    return t2
            else:
                return t1
        elif t2.builtFrom(self):
            return t2
        else:
            # these packages should at least match given a mismatched
            # version
            assert(t1.builtFrom(self, True) and t2.builtFrom(self, True))
            if t1.getVersion().isAfter(t2.getVersion()):
                return t1
            elif t2.getVersion().isAfter(t1.getVersion()):
                return t2
        # versions match exactly, check flavors
        if (self.countFlavorMatches(t1) < self.countFlavorMatches(t2)):
            return t2
        else:
            return t1


    def countFlavorMatches(self, packageId):
        """ returns # of matches in flavor between the two  """
        count = 1
        if packageId.getFlavor() is None or self.getFlavor() is None:
            return 0
        # this should cover Arch 
        if not self.getFlavor().satisfies(packageId.getFlavor()):
            return 0
        builtFlags = flavorutil.getFlavorUseFlags(packageId.getFlavor())
        srcFlags = flavorutil.getFlavorUseFlags(self.getFlavor())
        builtUse = builtFlags['Use']
        srcUse = srcFlags['Use']
        if self.getUsedFlags():
            srcUse.update(self.getUsedFlags()['Use'])
        
        for flag, value in srcUse.iteritems():
            if flag in builtUse:
                if builtUse[flag] != value:
                    return 0
                else:
                    count += 1
        try:
            srcLocal = srcFlags['Flags'][self.getName()]
            if self.getUsedFlags():
                usedFlags = self.getUsedFlags()
                for key in usedFlags:
                    if key in srcUse:
                        srcUse[key].update(usedFlags[key])
                    else:
                        srcUse[key] = usedFlags[key]
            builtLocal = builtFlags['Flags'][self.getName()]
        except KeyError:
            # if either of these doesn't mention any local flags,
            # then it's impossible for them to have a contradiction
            # between them
            return True
        for flag, value in srcLocal.iteritems():
            if flag in builtLocal:
                if builtLocal[flag] != value:
                    return 0
                count += 1
        return count


    def getTroveId(self):
        """ Return trove that was built from this source trove """
        return self._troveId
    
    def __getstate__(self):
        """ Pickling function.  Returns a dict containing this 
            packageId's critical information.  
        """
        state = _PkgId.__getstate__(self)
        if '_recipeClass' in state:
            del state['_recipeClass']
        if '_localFlags' in state:
            del state['_localFlags']
        if '_usedFlags' in state:
            del state['_usedFlags']
        return state


class _TroveId(_PkgId):
    def __init__(self, name, version, flavor, repr=repr, trove=None):
        _PkgId.__init__(self, name, version, flavor, repr=repr)
        self._trove = trove
        
    def builtFrom(self, sourceId, allowVersionMismatch=False):
        """ returns True if cooking sourceId could result in the
            given package -- if allowVersionMismatch, match only the 
            branch, unless a specific version release was asked for
            """
        if sourceId.getName() != self.getName():
            return False
        if allowVersionMismatch:    
            # allow the troveId to be from a different version than that
            # of the sourceId -- within limits.
            # make sure the branches match
            # XXX this does not work with the update repo, where all 
            # versions have stored with them the version/release of the 
            # source they were branched from
            v = self.getBranch().getSourceBranch()
            pv = sourceId.getBranch().getSourceBranch()
            if not v == pv:
                return False

            # if a specific version was requested with addTrove,
            # use that info.
            vs = sourceId.getDesiredVersionStr()
            if vs: 
                # if a version/release was used, make sure it matches
                # the troveId's version/release
                try:
                    tv = versions.VersionRelease(vs)
                except ParseError:
                    tv = None
                if tv:
                    if tv.buildCount:
                        if self.getVersion().getTrailingVersion() != tv:
                            return False
                    else:
                        stv = self.getVersion().trailingVersion().copy()
                        stv.buildCount = None
                        if stv != tv:
                            return False
                else:
                    # if a full version was used, it should match exactly
                    try:
                        v = versions.VersionFromString(vs)
                    except AttributeError:
                        v = None
                    if v:
                        pv = self.getVersion().getSourceBranch()
                        pv.trailingVersion().buildCount = None
                        if v != pv:
                            return False
                # all other cases should have been handled by the 
                # earlier branch validity check.
        else:
            v = sourceId.getVersion().getSourceBranch()
            pv = self.getVersion().getSourceBranch()
            pv.trailingVersion().buildCount = None
            if v != pv:
                return False
        if self.flavorsMatch(sourceId):
            return True
        return False

    def sameSource(self, troveId):
        """ returns True if the two packages could have come from the same
            sourceId with the same flags """
        if troveId.getName() != self.getName():
            return False
        if troveId.getBranch().getSourceBranch() != \
                                        self.getBranch().getSourceBranch():
            return False
        if troveId.getSourceCount() != self.getSourceCount():
            return False
        # build count doesn't matter

        return self.flavorsMatch(troveId)

    def flavorsMatch(self, packageId):
        """ return True if if our flavor does not directly contradict
            the flavors listed in the other pkgId """
        if packageId.getFlavor() is None:
            return True
        # this should cover Arch 
        if not self.getFlavor().satisfies(packageId.getFlavor()):
            return False
        builtFlags = flavorutil.getFlavorUseFlags(self.getFlavor())
        srcFlags = flavorutil.getFlavorUseFlags(packageId.getFlavor())
        builtUse = builtFlags['Use']
        srcUse = srcFlags['Use']
        
        # only return false if it actually negates the flag value
        # -- it's possible that although a flag is specified for the trove,
        # the flag is never used during the building of this trove
        for flag, value in srcUse.iteritems():
            if flag in builtUse and builtUse[flag] != value:
                return False
        try:
            srcLocal = srcFlags['Flags'][packageId.getName()]
            builtLocal = builtFlags['Flags'][packageId.getName()]
        except KeyError:
            # if either of these doesn't mention any local flags,
            # then it's impossible for them to have a contradiction
            # between them
            return True
        for flag, value in srcLocal.iteritems():
            if flag in builtLocal and builtLocal[flag] != value:
                return False
        return True

    
    def getTrove(self, troveLoc):
        if self._trove:
            return self._trove
        self._trove = troveLoc.getTrove(self.getName(), self.getVersion(), 
                                                         self.getFlavor())

    def createChangeSet(self, path, troveLoc):
        """ extract the trove from the repository to the given location """
        version = self.getVersion()
        flavor = self.getFlavor()
        troveLoc.createChangeSetFile(
            [(self.getName(), (None, flavor), (version, flavor), True)], path)
        return ChangeSetId(self.getName(), version, flavor, path)

class _ChangeSetId(_TroveId):
    
    def __init__(self, name, version, flavor, path, repr=repr):
        _TroveId.__init__(self, name, version, flavor, repr=repr)
        self._path = path

    def getPath(self):
        return self._path

    def rename(self, newPath):
        os.rename(self._path, newPath)
        self._path = newPath

    def createChangeSet(self, troveLoc):
        raise NotImplementedError

def getSortedLeavesAfterUnbranch(pkgIds, label):
    """ Returns a list of lists of pkgIds such that, after all
        of the ids in pkgId are reverted from being branched on label,
        each tuple represents the latest version on whatever branch
        it was on after reverting. 
        e.g. you branch /localhost@spx:linux/foo-1.0-1 => updatehost,
        and /localhost@spx:linux/foo-1.0-2 => updatehost
        and branch /localhost@spx:linux/foo-1.0-1/fooother/2 => updatehost,
        you would get packages
        /localhost@spx:linux/foo-1.0-1/updatehost/1
        /localhost@spx:linux/foo-1.0-1/updatehost/2
        /localhost@spx:linux/foo-1.0-1/fooother/2/updatehost/2.
        From this function, you should expect back
        [[/localhost@spx:linux/foo-1.0-1/updatehost/2], 
         [/localhost@spx:linux/foo-1.0-1/fooother/2/updatehost/2]].
        An interior list would contain more than one element if more than one
        pkgId has exactly the same source version, but different flavors.

        Note that even if you pass in troveIds, this function assumes that the
        sources were branched.
    """
    branched = {}
    troveIds = []
    for pkgId in pkgIds:
        unbranchedId = pkgId.unbranch(label)
        branched[unbranchedId] = pkgId
        troveIds.append(unbranchedId)

    # figure out the max values for each branch
    branchMaxes = {}
    for troveId in troveIds:
        branch = troveId.getBranch()
        if branch not in branchMaxes:
            branchMaxes[branch] = [ troveId ]
            continue

        # the current max for this branch
        branchMax = branchMaxes[branch][0]
        bsc = branchMax.getSourceCount()
        tsc = troveId.getSourceCount()
        if bsc < tsc:
            branchMaxes[branch] = [ troveId ]
        elif bsc == tsc:
            # they are the same source version, but have different
            # flavors
            branchMaxes[branch].append(troveId)
    results = []
    for unbranchedIds in branchMaxes.values():
        results.append([ branched[x] for x in unbranchedIds ])
    return results
