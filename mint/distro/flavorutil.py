#
# Copyright (c) 2004 Specifix, Inc.
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
