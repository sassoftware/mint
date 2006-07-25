#!/usr/bin/python
#
# Simple httpd access log parser for rBuilder
# Generates a report based on project downloads and individual file downloads.
#
import re
import sys
import os
import time

from conary.lib import util
from conary import dbstore

sys.excepthook = util.genExcepthook()

if len(sys.argv) < 3:
    print "Usage: logs.py <input file> <start date> <end date>"
    print "Dates are inclusive: YYYY-mm-dd format"
    sys.exit(1)

f = open(sys.argv[1])

startDate = time.mktime(time.strptime(sys.argv[2], "%Y-%m-%d"))
endDate = time.mktime(time.strptime(sys.argv[3], "%Y-%m-%d"))

logRx = re.compile("(.+) \- \- \[(.+)\] \"GET \/.*downloadImage/(\d+)/([\w\-]+)\-(\d*.*) HTTP.+\" (\d+) (\d+) \"(.*)\" \"(.*)\"")

downloads = {} # individual image downloads
projDls = {} # project downloads
isoDownloads = vmDownloads = rawhdDownloads = 0 # file type counts
first = last = None # first date parsed, last date parsed

for x in f.readlines():
    m = logRx.match(x)
    if m:
        g = m.groups()
        date = time.mktime(time.strptime(g[1].split(":")[0], "%d/%b/%Y"))

        if date >= startDate and date <= endDate:
            if not first:
                first = g[1]

            downloads.setdefault(g[2], 0)
            projDls.setdefault(g[3], 0)
            projDls[g[3]] += 1
            downloads[g[2]] += 1
            last = g[1]

# match file ids to full filenames
db = dbstore.connect("rbuilder@db1.cogent-dca.rpath.com/mint", driver = "mysql")
cu = db.cursor()

counts = []
for fileId, count in downloads.items():
    cu.execute("SELECT filename FROM ImageFiles WHERE fileId=?", fileId)
    r = cu.fetchone()
    if r:
        counts.append((count, os.path.basename(r[0])))
        if ".iso" in r[0]:
            isoDownloads += count
        elif "vmware" in r[0]:
            vmDownloads += count
        elif ".gz" in r[0]:
            rawhdDownloads += count
        else:
            print >> sys.stderr, "unmatched file type:", r[0]


print "SUMMARY:"
print "--------"
print "Report starts:     ", first[:11]
print "Report ends:       ", last[:11]
print "ISO downloads:     ", int(isoDownloads)
print "VMware downloads:  ", int(vmDownloads)
print "Raw HDD downloads: ", int(rawhdDownloads)
print "Total Downloads:   ", int((isoDownloads + vmDownloads + rawhdDownloads))
print '-------------------------------------------------------\n'

print 'TOP PROJECTS BY DOWNLOADS'
print '-------------------------'
for proj, count in sorted(projDls.items(), key = lambda x: x[1], reverse = True):
    cu.execute("SELECT name FROM Projects WHERE hostname=?", proj)
    r = cu.fetchone()
    if r and int(count) > 0:
        print "%-50s %4d" % (r[0][:50], count)
print '-------------------------------------------------------\n'

print 'TOP DOWNLOADS BY FILE'
print '---------------------'
for count, file in sorted(counts, reverse = True):
    if int(count) > 0:
        print "%-50s %4d" % (file, count)
