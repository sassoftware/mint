#
# Copyright (c) 2004-2005 Specifix, Inc.
# All rights reserved.

import os

# conary
from deps import deps
import versions
import cscmd

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
    #if repr in _PkgId._hashcache:
    #    return _PkgId.hashcache[repr]
    #else:
    return _PkgId(name, version, flavor, repr=repr)

def SourceId(name, version, flavor):
    repr = makePkgIdRepr(name, version, flavor)
    #if repr in _PkgId._hashcache:
    #    return _PkgId.hashcache[repr]
    #else:
    return _SourceId(name, version, flavor, repr=repr)

def TroveId(name, version, flavor, trove=None):
    repr = makePkgIdRepr(name, version, flavor)
    #if repr in _PkgId._hashcache:
    #    return _PkgId.hashcache[repr]
    #else:
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

    def getSourceBranch(self):
        return self.getVersion().getSourceVersion().branch()

    def getBinaryVersion(self):
        return self.getVersion().getBinaryVersion().branch()

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
        branchV = self.getVersion().createBranch(newLabel, withVerRel = 1)
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
        return self.__version.trailingRevision().getSourceCount()

    def getBuildCount(self):
        return self.__version.trailingRevision().buildCount

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
            if self._desVersionStr == versionStr:
                return
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
            if self._troveId.getLabel() == branch:
                better = self.getBetterMatch(
                                        self._troveId.unbranch(branch), 
                                                 troveId.unbranch(branch))
                if better != self._troveId.unbranch(branch):
                    self._troveId = troveId
            else:
                better = self.getBetterMatch(self._troveId,
                                                 troveId.unbranch(branch))
                if better != self._troveId:
                    self._troveId = troveId

    def getBetterMatch(self, t1, t2):
        if t1 is None:
            return t2
        if t2 is None:
            return t1
        if t1.getVersion() == t2.getVersion():
            # versions match exactly, check flavors
            if t1.getFlavor() != t2.getFlavor():
                raise RuntimeError, ("addTrove is not specific enough -- two"
                                     " packages, %s and %s match for sourceId"
                                     "  %s "  % (t1, t2, self))
            return t1
        elif t1.builtFrom(self):
            if t2.builtFrom(self):
                if t1.getVersion().isAfter(t2.getVersion()):
                    return t1
                elif t2.getVersion().isAfter(t1.getVersion()):
                    return t2
                else:
                    # should not get here -- timestamps are the same
                    # but versions are different?
                    assert(False)
            else:
                return t1
        elif t2.builtFrom(self):
            return t2
        else:
            # neither package is an exact match, so they should be
            # inexact matches at least
            assert(t1.builtFrom(self, True) and t2.builtFrom(self, True))
            if t1.getVersion().isAfter(t2.getVersion()):
                return t1
            elif t2.getVersion().isAfter(t1.getVersion()):
                return t2
            # should not get here -- timestamps are the same
            # but versions are different?
            assert(False)

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
            v = self.getSourceBranch()
            pv = sourceId.getSourceBranch()
            if not v == pv:
                return False

            # if a specific version was requested with addTrove,
            # use that info.
            vs = sourceId.getDesiredVersionStr()
            if vs: 
                # if a version/release was used, make sure it matches
                # the troveId's version/release
                try:
                    tv = versions.Revision(vs)
                except versions.ParseError:
                    tv = None
                if tv:
                    if tv.buildCount:
                        if self.getVersion().getTrailingVersion() != tv:
                            return False
                    else:
                        stv = self.getVersion().trailingRevision().copy()
                        stv.buildCount = None
                        if stv != tv:
                            return False
                else:
                    # if a full version was used, it should match exactly
                    try:
                        v = versions.VersionFromString(vs)
                    except AttributeError:
                        v = None
                    if v and not isinstance(v, versions.Branch):
                        pv = self.getVersion().getSourceVersion()
                        pv.trailingRevision().buildCount = None
                        if v != pv:
                            return False
                # all other cases should have been handled by the 
                # earlier branch validity check.
        else:
            v = sourceId.getVersion().getSourceVersion()
            pv = self.getVersion().getSourceVersion()
            pv.trailingRevision().buildCount = None
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
        if troveId.getSourceBranch() != \
                                        self.getSourceBranch():
            return False
        if troveId.getVersion().trailingRevision().getVersion() != \
                            self.getVersion().trailingRevision().getVersion():
            return False
        if troveId.getSourceCount() != self.getSourceCount():
            return False
        # build count doesn't matter

        return self.flavorsMatch(troveId)

    def flavorsMatch(self, packageId):
        """ return True if if our flavor does not directly contradict
            the flavors listed in the other pkgId """
        myFlavor = self.getFlavor()
        pkgFlavor = packageId.getFlavor()
        if None in (myFlavor, pkgFlavor):
            return True
        # this should cover Arch 
        if (deps.DEP_CLASS_IS in myFlavor.getDepClasses() and 
            deps.DEP_CLASS_IS in pkgFlavor.getDepClasses()):
            myInsSet = deps.DependencySet()
            pkgInsSet = deps.DependencySet()
            myInsDep = [x for x in myFlavor.members[deps.DEP_CLASS_IS].getDeps()]
            pkgInsDep = [ x for x in pkgFlavor.members[deps.DEP_CLASS_IS].getDeps()]
            if len(myInsDep) != len(pkgInsDep):
                  return False
            for insDep in myInsDep:
                myInsSet.addDep(deps.InstructionSetDependency, insDep)
            for insDep in pkgInsDep:
                pkgInsSet.addDep(deps.InstructionSetDependency, insDep)
            if not myInsSet.satisfies(pkgInsSet):
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
        return self._trove

    def createChangeSet(self, path, repos, cfg, component=None):
        """ extract the trove from the repository to the given location """
        version = self.getVersion()
        flavor = self.getFlavor()
        if component is None: 
            component = self.getName()
        if component.startswith('group-'):
            recurse = False
        else:
            recurse = True

        cscmd.ChangeSetCommand(repos, cfg,
           ["%s=%s[%s]" % (component,
                           version.asString(),
                           deps.formatFlavor(flavor))
           ],
           path, recurse = recurse
        )
        return ChangeSetId(self.getName(), version, flavor, path)

class _ChangeSetId(_TroveId):
    
    def __init__(self, name, version, flavor, path, repr=repr):
        _TroveId.__init__(self, name, version, flavor, repr=repr)
        self._path = path

    def isChangeSet(self):
        return True

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
