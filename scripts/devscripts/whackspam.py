from conary.lib import util
import pickle
import os
import epdb
import sys

sys.excepthook = util.genExcepthook()

listsDir = '/var/mailman/lists/'

for d in os.listdir(listsDir):
    request = os.path.join(listsDir, d, 'request.pck')
    if os.path.exists(request):
        f = pickle.load(open(request))

        for x in f.keys():
            if x == 'version':
                continue

            data = f[x][1]
            if data[3] == 'Post by non-member to a members-only list' and data[1] != 'rbuilder@rpath.com':
                print "deleting message from %s" % data[1]
                if os.path.exists('/var/mailman/data/' + data[4]):
                    os.unlink('/var/mailman/data/' + data[4])
                del f[x]
        pickle.dump(f, open(request, 'w'))
