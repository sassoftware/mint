# flavor manipulations
#
from deps import deps
from build import use
from build.use import Arch, Use, LocalFlags

def getFlavorUseFlags(flavor):
    """ Convert a flavor-as-dependency set to flavor-as-use-flags.
    """
    useFlags = {'Flags' : {}, 'Use' : {}}
    if flavor is None:
        return useFlags
    for depGroup in flavor.getDepClasses().values():
        if isinstance(depGroup, deps.UseDependency):
            for dep in depGroup.getDeps():
                for flag in dep.flags:
                    value = True
                    # we don't care about ~ mark,
                    # just whether the flag should be true of false
                    if flag[0] == '~':
                        flag = flag[1:]
                    if flag[0] == '!':
                        value = False
                        flag = flag[1:]
                    parts = flag.split('.',1)
                    if len(parts) == 1:
                        useFlags['Use'][flag] = value
                    else:
                        name = parts[0]
                        flag = parts[1]
                        if name not in useFlags['Flags']:
                            useFlags['Flags'][name] = {}
                        useFlags['Flags'][name][flag] = value
    return useFlags

def getLocalFlags():
    """ Get the local flags that are currently set, so that the flags 
        created can be reset. """
    flags = {}
    for flag in LocalFlags:
        flags[flag] = LocalFlags[flag]
    return flags

def setLocalFlags(flags):
    """ Make the given local flags exist.  """
    freeze = LocalFlags._frozen
    if freeze:
        LocalFlags._thaw()
    for flag in flags:
        LocalFlags.__getattr__(flag)
        LocalFlags[flag] = flags[flag]
    if freeze:
        LocalFlags._freeze()

def resetLocalFlags():
    """ Delete all created local flags. """
    freeze = LocalFlags._frozen
    # local flags should be unfrozen for the next use
    LocalFlags._thaw()
    for flag in LocalFlags.keys():
        del LocalFlags[flag]
    return

def setFlavor(flavor, recipeName):
    """ Given a flavor-as-dependency set, set the related Use flags.
        Returns the old flavor as Use flags for resetting the flavor
        later.
    """
    if flavor is None:
        return None
    oldFlags = { 'Use' : {}, 'Arch' : {}, 'Flags' : {} }
    useFlags = getFlavorUseFlags(flavor)
    for flag, value in useFlags['Use'].iteritems():
        print "Setting Use.%s %s" % (flag, value)
        if flag in Use:
            oldValue = Use[flag]
        else:
            oldValue = None
        if Use._frozen:
            Use._thaw()
            Use._override(flag, value)
            Use._freeze()
        else:
            Use._override(flag, value)
        oldFlags['Use'][flag] = oldValue

    if recipeName in useFlags['Flags']:
        for flag,value in useFlags['Flags'][recipeName].iteritems():
            if flag in LocalFlags:
                oldValue = LocalFlags[flag]
            else:
                oldValue = None
            print "Setting Flags.%s %s" % (flag, value)
            if LocalFlags._frozen:
                LocalFlags._thaw()
                LocalFlags._override(flag, value)
                LocalFlags._freeze()
            else:
                LocalFlags._override(flag, value)
            oldFlags['Flags'][flag] = oldValue
    return oldFlags

def resetFlavor(oldFlags):
    """ Takes the value returned from setFlavor and resets the 
        Use flags to their previous values
    """
    # assumes that oldFlags was returned from setFlavor
    if oldFlags is None:
        return None
    for flagset in (Use, LocalFlags):
        flagset._overrides = {}
        freeze = flagset._frozen
        if freeze:
            flagset._thaw()
        oldSetFlags = oldFlags[flagset._name]
        for flag in oldSetFlags:
            value = oldSetFlags[flag]
            if value:
                flagset[flag]._set(value)
            else:
                if flag in flagset:
                    del flagset[flag]
        if freeze:
            flagset._freeze()

def nullFlagSet():
        return use.Flag(name='__GLOBAL__').asSet()
