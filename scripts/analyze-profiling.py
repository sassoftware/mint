import os
import os.path
import time

calldict = {}
firstline = True

if not os.path.exists('/var/logs/rbuilder/profiling'):
    print "Profiling data file does not exist."
    os.exit(1)

f = file('/var/logs/rbuilder/profiling','r')

for l in f:
    if l.startswith('#'):
        continue
    l = l.rstrip('\n')
    if l.find('<<') >= 0:
        (t, lavg, pid, nc, tag, name, elapsed) = l.split('|')
        tag = tag.strip('<')
        name = name.strip('-+')
        elapsed = float(int(elapsed) / 1000.0)
        if firstline:
            firstline = False
            starttime = time.gmtime(float(t))
        else:
            endtime = time.gmtime(float(t))
        key = tag + ':' + name
        if key in calldict:
            (min, max, sum, count) = calldict[key]
            count += 1
            sum += elapsed
            if elapsed < min:
                min = elapsed
            if elapsed > max:
                max = elapsed
            calldict[key] = (min, max, sum, count)
        else:
            calldict[key] = (elapsed, elapsed, elapsed, 1)

f.close()

# print report
calllist = calldict.items()
calllist.sort(key = lambda x: x[1][3], reverse = True)
print "*** Profiling Data ***\n"
print "Starting time: %s UTC\nEnding time:   %s UTC\n" %\
    (time.asctime(starttime), time.asctime(endtime))
print "(NOTE: All times in seconds)\n"
print "%9s %9s %7s %7s   %s" % ("Count", "Sum", "Avg", "Max", "Item")
print "%9s %9s %7s %7s   %s" % ("-------", "-------", "-------", "-------", "-------------")
for i in calllist:
    print "%9d %9.2f %7.2f %7.2f   %s" % (i[1][3], i[1][2], (i[1][2] / i[1][3]), i[1][1], i[0])

