#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

f = open('rmakeconstants.py', 'w')

print >>f, '''#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

class Constants(dict):
    def __getattribute__(self, item):
        try:
            return dict.__getattribute__(self, item)
        except AttributeError:
            return dict.__getitem__(self, item)

supportedApiVersions = (1,)
currentApi = 1

'''

from rmake.build.buildjob import jobStates
print >>f, 'buildjob = Constants(' + ',\n'.join(str(jobStates).split(',')) + ')'
print >>f

from rmake.build.buildtrove import troveStates
print >>f, 'buildtrove = Constants(' + ',\n'.join(str(troveStates).split(',')) + ')'
print >>f

