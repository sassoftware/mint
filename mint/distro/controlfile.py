import os
import os.path
import sys

# conary 
from deps import deps
from build import lookaside, recipe, use
from local import database 
from repository import changeset, repository

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

    def __init__(self, controlTroveName, repos, cfg, canonicalLabel, 
                                                            updateLabel=None):
        self._controlTroveName = controlTroveName
        self._repos = repos
        self._canonicalLabel = canonicalLabel
        self._updateLabel = updateLabel
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
        self.usedFlags = {}

    def getControlTroveName(self):
        return self._controlTroveName

    def getLatestSource(self, name, versionStr=None):
        """ Get the latest source version for a trove.  Search
            both canonical and update sources. """

        # Note you can't just rely on the search path because 
        # findTrove will return the first result, even if 
        # later troves are available laterl
        canTroves =  self._repos.findTrove(self._canonicalLabel,
                                                name + ':source',
                                                None, versionStr)
        assert(len(canTroves) == 1)
        canTrove = canTroves[0]

        if self._updateLabel:
            try:
                updateTroves =  self._repos.findTrove(self._updateLabel,
                                               name + ':source', 
                                               None, versionStr)
                # we only get to this assertion if 
                # we found at least one trove...
                if len(updateTroves) > 1:
                    updateIds = [ TroveIdFromTrove(x) for x in updateTroves ] 
                    latest = pkgid.getSortedLeavesAfterUnbranch(updateIds, 
                                                        self._updateLabel)
                    if len(latest) > 1:
                        # multiple branches were returned.
                        # if we didn't ask for a branch,
                        # assume we don't want one
                        newlatest = []
                        if not versionStr or versionStr.find('@') == -1:
                            desiredLabel = self._canonicalLabel
                        elif versionStr.find('/') == -1:
                            desiredLabel = versions.Label(versionStr)
                        else:
                            desiredLabel = versions.VersionFromString(versionStr)
                            desiredLabel = desiredLabel.label()
                        for leaf in latest:
                            assert(len(leaf) == 1)
                            leaf = leaf[0]
                            if leaf.unbranch(self._updateLabel).getLabel() \
                                    == desiredLabel:
                                newlatest.append([leaf])
                        latest = newlatest
                    if len(latest) > 1:
                        raise RuntimeError, (
                "Multiple possible versions could match version String %s "
                " for trove %s: %s" % (versionStr, name, 
                                       [x[0].asString() for x in latest]))
                    # could happen if there are multiple flavors...
                    # but these are source troves!
                    assert(len(latest[0]) == 1)
                    updateTrove = latest[0][0]
                else:
                    updateTrove = updateTroves[0]
            except repository.PackageNotFound:
                return canTroves[0]
            if not canTrove.getVersion().isAfter(updateTrove.getVersion()):
                return updateTrove
        return canTrove


    def loadControlFile(self, loadRecipes=True):
        """ Loads the control file's basic information about what 
            troves should be built.  If loadRecipes=True, also
            loads the desired troves' recipes and stores their
            classes for later use (calls getSources and loadRecipes).  
        """
        # grab the package and get a copy of the class defined in 
        # the controlTrove

        controlTrove = self.getLatestSource(self.getControlTroveName()) 
        controlId = SourceId(self.getControlTroveName(), 
                             controlTrove.getVersion(), 
                             controlTrove.getFlavor()) 
        controlClass = self.loadRecipe(controlId)

        # instantiate the recipe and call its setup method to 
        # make its internal addTroves be called
        branch = controlId.getVersion().branch()
        controlObj = controlClass(self._repos, self._cfg, branch, None)
        controlObj.setup()
        # setup may instantiate some LocalFlags while creating 
        # flagSets.  Delete those flags.
        for flag in use.LocalFlags.keys():
            del use.LocalFlags[flag]


        
        for (name, version, flavor) in controlObj.addTroveList:
            self.addDesiredTrove(name, version, flavor)

        sys.stdout.flush()
        if loadRecipes:
            print "Loading Recipes..." 
            self.getSources()
            self.loadRecipes()

    def addDesiredTrove(self, troveName, versionStr, flavor):
        """ Add this this trove as one that should be built.
            Takes the format used in group-recipes' addTrove commands
        """
        if flavor is not None:
            flavor = flavor.toDependency(troveName.split(':')[0])
        if (troveName, versionStr, flavor) in self._desTroves:
            raise RuntimeError, "Same trove listed twice in group file: (%s, %s %s)" % (troveName, versionStr, flavor)
        self._desTroves[(troveName, versionStr, flavor)] = None

    def setDesiredTroveSource(self, troveName, versionStr, flavor, 
                                                        sourceId):
        """ Add sourceId as the source that fulfills this desired 
            trove requirement """
        if self._desTroves[(troveName, versionStr, flavor)] is not None:
            raise RuntimeError, ("Source trove that satisfies (%s, %s, %s) was"
                               " already set to %s, cannot set to %s" 
                               % (troveName, versionStr, flavor, 
                               self._desTroves[(troveName, versionStr, flavor)],
                               sourceId))
        self._desTroves[(troveName, versionStr, flavor)] = sourceId
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
        return self._packages[packageName][0].getName()

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

        labelSources = {}
        # make lists of sources on a particular branch.
        # this should handle branching packages that are on a different
        # branch correctly 
        needBranching = []
        for sourceId in sourceIds:
            label = sourceId.getVersion().branch().label()
            if label.getHost() == newLabel.getHost():
                continue
            needBranching.append(sourceId)
            if label not in labelSources:
                labelSources[label] = []
            labelSources[label].append(sourceId)

        for label in labelSources:
            for sourceId in labelSources[label]:
                print "Branching %s" % sourceId
                branchV = sourceId.getVersion().fork(newLabel, sameVerRel = 1)
                self._repos.createBranch(newLabel,
                                         sourceId.getVersion(), 
                                         [sourceId.getName() + ':source'])

        # Update the sourceIds so that when we load them
        # we will load them from the new label
        # XXX this may be dumb
        for sourceId in needBranching:
            branchV = sourceId.getVersion().fork(newLabel, sameVerRel = 1)
            sourceId.setVersion(branchV)


    def getSources(self):
        """ 
            Must be called after calling loadControlFile. 
            Creates a list of the :source troves ids that fit the description
            of the desiredTroves.  Can be accessed by getDesiredTroveSources
            or getSourceTrovesByName.
        """
        notfound = {}
        flavor = None
        # XXX this might be faster if we tried to replicate findTrove behavior
        # e.g., if versionStrs are on the same label (90% of the time), we 
        # can just get leaves on label
        ln = self.getDesiredTroveList()
        index = 0
        for (origTroveName, versionStr, flavor) in self.getDesiredTroveList():
            # remove potential :devel, etc, components from the components, 
            # since we want to point to the source trove
            troveName = origTroveName.split(':', 1)[0]
            #print "%s/%s: %s, %s, %s" % (index, ln, origTroveName, versionStr, 
            #                                                        flavor)
            index += 1
            try: 
                sourceTrove = self.getLatestSource(troveName, versionStr)
            except repository.PackageNotFound:
                notfound[troveName] = True
                continue
            sourceId = SourceId(troveName, sourceTrove.getVersion(), 
                                                               flavor) 
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
        del self._notFound

    def loadRecipe(self, sourceId, label=None):
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
            recipefile = sourceId.getName().split(':')[0]
            name = recipefile + ':source'
            recipefile += '.recipe'

            # set up necessary flavors and track used flags before
            # calling loadRecipe, since even loading the class
            # may check some flags that may never be checked inside
            # the recipe
            flavorutil.resetLocalFlags()
            oldFlavor = flavorutil.setFlavor(sourceId.getFlavor(), 
                                             sourceId.getName())
            use.resetUsed()

            # put a little assertion in here to ensure that we 
            # actually are starting from a clean slate
            used = use.getUsed()
            assert ([ x for x in use.getUsedSet() ] == [])

            loader = recipe.recipeLoaderFromSourceComponent(name, recipefile, 
                                    self._cfg, self._repos, 
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
                for package in recipeObj.packages:
                    self.addPackageCreator(package, sourceId)
            flavorutil.resetLocalFlags()

            # we need to keep the loaders around so that they do not
            # get garbage collected -- their references are needed 
            # later for cooking.
            sourceId.setRecipeClass(recipeClass)
            self._loaders.append(loader)
        except recipe.RecipeFileError, e:
            flavorutil.resetFlavor(oldFlavor)
            raise
        else:
            flavorutil.resetFlavor(oldFlavor)
            return recipeClass

    def getInstalledPkgs(self):
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
            for sourceId in sourceIds:
                if sourceId not in unmatched:
                    unmatched[sourceId] = []
                unmatched[sourceId].append(name)

        db = database.Database(self._cfg.root, self._cfg.dbPath)
        for troveName in db.iterAllTroveNames():
            # if we've never heard of this package, ignore it
            if not self.isKnownPackage(troveName):
                continue
            for version in  db.getTroveVersionList(troveName):
                for trove in db.findTrove(troveName, version.asString()):

                    installedId = TroveId(troveName, trove.getVersion(), 
                                                trove.getFlavor())
                    for sourceId in self.getPackageSourceIds(installedId.getName()):
                        # builtFrom ensures that it is possible
                        # to get the built trove from the sourceId
                        # pkg
                        if not installedId.builtFrom(sourceId):
                            continue
                        if sourceId not in matches:
                            matches[sourceId] = []
                        matches[sourceId].append((installedId, troveName))
                        try:
                            del unmatched[sourceId]
                        except KeyError:
                            pass
        return (matches, unmatched)

    def getMatchedChangeSets(self, changesetpath, filterDict={}):
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
        """
        matches = {}
        unmatched = {}
        # all packages are unmatched by default
        for name,sourceIds in self.iterPackageSources():
            for sourceId in sourceIds:
                if filterDict and sourceId.getName() not in filterDict:
                    continue
                if sourceId not in unmatched:
                    unmatched[sourceId] = []
                unmatched[sourceId].append(name)
        if not os.path.exists(changesetpath):
            return matches, unmatched

        changesetNames =  [ x for x in os.listdir(changesetpath) if x.endswith('.ccs') ]
        flavors = {}
        changesetNames.sort()
        ln = len(changesetNames)
        index = 0
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
                    if not csId.builtFrom(sourceId):
                        continue
                    # We do some extra work here to ensure that 
                    # we only count one changeset with a particular
                    # flavor as a match per sourceId.   
                    # We keep track of matches for a package by flavor
                    # and if two packages match, we make only include
                    # the one with the later build count
                    if sourceId not in matches:
                        matches[sourceId] = []
                    if sourceId not in flavors:
                        flavors[sourceId] = {}
                    if csId.getFlavor() not in flavors[sourceId]:
                        flavors[sourceId][csId.getFlavor()] = csId
                    else:
                        other = flavors[sourceId][csId.getFlavor()]
                        if other.getBuildCount() < \
                            csId.getBuildCount():
                            matches[sourceId].remove(other)
                            flavors[sourceId][csId.getFlavor()] = csId
                        else:
                            # if there is already a changeset with
                            # this version and flavor but a later
                            # build count, don't count this as a match
                            continue
                    matches[sourceId].append(csId)
                    sourceId.addTroveId(csId)
                    try:
                        del unmatched[sourceId]
                    except KeyError:
                        pass
        return (matches, unmatched)

    def getMatchedRepoTroves(self, filterDict=None):
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
        """
        matches = {}
        unmatched = {}
        flavors = {}
        # all packages are unmatched by default
        for name,sourceIds in self.iterPackageSources():
            for sourceId in sourceIds:
                if filterDict and sourceId.getName() not in filterDict:
                    continue
                if sourceId not in unmatched:
                    unmatched[sourceId] = []
                unmatched[sourceId].append(name)

        ln = len(unmatched.keys())
        index = 0
        for sourceId in unmatched.keys():
            print "%d/%d: %s" % (index, ln, sourceId)
            index += 1
            if filterDict and sourceId.getName() not in filterDict:
                continue
            # find all latest troves in canonical and update sources
            matchingTroves = []
            try:
                troves = self._repos.findTrove(
                                 self._canonicalLabel, 
                                 sourceId.getName(), 
                                 self._cfg.flavor,
                                 sourceId.getLabel().asString(),
                                 acrossRepositories=False, withFiles=False)
                
            except repository.PackageNotFound:
                troves = []
            for trove in troves:
                troveId = TroveId(trove.getName(), trove.getVersion(), 
                                  trove.getFlavor())
                # builtfrom should take care of any extra troves
                # we found with the wrong version #s, source
                # counts
                if not troveId.builtFrom(sourceId):
                    continue
                matchingTroves.append(troveId)

            if self._updateLabel:
                # search the update label for newer versions of this package
                branchedSourceId  = sourceId.branch(self._updateLabel)
                branch = branchedSourceId.getVersion().branch().getBinaryBranch()
                try:
                    vers = self._repos.getTroveVersionList(
                                                    self._updateLabel.getHost(),
                                                    [sourceId.getName()])
                    flavors = self._repos.getTroveVersionFlavors(vers)
                    flavors = flavors[sourceId.getName()]

                    for ver in flavors:
                        for flavor in flavors[ver]:
                                troveId = TroveId(sourceId.getName(), ver,
                                                    flavor)
                                # If the trove in the update repo was built 
                                # from the source trove, it would have been 
                                # after the source trove was branched
                                if not troveId.builtFrom(branchedSourceId):
                                    continue
                                matchingTroves.append(troveId)
                except repository.PackageNotFound:
                    pass
            for troveId in matchingTroves:
                # We do some extra work here to ensure that 
                # we only count one trove with a particular
                # flavor as a match per sourceId.   
                # We keep track of matches for a package by flavor
                # and if two packages match, we make only include
                # the one with the later build count
                if sourceId not in matches:
                    matches[sourceId] = []
                if sourceId not in flavors:
                    flavors[sourceId] = {}
                if troveId.getFlavor() not in flavors[sourceId]:
                    flavors[sourceId][troveId.getFlavor()] = troveId
                else:
                    other = flavors[sourceId][troveId.getFlavor()]
                    if other.getVersion().trailingVersion().buildCount < \
                        troveId.getVersion().trailingVersion().buildCount:
                        matches[sourceId].remove(other)
                        flavors[sourceId][troveId.getFlavor()] = troveId
                    else:
                        # if there is already a trove with
                        # this version and flavor but a later
                        # build count, don't count this as a match
                        continue
                matches[sourceId].append(troveId)
                if troveId.getLabel() == self._updateLabel:
                    sourceId.addBranchedTroveId(troveId, self._updateLabel)
                else:
                    sourceId.addTroveId(troveId)
                try:
                    del unmatched[sourceId]
                except KeyError:
                    pass
        return (matches, unmatched)


    def loadPackageReqs(self, troveName):
        """ An alternative to loadControlFile.  Load packages only for 
        the prerequsites for a package.  
        """
        self.loadControlFile(loadRecipes=False)
        # XXX this could be so much faster if we only loaded
        # the sources we actually want...
        print "Getting sources..."
        self.getSources()
        print "Loading needed recipes..."
        deps = [troveName]
        allDeps = {}
        allDeps[troveName] = True
        while deps:
            depName = deps.pop()
            for depId in self.getSourceIds(depName):
                print "Loading %s..." % depId
                recipeClass = self.loadRecipe(depId)
                for newDepName in recipeClass.buildRequires:
                    baseDepName = newDepName.split(':')[0]
                    if baseDepName not in allDeps:
                        allDeps[baseDepName] = True
                        deps.append(baseDepName)
        return allDeps
