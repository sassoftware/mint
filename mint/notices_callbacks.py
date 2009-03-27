#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os
import time

from lxml.builder import E
from lxml import etree as ET

from mint import notices_store
from mint import packagecreator

class PackageNoticesCallback(packagecreator.callbacks.Callback):
    context = "builder"

    _labelTroveName = "Trove Name"
    _labelTroveVersion = "Trove Version"
    _labelTitle = "Package"

    def __init__(self, cfg, userId):
        self.userId = userId
        self.store = notices_store.createStore(
            os.path.join(cfg.dataPath, "notices"), userId)

    def notify_committed(self, troveBuilder, job):
        troveBinaries = self.getJobBuiltTroves(troveBuilder, job)
        title, buildDate = self.getJobMeta(job, troveBinaries)
        description = self.getJobInformation(job, troveBinaries)
        item = self.makeItem(title, description, buildDate, "empty")
        self.store.storeUser(self.context, item)

    notify_error = notify_committed

    @classmethod
    def makeItem(self, title, description, date, guid):
        item = E.item()
        node = E.title()
        node.text = title
        item.append(node)

        node = E.description()
        node.text = description
        item.append(node)

        node = E.date()
        node.text = date
        item.append(node)

        # We won't generate uuids for now
        #node = E.guid()
        #node.text = guid
        #item.append(node)

        return ET.tostring(item, xml_declaration = False,
            encoding = 'UTF-8')

    @classmethod
    def getJobBuiltTroves(cls, tb, job):
        if not job.getBuiltTroveList():
            # Re-fetch the job information to include troves
            job = tb.helper.getJob(job.jobId, withTroves = True)
        troveList = list(job.iterTroveList())
        builtTroves = job.getBuiltTroveList()
        troveSources = set(x[0].split(':', 1)[0] for x in troveList)
        mainBinaries = [ x for x in builtTroves if x[0] in troveSources ]
        if not mainBinaries:
            # Boggle, we have no binaries with the same name as the source; grab
            # the packages instead
            mainBinaries = [ x for x in builtTroves if ':' not in x[0] ]
        troveBinaries = set((x[0], x[1]) for x in mainBinaries)
        return sorted(troveBinaries)

    @classmethod
    def getJobMeta(cls, job, troveBinaries):
        if not troveBinaries:
            trv = job.iterTroveList().next()
        else:
            trv = troveBinaries[0]
        if job.isFailed():
            status = "failed"
        else:
            status = "built"
        title = "%s %s=%s %s" % (cls._labelTitle, trv[0],
                                 trv[1].trailingRevision(), status)
        buildDate = cls.formatRFC822Time(trv[1].timeStamps()[-1])
        return title, buildDate

    @classmethod
    def getJobInformation(cls, job, troveBinaries):
        if not troveBinaries:
            return "No troves built"
        template = "<b>%s:</b> %s"
        ret = []
        for trvName, trvVersion in troveBinaries:
            createdOn = trvVersion.timeStamps()[-1]
            ret.append(template % (cls._labelTroveName, trvName))
            ret.append(template % (cls._labelTroveVersion,
                "%s/%s" % (trvVersion.trailingLabel(), trvVersion.trailingRevision())))
        ret.append("")
        ret.append(template % ("Created On", cls.formatTime(createdOn)))
        ret.append(template % ("Duration", cls.formatSeconds(job.finish - job.start)))
        ret.append("")
        return '<br/>\n'.join(ret)

    @classmethod
    def formatTime(cls, tstamp):
        # set up timezone stuff
        if time.daylight:
            offset = -time.altzone
        else:
            offset = -time.timezone
        tzfmt = "%+03d:%02d" % (offset / 3600, (offset % 3600) / 30)
        s = time.strftime('%a %b %d %H:%M:%S %%s %Y', time.localtime(tstamp))
        s = s % 'UTC%s' % tzfmt
        return s

    @classmethod
    def formatRFC822Time(cls, tstamp):
        # set up timezone stuff
        if time.daylight:
            offset = -time.altzone
        else:
            offset = -time.timezone
        tzfmt = "%+03d%02d" % (offset / 3600, (offset % 3600) / 30)
        s = time.strftime('%d %b %Y %H:%M:%S %%s', time.localtime(tstamp))
        s = s % tzfmt
        return s

    @classmethod
    def formatSeconds(cls, secs):
        return "%02d:%02d:%02d" % (secs / 3600, (secs % 3600) / 60, secs % 60)

class ApplianceNoticesCallback(PackageNoticesCallback):
    _labelTitle = "Build"
