
def thawPackage(pkgStr):
    id =  PkgId._hashcache.get(pkgstr, None)
    if id:
        return id
    else:
        (name, value, flavor) = pkgstr.split(',', 2)
    if flavor == '0':
        flavor = None
    PkgId.init(name, value, flavor, name = True)


class PkgId:
    _hashcache = {}
    def __init__(self, recipeClassOrStr, version, flavor, justName=False):
        if justName:
            self.name = recipeClassOrStr
        else:
            self.recipeClass = recipeClassOrStr
            self.name = self.recipeClass.name
        self.version = version
        self.versionStr = self.version.asString()
        if flavor:
            self.flavor = flavor
            flavorStr = self.flavor._freeze()
        else:
            self.flavor = None
            flavorStr = '0'
        self._repr = ','.join([self.name, self.versionStr.replace('/','#'), flavorStr])
        # don't hash if we weren't given the 
        if not justName:
            self._hashcache[self] = self

    def __repr__(self):
        return self._repr

    def __str__(self):
        return self._repr

    def __add__(self, other):
        """ Treat like a string for adding """
        return self._repr + other

    def __radd__(self, other):
        """ Treat like a string for adding """
        return other + self._repr
