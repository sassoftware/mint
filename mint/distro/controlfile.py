#
# Copyright (c) 2004-2005 Specifix, Inc.
# All rights reserved.

import os
import os.path
import sys

# conary 
from build import lookaside, recipe, use
import conaryclient
from deps import deps
from local import database 
from repository import changeset, repository
import versions

# darby
from pkgid import TroveId, SourceId, ChangeSetId, TroveIdFromTrove
import pkgid
import flavorutil

class ControlFile:
    """ The controlFile contains the information about the packages 
        that should be built.  It gathers its information from a 
        specified group recipe, loading its source and picking out 
        the packages it wishes to add.  It then can load these 
        desired package's recipes, and determine information 
        about the troves that will result from cooking that recipe.
    """

    def __init__(self, arch, (name, versionStr, flavor), repos, cfg, 
                canonicalLabel, 
                updateLabel=None, controlTroveLabel=None):
        self._controlTroveInfo = (name, versionStr, flavor)
        self._repos = repos
        self._arch = arch
        self._canonicalLabel = canonicalLabel
        self._updateLabel = updateLabel
        if not controlTroveLabel:
            controlTroveLabel = canonicalLabel
        self._controlTroveLabel = controlTroveLabel

        self._cfg = cfg
        self._loaders = []
        # desTroves is desiredTrove to sourceId, many to one
        self._desTroves = {}
        # sources is troveName to sourceIds, one to many
        self._sourceIdsByName = {}
        # packages is package -> sourceId, many to many,
        # but all sourceIds that create a package are guaranteed to have 
        # the same name
        self._packages = {}
        self._packageCreators = {}
        self.usedFlags = {}
        self._fromSourceDir = {}

    def getControlTroveLabel(self):
        return self._controlTroveLabel

    def getControlTroveInfo(self):
        return self._controlTroveInfo

    def getLatestSource(self, name, versionStr=None):
        """ Get the latest source version for a trove.  Search
            both canonical and update sources. """

        # Note that we can't rely on installLabelPath because 
        # findTrove will return the result from the first label,
        # even if more recent troves are available at other labels
        canTroves =  self._repos.findTrove(self._canonicalLabel,
                                                name + ':source',
                                            self._cfg.buildFlavor, versionStr)
        assert(len(canTroves) == 1)
        return canTroves[0]


    def loadControlFile(self, loadRecipes=True, extraTroves=[]):
        """ Loads the control file's basic information about what 
            troves should be built.  If loadRecipes=True, also
            loads the desired troves' recipes and stores their
            classes for later use (calls getSources and loadRecipes).  
        """
        # grab the package and get a copy of the class defined in 
        # the controlTrove
        name, versionStr, flavor = self.getControlTroveInfo()
        if not versionStr:
            versionStr = self.getControlTroveLabel()
            
        # should be a source trove, so, no flavor
        self.loadGroup(name, versionStr)
        for extraTrove in extraTroves:
            if not isinstance(extraTrove, (list, tuple)):
                extraTrove = (extraTrove, None, None, None)
            else:
                extraTrove = (list(extraTrove) + [None, None, None])[0:4]
            if extraTrove[2] is None:
                extraTrove = list(extraTrove)
                extraTrove[2] = deps.DependencySet()
            if extraTrove[0].startswith('group-'):
                self.loadGroup(extraTrove[0], ctroveLabel)
            else:
                self.addDesiredTrove(*extraTrove)
        sys.stdout.flush()
        if loadRecipes:
            print "Loading Recipes..." 
            self.getSources()
            self.loadRecipes()

    def loadGroup(self, groupName, label):
        groupName = groupName + ':source'
        leaves = self._repos.getTroveLeavesByLabel([groupName], label)
        leaves = leaves[groupName]
        ver = leaves.keys()[-1]
        groupTrove = self._repos.getTrove(groupName, ver, deps.DependencySet())
        groupId = SourceId(groupName, 
                           groupTrove.getVersion(), 
                             groupTrove.getFlavor()) 
        groupClass = self.loadRecipe(groupId)

        # instantiate the recipe and call its setup method to 
        # make its internal addTroves be called
        branch = groupId.getVersion().branch()
        groupObj = groupClass(self._repos, self._cfg, branch, None)
        groupObj.setup()
        use.LocalFlags._clear()

        for (name, version, flavor, source) in groupObj.addTroveList:
            if version and version[0] == '/':
                v = versions.VersionFromString(version)
                if isinstance(v, versions.Version):
                    version = v.getSourceVersion().asString()
            if name.startswith('group-'):
                # XXX this doesn't allow the group to specify a version
                # string
                self.loadGroup(name, label)
            else:
                if source is None:
                    source = name.split(':')[0]
                if flavor is None:
                    flavor = deps.DependencySet()
                if deps.DEP_CLASS_IS in flavor.getDepClasses():
                    flavor = flavor.copy()
                    isClasses = flavor.members[deps.DEP_CLASS_IS]
                    if isClasses.members.keys() != [self._arch]:    
                        if self._arch not in isClasses.members.keys():
                            # don't even acknowledge this trove
                            continue
                        else:
                            from lib import epdb
                            epdb.set_trace()
                            # remove mention of other secondary architectures
                            # they are only important for cooking the final trove
                            isClasses.members = {
                                    self._arch: isClasses.members[self._arch] } 

                self.addDesiredTrove(name, version, flavor, source)

    def addDesiredTrove(self, troveName, versionStr, flavor, source):
        """ Add this this trove as one that should be built.
            Takes the format used in group-recipes' addTrove commands
        """
        if flavor is None:
            flavor = deps.DependencySet()
        #if (troveName, versionStr, flavor) in self._desTroves:
        #    raise RuntimeError, "Same trove listed twice in group file: (%s, %s %s)" % (troveName, versionStr, flavor)
        self._desTroves[(troveName, versionStr, flavor)] = None
        self._packageCreators[troveName.split(':')[0]] = source

    def setDesiredTroveSource(self, troveName, versionStr, flavor, 
                                                        sourceId):
        """ Add sourceId as the source that fulfills this desired 
            trove requirement """
        if self._desTroves[(troveName, versionStr, flavor)] is not None:
            if self._desTroves[(troveName, versionStr, flavor)] == sourceId:
                 return
            raise RuntimeError, ("Source trove that satisfies (%s, %s, %s) was"
                               " already set to %s, cannot set to %s" 
                               % (troveName, versionStr, flavor, 
                               self._desTroves[(troveName, versionStr, flavor)],
                               sourceId))
        self._desTroves[(troveName, versionStr, flavor)] = sourceId
        sourceId.setDesiredVersionStr(versionStr)
        troveName = troveName.split(':')[0]
        if troveName not in self._sourceIdsByName:
            self._sourceIdsByName[troveName] = []
        if sourceId in self._sourceIdsByName[troveName]:
           return 
        self._sourceIdsByName[troveName].append(sourceId)

    def addPackageCreator(self, packageName, sourceId):
        """ Add sourceId as a source package that can 
            result in a package with packageName being cooked. """
        if packageName not in self._packages:
            self._packages[packageName] = []
            self._packageCreators[packageName] = sourceId.getName()
        elif sourceId in self._packages[packageName]:
            # don't list a sourceId twice 
            return
        elif self.getPackageSourceName(packageName) != sourceId.getName():
            raise RuntimeError, ("Package %s was already set as created"
                                 " by %s, cannot set to %s" % (packageName, 
                                  self.getPackageSourceName(packageName),
                                  sourceId.getName()))
        self._packages[packageName].append(sourceId)

    def getDesiredTroveList(self):
        """ Return the human-readable set of troves to be built
            (as seen in the original control group
        """
        return self._desTroves.keys()

    def getDesiredTroveSourceId(self, troveName, versionStr, flavor):
        """ Get the source ids of packages that can create
            a desired trove
        """
        return self._desTroves[(troveName, versionStr, flavor)]

    def getSourceIds(self, troveName):
        """ Return the list of source packages for a trove name """
        return self._sourceIdsByName[troveName]

    def getSourceList(self):
        """ Return the names of packages for which we have  
        """
        keys = self._sourceIdsByName.keys()
        return keys

    def getPackageList(self):
        """ Gets the names of packages that are buildable by
            the loaded sources. 
            Valid after calls to loadRecipe/loadRecipes.
        """
        keys = self._packages.keys()
        return keys

    def isKnownPackage(self, packageName):
        """ Return True if any loaded source specified this package
            name as a package that can result from cooking it.
        """
        return packageName in self._packages

    def getPackageSourceIds(self, packageName):
        """ Return the source troves that state that they can build
            packageName
        """
        return self._packages[packageName]

    def getPackageSourceName(self, packageName):
        """ Return the name shared between all sourceIds that can build 
            this package """
        return self._packageCreators[packageName]

    def iterPackageSources(self):
        """ iterate through a package name and the source troves that 
            can result in a package with that name being built """
        for pkgName, sources in self._packages.iteritems():
            yield pkgName, sources

    def iterAllSourceIds(self):
        """ Iterate through all the known source Ids """
        for sourceName in self.getSourceList():
            for sourceId in self.getSourceIds(sourceName):
                yield sourceId

    def branchSourcePackages(self, sourceIds, newLabel):
        """ Branch the given sourceIds to the new branch, and update
            any needed pointers to the new sourceIds created """
        if not sourceIds:
            return

        cc = conaryclient.ConaryClient(self._cfg)
        labelSources = {}
        # make lists of sources on a particular branch.
        # this should handle branching packages that are on a different
        # branch correctly 
        needBranching = []
        for sourceId in sourceIds:
            label = sourceId.getLabel()
            if label == newLabel:
                continue
            needBranching.append(sourceId)
            if label not in labelSources:
                labelSources[label] = []
            labelSources[label].append(sourceId)

        for label in labelSources:
            for sourceId in labelSources[label]:
                print "Branching %s" % sourceId
                branchV = sourceId.getVersion().createBranch(newLabel, 
                                                             withVerRel=1)
                cc.createBranch(newLabel, sourceId.getVersion(), 
                                 [sourceId.getName() + ':source'])


    def getSources(self):
        """ 
            Must be called after calling loadControlFile. 
            Creates a list of the :source troves ids that fit the description
            of the desiredTroves.  Can be accessed by getDesiredTroveSources
            or getSourceTrovesByName.
        """
        notfound = {}
        # XXX this might be faster if we tried to replicate findTrove behavior
        # e.g., if versionStrs are on the same label (90% of the time), we 
        # can just get leaves on label
        ln = len(self.getDesiredTroveList())
        index = 1
        for (origTroveName, versionStr, flavor) in self.getDesiredTroveList():
            # remove potential :devel, etc, components from the components, 
            # since we want to point to the source trove
                                    
            troveName = origTroveName.split(':', 1)[0]
            print "%s/%s: %s, %s, %s" % (index, ln, origTroveName, versionStr, 
                                                                        flavor)
            index += 1

            try: 
                (sourceName, sourceVersion, dummy) = \
                                self.getLatestSource(troveName, versionStr)
            except repository.TroveNotFound:
                notfound[troveName] = True
                continue
            if isinstance(flavor, str):
                from lib import epdb
                epdb.set_trace()
            sourceId = SourceId(troveName, sourceVersion, flavor) 
            self.setDesiredTroveSource(origTroveName, versionStr, flavor,
                                                           sourceId) 
            self.addPackageCreator(troveName, sourceId)
        self._notFound = notfound

    def loadRecipes(self):
        """ Can only be called after getSources.  Actually loads the source
            troves that match the desired source trove ids.  This can be
            slow.  
        """

        keys = self.getSourceList()
        keys.sort()
        count = 0
        for sourceName in keys:
            for sourceId in self.getSourceIds(sourceName):
                self.loadRecipe(sourceId)
                sys.stdout.write('%d: %s\n' % (count, sourceId))
                count = count + 1
                sys.stdout.flush()
        sys.stdout.write('\nDone.\n')
        sys.stdout.flush()
        for package in self._notFound:
            if not self.isKnownPackage(package):
                print "Warning, could not find source trove for %s" % package
            else:
                desTroves = [ x for x in self.getDesiredTroveList() if \
                                                x[0].split(':')[0] == package ] 
                sourceIds = self.getPackageSourceIds(package)
                # sort by version (latest first)
                sourceIds.sort()
                sourceIds.reverse()
                for (desName, desVer, desFlavor) in desTroves:
                    found = False
                    for sourceId in sourceIds:
                        if (sourceId.getFlavor() == desFlavor 
                            and (desVer is None 
                             or sourceId.getVersionStr().find(desVer) != -1)):
                            found = True
                            break
                    if found:
                        self.setDesiredTroveSource(desName, desVer, 
                                                   desFlavor, sourceId)
        del self._notFound

    def loadRecipe(self, sourceId, label=None, packageCreator=True):
        """ Loads a recipeClass contained in a source trove identified by pkg.  
            Gathers information about the packages buildable from package
            Stores the information about the recipe's potential packages,
            as well as the class loaded from the recipe.
        """
        lcache = lookaside.RepositoryCache(self._repos)
        try:
            srcdirs = [ self._cfg.sourceSearchDir % { 'pkgname' : 
                                                        sourceId.getName() }  ]

            # ensure name has :source tacked on end, and recipefile is
            # name.recipe
            pkgName = sourceId.getName().split(':')[0]
            name = pkgName + ':source'
            recipefile = pkgName + '.recipe'

            # set up necessary flavors and track used flags before
            # calling loadRecipe, since even loading the class
            # may check some flags that may never be checked inside
            # the recipe
            use.LocalFlags._clear()
            use.setBuildFlagsFromFlavor(sourceId.getName(),
                                        sourceId.getFlavor())
            use.resetUsed()

            # put a little assertion in here to ensure that we 
            # actually are starting from a clean slate
            used = use.getUsed()
            assert ([ x for x in use.getUsed() ] == [])

            loader = None
            if hasattr(self._cfg, 'recipedir') and self._cfg.recipedir:
                recipeFile = '/'.join((self._cfg.recipedir, pkgName, 
                                                     pkgName + '.recipe'))
                if os.path.exists(recipeFile):
                    print "Loading %s from sources dir..." % pkgName
                    loader = recipe.RecipeLoader(recipeFile, cfg=self._cfg,
                                                             repos=self._repos)
                    loader = (loader, sourceId.getVersion())
                    self._fromSourceDir[sourceId] = True
            if loader is None:
                loader = recipe.recipeLoaderFromSourceComponent(name, 
                                    recipefile, self._cfg, self._repos, 
                                    sourceId.getVersionStr(), 
                                    label=sourceId.getLabel())
            # gather the local flags created (they may not have been tracked)
            sourceId.setLocalFlags(flavorutil.getLocalFlags())
            # gather the local/use/arch flags actually tracked
            sourceId.setUsedFlags(use.getUsed())
            # delete any created local flags
            recipeClass = loader[0].getRecipe()

            if not recipeClass.name.startswith('group-'):
                # grab information about the packages created 
                # by this recipe -- the packages may be used in
                # build requirements, or when picking packages
                # to add to a group
                recipeObj = recipeClass(self._cfg, lcache, srcdirs) 
                recipeObj.setup()
                if packageCreator:
                    for package in recipeObj.packages:
                        self.addPackageCreator(package, sourceId)
                    sourceId.packages = recipeObj.packages
            use.LocalFlags._clear()

            # we need to keep the loaders around so that they do not
            # get garbage collected -- their references are needed 
            # later for cooking.
            sourceId.setRecipeClass(recipeClass)
            self._loaders.append(loader)
        except recipe.RecipeFileError, e:
            raise
        else:
            return recipeClass

    def getInstalledPkgs(self, filterDict=None):
        """ Must be called after getSources.  Looks at the installed 
            packages in the given root, and matches them against the 
            list of source troves that must be built.  Returns a list
            matched, unmatched, where matched is a map from sourceId 
            => [(installedId, troveName), ...], and unmatched is map 
            from sourceId => [sourceTroveName , ...]
            XXX why isn't unmatched just a list of sourceIds?
        """
        matches = {}
        unmatched = {}

        # by default everything is unmatched
        for name,sourceIds in self.iterPackageSources(): 
            if filterDict and name not in filterDict:
                continue
            for sourceId in sourceIds:
                unmatched[sourceId] = True

        db = database.Database(self._cfg.root, self._cfg.dbPath)
        for troveName in db.iterAllTroveNames():
            # if we've never heard of this package, ignore it
            if not self.isKnownPackage(troveName):
                continue
            if filterDict and troveName not in filterDict:
                continue
            for version in  db.getTroveVersionList(troveName):
                for trove in db.findTrove(troveName, version.asString()):

                    installedId = TroveId(troveName, trove.getVersion(), 
                                                trove.getFlavor())
                    for sourceId in self.getPackageSourceIds(troveName):
                        # builtFrom ensures that it is possible
                        # to get the built trove from the sourceId
                        # pkg
                        
                        if (installedId.builtFrom(sourceId) or 
                            (self._updateLabel and installedId.builtFrom(
                                        sourceId.branch(self._updateLabel)))):
                            if sourceId not in matches:
                                matches[sourceId] = []
                            matches[sourceId].append(installedId)
                            try:
                                del unmatched[sourceId]
                            except KeyError:
                                pass
        return (matches, unmatched)

    def getMatchedChangeSets(self, changesetpath, filterDict=None,
                                                  allowVersionMismatch=False):
        """ Must be called after getSources.  Looks at the changesets 
            in changesetpath in the given root, and matches them against 
            the list of source troves that must be built.  Returns a list
            matched, unmatched, where matched is a map from sourceId 
            => [changesetId, ...], and unmatched is list of sourceIds.

            If filterDict is supplied, excludes examining all package 
            that are not keys in filterDict.

            Successful changesets must match:
            1. Name 
            2. Label
            3. Version (this may have been grabbed from repository
                        if not specified in control file)
            4. Source version
            5. Use/Flag flavor 

            If allowVersionMismatch is True, then it is not required 
            that the trove found matches the latest source version of a trove.
            Instead, the latest built version on the given branch is acceptable.
        """
        matches = {}
        unmatched = {}
        # all packages are unmatched by default
        for name,sourceIds in self.iterPackageSources():
            for sourceId in sourceIds:
                if filterDict and sourceId.getName() not in filterDict:
                    continue
                unmatched[sourceId] = True
        if not os.path.exists(changesetpath):
            return matches, unmatched

        changesetNames =  [ x for x in os.listdir(changesetpath) if x.endswith('.ccs') ]
        flavors = {}
        changesetNames.sort()
        ln = len(changesetNames)
        index = 1
        for changesetName in changesetNames:
            print '%d/%d: %s' % (index, ln, changesetName)
            index += 1
            csfile = os.path.join(changesetpath, changesetName)
            cs = changeset.ChangeSetFromFile(csfile)
            pkgs = cs.getPrimaryPackageList()
            for (name, version, flavor) in pkgs:
                if filterDict and name not in filterDict:
                    continue
                csId = ChangeSetId(name, version, flavor, csfile)
                if not self.isKnownPackage(csId.getName()):
                    continue
                for sourceId in self.getPackageSourceIds(csId.getName()): 
                    if self._updateLabel:
                        if not csId.builtFrom(
                                        sourceId.branch(self._updateLabel),
                                    allowVersionMismatch=allowVersionMismatch):
                            continue
                    elif not csId.builtFrom(sourceId,
                                allowVersionMismatch=allowVersionMismatch):
                        continue
                    matches[sourceId] = True
                    if self._updateLabel:
                        sourceId.addBranchedTroveId(csId, self._updateLabel,
                                allowVersionMismatch=allowVersionMismatch)
                    else:
                        sourceId.addTroveId(csId, 
                                    allowVersionMismatch=allowVersionMismatch)
                    try:
                        del unmatched[sourceId]
                    except KeyError:
                        pass
        return (matches, unmatched)

    def getRepoTrovesFromCookedGroup(self):
        matches = {}
        unmatched = {}
        flavors = {}
        repos = self._repos
        # all packages are unmatched by default
        #for name,sourceIds in self.iterPackageSources():
        #    for sourceId in sourceIds:
        #        unmatched[sourceId] = True
        name, versionStr, flavor = self._controlTroveInfo
        if flavor:
            buildFlavor = flavorutil.overrideFlavor(self._cfg.buildFlavor,
                                                    flavor)
        else:
            buildFlavor = self._cfg.buildFlavor
        troveList = repos.findTrove(self._controlTroveLabel, 
                                    name,
                                    buildFlavor)
        if not troveList:
            raise RuntimeError, "No matching groups for %s" % self.controlTroveName
        if len(troveList) > 1:
            raise RuntimeError, "Too many matching groups!"
        groupTroves = repos.getTroves(troveList)
        troves = {}
        while groupTroves:
            groupTrove = groupTroves.pop()
            troves[TroveId(groupTrove.getName(), groupTrove.getVersion(), groupTrove.getFlavor())] = True
            for (name, version, flavor) in groupTrove.iterTroveList():
                if name.startswith('group-'):
                    trv = repos.getTrove(name, version, flavor)
                    groupTroves.append(trv)
                else:
                    troves[TroveId(name, version, flavor)] = True
        return troves


    def getMatchedRepoTroves(self, filterDict=None, allowVersionMismatch=False):
        """ Must be called after getSources.  Looks at the troves 
            on installLabelPath, and matches them against 
            the list of source troves that must be built.  Returns a list
            matched, unmatched, where matched is a map from sourceId 
            => [changesetId, ...], and unmatched is list of sourceIds.

            If filterDict is supplied, excludes examining all package 
            that are not keys in filterDict.

            Successful troves must match:
            1. Name 
            2. Label (may be branched into the update repo)
            3. Version (this may have been grabbed from repository
                        if not specified in control file)
            4. Source version
            5. Use/Flag flavor 

            If allowVersionMismatch is True, then it is not required 
            that the trove found matches the latest source version of a trove.
            Instead, the latest built version on the given branch is acceptable.
        """
        matches = {}
        unmatched = {}
        flavors = {}
        # all packages are unmatched by default
        for name,sourceIds in self.iterPackageSources():
            for sourceId in sourceIds:
                if filterDict and sourceId.getName() not in filterDict:
                    continue
                unmatched[sourceId] = True

        ln = len(unmatched.keys())
        unmatchedKeys = unmatched.keys()
        unmatchedKeys.sort()
        index = 1

        for sourceId in unmatchedKeys:
            print "%d/%d: %s" % (index, ln, sourceId)
            index += 1
            # find all latest troves in canonical and update sources
            matchingTroves = []
            # findTrove doesn't seem to reliably give us the latest
            # version.  getLeavesByLabel seems to be the culprit
            # we hack around this by getting our own version list
            #troves = self._repos.findTrove(
            #                 self._canonicalLabel, 
            #                 sourceId.getName(), 
            #                 self._cfg.flavor,
            #                 sourceId.getLabel().asString(),
            #                 acrossRepositories=False, withFiles=False)
            try:
                vers = self._repos.getTroveVersionList(
                                           self._canonicalLabel.getHost(),
                                           dict.fromkeys([sourceId.getName()], 
                                                                        None))
                if vers:
                    flavors = self._repos.getTroveVersionFlavors(vers)
                    flavors = flavors[sourceId.getName()]
                else:
                    flavors = {}

                for ver in flavors:
                    for flavor in flavors[ver]:
                            troveId = TroveId(sourceId.getName(), ver,
                                                flavor)
                            if troveId.builtFrom(sourceId, 
                                 allowVersionMismatch=allowVersionMismatch):
                                matchingTroves.append(troveId)
            except repository.TroveNotFound:
                pass
            if self._updateLabel:
                # search the update label for newer versions of this package
                branchedSourceId  = sourceId.branch(self._updateLabel)
                branch = branchedSourceId.getBinaryVersion()
                try:
                    vers = self._repos.getTroveVersionList(
                                                    self._updateLabel.getHost(),
                                                    {sourceId.getName():None})
                    if vers:
                        flavors = self._repos.getTroveVersionFlavors(vers)
                        flavors = flavors[sourceId.getName()]
                    else:
                        flavors = {}

                    for ver in flavors:
                        for flavor in flavors[ver]:
                                troveId = TroveId(sourceId.getName(), ver,
                                                    flavor)
                                # If the trove in the update repo was built 
                                # from the source trove, it would have been 
                                # after the source trove was branched
                                if troveId.builtFrom(branchedSourceId,
                                     allowVersionMismatch=allowVersionMismatch):
                                    matchingTroves.append(troveId)
                except repository.TroveNotFound:
                    pass
            if allowVersionMismatch and matchingTroves:
                # even though we are allowing for binaries that are not 
                # as new as the latest :source trove, we still want only
                # the latest binaries on this branch.
                matchingTroves.sort()
                matchingTroves.reverse()
                newMatching = [ matchingTroves[0] ]
                for troveId in matchingTroves[1:]:
                    if troveId.getVersion() == matchingTroves[0].getVersion():
                        newMatching.append(troveId)
                    else:
                        break
                matchingTroves = newMatching
            for troveId in matchingTroves:
                matches[sourceId] = True
                if troveId.getLabel() == self._updateLabel:
                    sourceId.addBranchedTroveId(troveId, self._updateLabel,
                                    allowVersionMismatch=allowVersionMismatch)
                else:
                    sourceId.addTroveId(troveId, 
                                    allowVersionMismatch=allowVersionMismatch)
                try:
                    del unmatched[sourceId]
                except KeyError:
                    pass
        return (matches, unmatched)

    def loadPackageReqs(self, troveNames, extraTroves=[]):
        """ An alternative to loadControlFile.  Load packages only for 
        the prerequsites for a package.  
        """
        self.loadControlFile(loadRecipes=False, extraTroves=extraTroves)
        # XXX this could be so much faster if we only loaded
        # the sources we actually want...
        print "Getting sources..."
        self.getSources()
        print "Loading needed recipes..."
        origDeps = {}
        deps = []
        for troveName in troveNames:
            sourceName = self.getPackageSourceName(troveName.split(':')[0])
            origDeps[sourceName] = True
            deps.append(sourceName)
        allDeps = {}
        while deps:
            sourceName = deps.pop()
            for depId in self.getSourceIds(sourceName):
                print "Loading %s..." % depId
                recipeClass = self.loadRecipe(depId)
                for newDepName in recipeClass.buildRequires:
                    baseDepName = newDepName.split(':')[0]
                    sourceName = self.getPackageSourceName(baseDepName)
                    if (baseDepName not in allDeps 
                        and baseDepName not in origDeps):
                        allDeps[sourceName] = True
                        deps.append(sourceName)
        return allDeps
