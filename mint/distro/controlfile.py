# Here's what I need to be able to do:
# 1.  Grab the desired version info from control file
# 2.  Determine the correct source version for each desired verion - Update
#     desired version to include latest source version information 
# 3.  Determine if a changeset file fits the desired version
# 4.  Grab a matching version from the repository
from build import lookaside, recipe
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

    def loadControlFile(self):
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
        print "Loading Recipes..." 
        sys.stdout.flush()
        self.getSources()
        self.loadRecipes()

    def getSources(self):
        notfound = {}
        sources = {}
        flavor = None
        # XXX this might be faster if we tried to replicate findTrove behavior
        # e.g., if versionStrs are on the same label (90% of the time), we 
        # can just get leaves on label
        for (troveName, versionStr) in self.troves:
            # remove potential :devel, etc, components from the components, 
            # since we want to point to the source trove
            troveName = troveName.split(':', 1)[0]
            try: 
                sourceTroveName = troveName + ':source'
                sourceTroves = self.repos.findTrove(self.label, sourceTroveName, flavor, versionStr)
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
        recipes = {}
        keys = self.sources.keys()
        keys.sort()
        count = 0
        lcache = lookaside.RepositoryCache(self.repos)
        for source in keys:
            for p in self.sources[source]:
                try:
                    srcdirs = [ self.cfg.sourceSearchDir % { 'pkgname' : p.name }  ]
                    recipeClass = self.loadRecipe(p)
                    # XXX Use flags can be checked during the execution
                    # of actions, so it's no good to try to figure
                    # out which ones this package cares about after
                    # just calling setup
                    #use.track(True)
                    recipeObj = recipeClass(self.cfg, lcache, srcdirs) 
                    recipeObj.setup()
                    # one recipe can create several packages -- 
                    # get a list of them here
                    # XXX should probably also get components, 
                    # and check components
                    for package in recipeObj.packages:
                        if not package in self.packages:
                            self.packages[package] = []
                        self.packages[package].append(p)
                except recipe.RecipeFileError, e:
                    print str(e)
                    sys.exit(1)
                else:
                    p.recipeClass = recipeClass
                    l = recipes.get(recipeClass.name, [])
                    l.append(p)
                    recipes[recipeClass.name] = l
                    sys.stdout.write('%d: %s\n' % (count, p))
                    count = count + 1
                    sys.stdout.flush()
        sys.stdout.write('\nDone.\n')
        sys.stdout.flush()
        self.recipes = recipes

    def loadRecipe(self, pkg, label=None):
        recipefile = pkg.name.split(':')[0]
        # ensure name has :source tacked on end
        name = recipefile + ':source'
        recipefile += '.recipe'
        loader = recipe.recipeLoaderFromSourceComponent(name, recipefile, 
                                self.cfg, self.repos, pkg.versionStr, 
                                label=label)
        recipeClass = loader[0].getRecipe()
        # we need to keep the loaders around so that they do not
        # get garbage collected -- their references are needed 
        # later!!!
        self._loaders.append(loader)
        return recipeClass


    def getMatchedChangeSets(self, changesetpath):
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
        changesetNames =  [ x for x in os.listdir(changesetpath) if x.endswith('.ccs') ]
        for changesetName in changesetNames:
            cs = changeset.ChangeSetFromFile(os.path.join(changesetpath, changesetName))
            pkgs = cs.primaryTroveList
            for (name, version, flavor) in pkgs:
                cspkg = PkgId(name, version, flavor, justName=True)
                if cspkg.name in self.packages:
                    for pkg in self.packages[cspkg.name]:
                    # convert cspkg version to source version by removing
                    # buildCount
                        v = cspkg.version.copy()
                        v.trailingVersion().buildCount = None
                        if pkg.version == v:
                            if pkg not in matches:
                                matches[pkg] = []
                            matches[pkg].append((cspkg, changesetName))
                            if len(matches[pkg]) > 1:
                                raise TypeError, "We don't handle multiple changesets matching a package yet"
                                # when we do, we'll sort them so that the highest version #
                                # comes first

        return matches

    def getDesiredCompiledVersion(self, pkg):
        # XXX this is faking basically what cooking a group does.
        # do I really not want to keep info in a group and recompile it before building?
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

