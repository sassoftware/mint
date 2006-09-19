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
logRxS3 = re.compile("(.+) \- \- \[(.+)\] \"GET \/.*downloadImage\?fileId\=(\d+) HTTP.+\" (\d+) (\d+) \"(.*)\" \"(.*)\"")

# match file ids to full filenames
db = dbstore.connect("rbuilder@db2.cogent-dca.rpath.com/mint", driver = "mysql")
cu = db.cursor()

downloads = {} # individual image downloads
projDls = {} # project downloads
isoDownloads = vmDownloads = rawhdDownloads = 0 # file type counts
first = last = None # first date parsed, last date parsed

for x in f.readlines():
    m = logRx.match(x)
    m2 = logRxS3.match(x)
    if m or m2:
        if m:
	    g = m.groups()
            fileId = g[2]
        elif m2:
	    g = m2.groups()
	    fileId = g[2]

        date = time.mktime(time.strptime(g[1].split(":")[0], "%d/%b/%Y"))
        if date >= startDate and date <= endDate:

	    cu.execute("""select hostname from projects, builds, buildfiles 
		where projects.projectid=builds.projectid 
		and builds.buildid=buildfiles.buildid and buildfiles.fileid=?""", fileId)
    
	    r = cu.fetchone()
	    if not r: # skip deleted images
		continue
	    hostname = r[0]

            if not first:
                first = g[1]
            downloads.setdefault(fileId, 0)
            projDls.setdefault(hostname, 0)
            downloads[fileId] += 1
            projDls[hostname] += 1
            last = g[1]

counts = []
for fileId, count in downloads.items():
    cu.execute("""SELECT u.url 
                      FROM buildfiles bf
                           JOIN buildfilesurlsmap bffu
                             USING (fileId)
                           JOIN filesurls u
                             USING (urlId)
                      WHERE bf.fileId = ? ORDER BY bf.fileId""", fileId)

    r = cu.fetchone()
    if r:
        counts.append((count, os.path.basename(r[0]), int(fileId)))
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
for count, file, fileId in sorted(counts, reverse = True):
    if int(count) > 0:
        print "%-50s %4d (fileId: %d) " % (file.split("%2F")[-1], count, fileId )
