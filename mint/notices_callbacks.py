# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import logging
import os
import time

from lxml.builder import E
from lxml import etree as ET

from mint import notices_store
from mint import packagecreator

log = logging.getLogger(__name__)

class NoticesCallback(packagecreator.callbacks.Callback):
    context = "builder"

    _lineSep = "<br/>"

    def __init__(self, cfg, userId):
        self.userId = userId
        self.store = notices_store.createStore(
            os.path.join(cfg.dataPath, "notices"), userId)

    def _notify(self, *args, **kw):
        raise NotImplementedError

    def _storeNotice(self, title, description, category, noticeDate):
        # Create the dummy notice so we can secure a guid
        try:
            notice = self.store.storeUser(self.context, "")
            guid = self.getNoticesUrl(notice.id)
            item = self.makeItem(title, description, category, noticeDate, guid)
            notice.content = item
            self.store.storeUser(None, notice)
        except Exception, e:
            log.exception('Exception creating notice: %s' % e)


    def getNoticesUrl(self, noticeId):
        return '/'.join(["/api/users", self.userId,
                      "notices/contexts", noticeId])

    @classmethod
    def makeItem(self, title, description, category, date, guid):
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

        node = E.category()
        node.text = category
        item.append(node)

        node = E.guid()
        node.text = guid
        item.append(node)

        return ET.tostring(item, xml_declaration = False,
            encoding = 'UTF-8')

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

setup_complete_message="""\
Welcome to rBuilder!

The menu on the left is the launch point for each task you can do here. Before you get started creating Appliances and deploying Systems, though, be sure to do the following:

(1) Add one or more Platforms to use as the base operating system for your appliances.

(2) If you're using rBuilder to deploy and manage systems in a virtual environment, add a Target with the configuration rBuilder needs for that environment.

For information on how to complete these first tasks and more, see the rBuilder Evaluation Guide at <a href="event:http://docs.rpath.com" target="_blank">docs.rpath.com</a>.
"""

class RbaSetupNoticeCallback(NoticesCallback):

    def __init__(self, *args, **kw):
        self.title = 'rBuilder setup complete'
        self.noticeDate = self.formatTime(time.time())
        self.description = setup_complete_message
        self.category = 'success'
        NoticesCallback.__init__(self, *args, **kw)

    def notify(self):
        self._storeNotice(self.title, self.description, self.category, self.noticeDate)

class PackageNoticesCallback(NoticesCallback):
    context = "builder"

    _labelTroveName = "Name"
    _labelTroveVersion = "Version"
    _labelTitle = "Package Build"

    def _notify(self, troveBuilder, job):
        troveBinaries = self.getJobBuiltTroves(troveBuilder, job)
        self.refreshCachedUpdates(troveBinaries)
        title, buildDate = self.getJobMeta(job, troveBinaries)
        description = self.getJobInformation(job, troveBinaries)

        category = (job.isFailed() and "error") or "success"
        self._storeNotice(title, description, category, buildDate)

    notify_committed = _notify
    notify_error = _notify

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
            status = "completed"
        title = "%s %s=%s %s" % (cls._labelTitle, trv[0],
                                 trv[1].trailingRevision(), status)
        buildDate = cls.formatRFC822Time(trv[1].timeStamps()[-1])
        return title, buildDate

    @classmethod
    def getJobInformation(cls, job, troveBinaries):
        if not troveBinaries:
            return "No packages built"
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
        return cls._lineSep.join(ret)

    @classmethod
    def refreshCachedUpdates(cls, troveBinaries):
        # Make sure django settings module is set before trying to import
        # anything from django.
        import mint.django_rest.rbuilder  # pyflakes=ignore

        from django import db
        db.close_connection()

        from mint.django_rest.rbuilder import service as rbuilder_service
        srv = rbuilder_service.BaseAuthService()
        srv._setMintAuth()
        for trvName, trvVersion in troveBinaries:
            trvLabel = trvVersion.trailingLabel().asString()
            srv.mgr.refreshCachedUpdates(trvName, trvLabel)

class ApplianceNoticesCallback(PackageNoticesCallback):
    _labelTitle = "Build"

class ImageNotices(PackageNoticesCallback):
    _template = "<b>%s:</b> %s"
    def notify_built(self, buildName, buildType, buildTime,
                     projectName, projectVersion, imageFiles):
        category = "success"
        return self._notify(category, buildName, buildType, buildTime,
            projectName, projectVersion, imageFiles)

    def notify_error(self, buildName, buildType, buildTime,
                     projectName, projectVersion, imageFiles):
        category = "error"
        # No images on error
        imageFiles = []
        return self._notify(category, buildName, buildType, buildTime,
            projectName, projectVersion, imageFiles)

    def _notify(self, category, buildName, buildType, buildTime,
                projectName, projectVersion, imageFiles):
        lines = []
        lines.append(self._template % ("Appliance Name", projectName))
        lines.append(self._template % ("Appliance Major Version", projectVersion))
        if buildType:
            lines.append(self._template % ("Image Type", buildType))
        for ent in imageFiles:
            lines.extend(self.getEntryDescription(ent))
        lines.append(self._template % ("Created On", self.formatTime(buildTime)))
        description = self._lineSep.join(lines)

        statesMap = dict(error = "failed to build", success = "built")
        st = statesMap[category]
        title = "Image `%s' %s (%s version %s)" % (buildName, st, projectName,
            projectVersion)
        buildDate = self.formatRFC822Time(buildTime)
        self._storeNotice(title, description, category, buildDate)

    @classmethod
    def getEntryDescription(cls, ent):
        fileName, downloadUrl = ent[:2]
        ret = []
        ret.append(cls._template % ("File Name", os.path.basename(fileName)))
        ret.append(cls._template % ("Download URL", '<a href="%s">%s</a>' %
            (downloadUrl, downloadUrl)))
        return ret

class AMIImageNotices(ImageNotices):
    @classmethod
    def getEntryDescription(cls, ent):
        amiId = ent
        ret = []
        ret.append(cls._template % ("AMI", amiId))
        return ret
