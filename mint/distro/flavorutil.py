#
# Copyright (c) 2004-2005 Specifix, Inc.
# All rights reserved.

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
                for flag, sense in dep.flags.iteritems():
                    if sense in (deps.FLAG_SENSE_REQUIRED,
                                 deps.FLAG_SENSE_PREFERRED):
                         value = True
                    else:
                         value = False
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
    return [ x for x in LocalFlags._iterAll()]

def setLocalFlags(flags):
    """ Make the given local flags exist.  """
    for flag in flags:
        LocalFlags.__setattr__(flag._name, flag._get())

def resetLocalFlags():
    """ Delete all created local flags. """
    LocalFlags._clear()


def overrideFlavor(oldFlavor, newFlavor):
        flavor = oldFlavor.copy()
        if (deps.DEP_CLASS_IS in flavor.getDepClasses()
            and deps.DEP_CLASS_IS in newFlavor.getDepClasses()):
            del flavor.members[deps.DEP_CLASS_IS]
        flavor.union(newFlavor, mergeType=deps.DEP_MERGE_TYPE_OVERRIDE)
        return flavor

def parseTrove(trove):
    trove = trove.split(',', 2)
    if len(trove) == 1:
        trove.extend((None, None))
    elif len(trove) == 2:
        trove.append(None)
    if trove[1]:
        version =  trove[1].strip().lower()
        if not version or version == 'none':
            trove[1] = None
    else:
        trove[1] = None
    if trove[2]:
        flavor = trove[2].strip()
        if flavor:
            parsedFlavor = deps.parseFlavor(flavor)
            if not parsedFlavor:
                raise RuntimeError, '%s didnt parse as a flavor' % flavor
            trove[2] = parsedFlavor
        else:
            trove[2] = None
    return trove


