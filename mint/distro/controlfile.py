# Here's what I need to be able to do:
# 1.  Grab the desired version info from control file
# 2.  Determine the correct source version for each desired verion - Update
#     desired version to include latest source version information 
# 3.  Determine if a changeset file fits the desired version
# 4.  Grab a matching version from the repository
from build import lookaside, recipe, use
from local import database 
import os
import os.path
from repository import changeset, repository
from pkgid import PkgId, thawPackage
import sys

class ControlFile:
    def __init__(self, group, repos, cfg, label):
        self.file = group + ':source'
        self.repos = repos
        self.label = label
        self._loaders = []
        self.cfg = cfg

    def loadControlFile(self, loadRecipes=True):
        self.trove = self.repos.findTrove(self.label, self.file, None, None)[0]
        self.pkg = PkgId(self.file, self.trove.getVersion(), self.trove.getFlavor(), justName = True) 
        self.controlClass = self.loadRecipe(self.pkg)
        branch = self.pkg.version.branch()
        self.controlObj = self.controlClass(self.repos, self.cfg, branch, None)
        self.controlObj.setup()
        self.troves = self.controlObj.addTroveList
        # XXX need to change variable names...
        self.packages = {}
        self.recipes = {}
        self.sources = {}
        self.usedFlags = {}
        sys.stdout.flush()
        if loadRecipes:
            print "Loading Recipes..." 
            self.getSources()
            self.loadRecipes()

    def getSources(self):
        notfound = {}
        sources = {}
        flavor = None
        # XXX this might be faster if we tried to replicate findTrove behavior
        # e.g., if versionStrs are on the same label (90% of the time), we 
        # can just get leaves on label
        for (troveName, versionStr, flavor) in self.troves:
            # remove potential :devel, etc, components from the components, 
            # since we want to point to the source trove
            troveName = troveName.split(':', 1)[0]
            try: 
                sourceTroveName = troveName + ':source'
                # XXX can't look at flavor yet
                sourceTroves = self.repos.findTrove(self.label, sourceTroveName, None, versionStr)
            except repository.PackageNotFound:
                notfound[troveName] = True
                continue
            for sourceTrove in sourceTroves:
                p = PkgId(troveName, sourceTrove.getVersion(), sourceTrove.getFlavor(), justName = True) 
                if troveName not in sources:
                    sources[troveName] = []
                # its possible that multiple addTrove commands point to a single
                # source trove
                if p not in sources[troveName]:
                    sources[troveName].append(p)
        self.notfound = notfound
        self.sources = sources

    def loadRecipes(self):
        self.recipes = {}
        keys = self.sources.keys()
        keys.sort()
        count = 0
        for source in keys:
            for p in self.sources[source]:
                self.loadRecipe(p)
                sys.stdout.write('%d: %s\n' % (count, p))
                count = count + 1
                sys.stdout.flush()
        sys.stdout.write('\nDone.\n')
        sys.stdout.flush()

    def loadRecipe(self, pkg, label=None):
        lcache = lookaside.RepositoryCache(self.repos)
        try:
            srcdirs = [ self.cfg.sourceSearchDir % { 'pkgname' : pkg.name }  ]

            recipefile = pkg.name.split(':')[0]
            # ensure name has :source tacked on end
            name = recipefile + ':source'
            recipefile += '.recipe'
            use.resetUsed()
            loader = recipe.recipeLoaderFromSourceComponent(name, recipefile, 
                                    self.cfg, self.repos, pkg.versionStr, 
                                    label=label)
            pkg.usedFlags = use.getUsed()
            recipeClass = loader[0].getRecipe()
            if not recipeClass.name.startswith('group-'):
                recipeObj = recipeClass(self.cfg, lcache, srcdirs) 
                recipeObj.setup()
                # one recipe can create several packages -- 
                # get a list of them here
                # XXX should probably also get components, 
                # and check components
                for package in recipeObj.packages:
                    if not package in self.packages:
                        self.packages[package] = []
                    self.packages[package].append(pkg)
                l = self.recipes.get(recipeClass.name, [])
                l.append(pkg)
                self.recipes[recipeClass.name] = l
            # we need to keep the loaders around so that they do not
            # get garbage collected -- their references are needed 
            # later!!!
            pkg.recipeClass = recipeClass
            self._loaders.append(loader)
        except recipe.RecipeFileError, e:
            raise
        else:
                    return recipeClass

    def getInstalledPkgs(self):
        matches = {}
        unmatched = {}
        for name,pkgs in self.packages.iteritems():
            for pkg in pkgs:
                if pkg not in unmatched:
                    unmatched[pkg] = []
                unmatched[pkg].append(name)

        db = database.Database(self.cfg.root, self.cfg.dbPath)
        for troveName in db.iterAllTroveNames():
            if troveName not in self.packages:
                continue
            for version in  db.getTroveVersionList(troveName):
                for trove in db.findTrove(troveName, version.asString()):

                    dbpkg = PkgId(troveName, trove.getVersion(), trove.getFlavor(), justName=True)
                    for pkg in self.packages[dbpkg.name]:
                    # convert dbpkg version to source version by removing
                    # buildCount
                    #
                        v = dbpkg.version.getSourceBranch()
                        pv = pkg.version.getSourceBranch()
                        v.trailingVersion().buildCount = None
                        if pv == v or pkg.name == 'icecream':
                            if pkg not in matches:
                                matches[pkg] = []
                            matches[pkg].append((dbpkg, troveName))
                            try:
                                del unmatched[pkg]
                            except KeyError:
                                pass
        return (matches, unmatched)

    def getMatchedChangeSets(self, changesetpath, filterDict={}):
        """ Try to match the changesets in changesetpath against the 
            desired troves 
            Successful changesets must match:
            1. Name 
            2. Label
            3. Version (this may have been grabbed from repository
                        if not specified in control file)
            4. Source version
            Potentially (if specified):
            5. Use/Flag flavor 5. build count
        """
        matches = {}
        unmatched = {}
        for name,pkgs in self.packages.iteritems():
            for pkg in pkgs:
                if filterDict and pkg.name not in filterDict:
                    continue
                if pkg not in unmatched:
                    unmatched[pkg] = []
                unmatched[pkg].append(name)
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
                cspkg = PkgId(name, version, flavor, justName=True)
                if cspkg.name in self.packages:
                    for pkg in self.packages[cspkg.name]:
                    # convert cspkg version to source version by removing
                    # buildCount
                        v = cspkg.version.getSourceBranch()
                        pv = pkg.version.getSourceBranch()
                        v.trailingVersion().buildCount = None
                        # XXXXXXXXX big hack to deal with the fact that
                        # icecream version numbers are out of whack
                        if pv == v or pkg.name == 'icecream':
                            if pkg not in matches:
                                matches[pkg] = []
                            if pkg not in flavors:
                                flavors[pkg] = {}
                            if cspkg.flavor not in flavors[pkg]:
                                flavors[pkg][cspkg.flavor] = cspkg
                            else:
                                other = flavors[pkg][cspkg.flavor]
                                if other.version.trailingVersion().buildCount < \
                                    cspkg.version.trailingVersion().buildCount:
                                    matches[pkg].remove(other)
                                    flavors[pkg][cspkg.flavor] = cspkg
                                else:
                                    # if there is already a changeset with
                                    # this version and flavor but a later
                                    # build count, don't count this as a match
                                    continue
                            matches[pkg].append(cspkg)
                            pkg.cspkgs[cspkg] = True
                            cspkg.file = csfile
                            try:
                                del unmatched[pkg]
                            except KeyError:
                                pass

        return (matches, unmatched)

    def getDesiredCompiledVersion(self, pkg):
        pv = pkg.version.copy()
        versions = self.repos.getTroveVersionList(pkg.version.branch().label(), [pkg.name])
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

    def loadPackageReqs(self, pkg):
        self.loadControlFile(loadRecipes=False)
        self.getSources()
        deps = [pkg]
        allDeps = {}
        allDeps[pkg] = True
        while deps:
            dep = deps.pop()
            for depPkg in self.sources[dep]:
                recipeClass = self.loadRecipe(depPkg)
                for newDep in recipeClass.buildRequires:
                    baseDep = newDep.split(':')[0]
                    if baseDep not in allDeps:
                        allDeps[baseDep] = True
                        deps.append(baseDep)
        return allDeps
