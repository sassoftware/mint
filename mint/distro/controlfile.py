import os
import os.path
import sys

# conary 
from deps import deps
from build import lookaside, recipe, use
from local import database 
from repository import changeset, repository

# darby
from pkgid import PkgId, thawPackage
import flavorutil

class ControlFile:
    """ The controlFile contains the information about the packages 
        that should be built.  It gathers its information from a 
        specified group recipe, loading its source and picking out 
        the packages it wishes to add.  It then can load these 
        desired package's recipes, and determine information 
        about the troves that will result from cooking that recipe.
    """

    def __init__(self, controlTroveName, repos, cfg, label):
        self._controlTroveName = controlTroveName + ':source'
        self._repos = repos
        self._controlLabel = label
        self._cfg = cfg
        self._loaders = []
        self.packages = {}
        self.recipes = {}
        self.sources = {}
        self.troves = {}
        self.usedFlags = {}

    def getControlTroveName(self):
        return self._controlTroveName

    def getControlTroveLabel(self):
        return self._controlLabel

    def loadControlFile(self, loadRecipes=True):
        """ Loads the control file's basic information about what 
            troves should be built.  If loadRecipes=True, also
            loads the desired troves' recipes and stores their
            classes for later use (calls getSources and loadRecipes).  
        """
        # grab the package and get a copy of the class defined in 
        # the controlTrove
        controlTrove = self._repos.findTrove(self.getControlTroveLabel(),
                                            self.getControlTroveName(), 
                                            None, None)[0]
        controlId = PkgId(self.getControlTroveName(), 
                           controlTrove.getVersion(), 
                           controlTrove.getFlavor()) 
        controlClass = self.loadRecipe(controlId)

        # instantiate the recipe and call its setup method to 
        # make its internal addTroves be called
        branch = controlId.getVersion().branch()
        controlObj = controlClass(self._repos, self._cfg, branch, None)
        controlObj.setup()

        
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
            flavor = flavor.toDependency(troveName)
        self.troves[(troveName, versionStr, flavor)] = []

    def addDesiredTroveSource(self, troveName, versionStr, flavor, 
                                                        sourceId):
        """ Add sourceId as a source that fulfills this desired 
            trove requirement """
        self.troves[(troveName, versionStr, flavor)].append(sourceId)
        troveName = troveName.split(':')[0]
        if troveName not in self.sources:
            self.sources[troveName] = []
        self.sources[troveName].append(sourceId)

    def addPackageCreator(self, packageName, sourceId):
        """ Add sourceId as source that can result in
            a package with packageName being cooked. """
        if not packageName in self.packages:
            self.packages[packageName] = []
            self.packages[packageName].append(sourceId)

    def getDesiredTroveList(self):
        """ Return the human-readable set of troves to be built
            (as seen in the original control group
        """
        return self.troves.keys()

    def getDesiredTroveSources(self, troveName, versionStr, flavor):
        """ Get the source ids of packages that can create
            a desired trove
        """
        return self.troves[(troveName, versionStr, flavor)]

    def getSourceIds(self, troveName):
        """ Return the list of source packages for a trove name """
        return self.sources[troveName]


    def addRecipeSource(self, recipeName, sourceId):
        """ Add sourceId as a source that uses this recipe 
            XXX can get get rid of self.recipes?
        """ 
        l = self.recipes.get(recipeName, [])
        l.append(sourceId)
        self.recipes[recipeName] = l

    def getRecipeList(self):
        return self.recipes.keys()

    def getRecipeSources(self, recipeName):
        """ Return the list of source packages for recipe name 
            (how is this different from getSource?
        """
        return self.recipes[recipeName]

    def getSourceList(self):
        """ Return the names of packages for which we have  
        """
        keys = self.sources.keys()
        return keys

    def getPackageList(self):
        """ Gets the names of packages that are buildable by
            the loaded sources. 
            Valid after calls to loadRecipe/loadRecipes.
        """
        keys = self.packages.keys()
        return keys

    def isKnownPackage(self, packageName):
        """ Return True if any loaded source specified this package
            name as a package that can result from cooking it.
        """
        return packageName in self.packages

    def getPackageSources(self, packageName):
        """ Return the source troves that state that they can build
            packageName
        """
        return self.packages[packageName]

    def iterPackageSources(self):
        """ iterate through a package name and the source troves that 
            can result in a package with that name being built """
        for pkgName, sources in self.packages.iteritems():
            yield pkgName, sources

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
        for (origTroveName, versionStr, flavor) in self.getDesiredTroveList():
            # remove potential :devel, etc, components from the components, 
            # since we want to point to the source trove
            troveName = origTroveName.split(':', 1)[0]
            try: 
                sourceTroveName = troveName + ':source'
                # XXX can't look at flavor yet
                sourceTroves = self._repos.findTrove(self._controlLabel, 
                                            sourceTroveName, None, versionStr)
            except repository.PackageNotFound:
                notfound[troveName] = True
                continue
            for sourceTrove in sourceTroves:
                sourceId = PkgId(troveName, sourceTrove.getVersion(), flavor) 
                self.addDesiredTroveSource(origTroveName, versionStr, flavor,
                                                               sourceId) 
        self.notfound = notfound

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

    def loadRecipe(self, sourceId, label=None):
        """ Loads a recipeClass contained in a source trove identified by pkg.  
            Gathers information about the packages buildable from package
            Stores the information about the recipe's potential packages,
            as well as the class loaded from the recipe.
            XXX need to combine getRecipeSources and getSource.
            XXX add getRecipeClass method
        """
        lcache = lookaside.RepositoryCache(self._repos)
        try:
            srcdirs = [ self._cfg.sourceSearchDir % { 'pkgname' : sourceId.name }  ]

            # ensure name has :source tacked on end, and recipefile is
            # name.recipe
            recipefile = sourceId.getName().split(':')[0]
            name = recipefile + ':source'
            recipefile += '.recipe'

            # set up necessary flavors and track used flags before
            # calling loadRecipe, since even loading the class
            # may check some flags that may never be checked inside
            # the recipe
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
                                    label=label)
            sourceId.setUsedFlags(use.getUsed())
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
                # XXX replace with 
                self.addRecipeSource(recipeClass.name, sourceId)

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

                    installedId = PkgId(troveName, trove.getVersion(), 
                                                trove.getFlavor())
                    for sourceId in self.getPackageSources(installedId.name):
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
        for changesetName in changesetNames:
            csfile = os.path.join(changesetpath, changesetName)
            cs = changeset.ChangeSetFromFile(csfile)
            pkgs = cs.primaryTroveList
            for (name, version, flavor) in pkgs:
                if filterDict and name not in filterDict:
                    continue
                csId = PkgId(name, version, flavor, justName=True)
                if not self.isKnownPackage(csId.getName()):
                    continue
                for sourceId in self.getPackageSources(csId.name): 
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
                        if other.version.trailingVersion().buildCount < \
                            csId.version.trailingVersion().buildCount:
                            matches[sourceId].remove(other)
                            flavors[sourceId][csId.getFlavor()] = csId
                        else:
                            # if there is already a changeset with
                            # this version and flavor but a later
                            # build count, don't count this as a match
                            continue
                    matches[sourceId].append(csId)
                    csId.setChangeSetFile(csfile)
                    sourceId.addChangeSet(csId)
                    try:
                        del unmatched[sourceId]
                    except KeyError:
                        pass
        return (matches, unmatched)

    def getDesiredCompiledVersion(self, pkg):
        """ XXX is this used anywhere?  It is a dumb function """
        pv = pkg.version.copy()
        versions = self._repos.getTroveVersionList(pkg.version.branch().label(), [pkg.name])
        maxver = None
        maxcount = -1
        for version in versions[pkg.name]:
            bc = version.trailingVersion().buildCount
            pv.trailingVersion().buildCount = bc
            if pv == version:
                if bc > maxcount:
                    maxcount = bc
                    maxver = version
        return version

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
            for depId in self.sources[depName]:
                print "Loading %s..." % depId
                recipeClass = self.loadRecipe(depId)
                for newDepName in recipeClass.buildRequires:
                    baseDepName = newDepName.split(':')[0]
                    if baseDepName not in allDeps:
                        allDeps[baseDepName] = True
                        deps.append(baseDepName)
        return allDeps
