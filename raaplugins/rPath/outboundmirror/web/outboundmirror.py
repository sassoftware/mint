# Copyright (c) 2005-2007 rPath, Inc
# All rights reserved

from gettext import gettext as _

from raa.modules.raawebplugin import rAAWebPlugin
import raa
from raa.lib import repeatschedules
import cherrypy
import random
from datetime import datetime
import time
from raa.db import database, schedule
import math
import raa.web

class OutboundMirror(rAAWebPlugin):
    '''
    Schedule outbound mirroring
    '''
    displayName = _("Schedule Outbound Mirroring")

    @raa.web.expose(template="rPath.outboundmirror.index")
    def index(self):
        ret = {}
        scheds = repeatschedules.getCurrentRepeatingSchedules(self.taskId)
        if len(scheds) == 1:
            enabled = True
            ret['schedule'] = repeatschedules.getWidgetValuesFromSchedule(scheds.values()[0])
        else:
            enabled = False
            ret['schedule'] = dict(checkFreq = "Weekly", timeHour=23, timeDay=0, timeDayMonth=1)

        ret.update(enabled=enabled)
        return ret

    @raa.web.expose(allow_json=True)
    def prefsSave(self, enabled, checkFreq, timeHour, timeDay, timeDayMonth):
        enabled = True and (enabled == 1 or enabled == '1')
        sched = self.savePrefs(
            enabled, checkFreq, timeHour, timeDay, timeDayMonth)

        if not sched:
            message = "Outbound mirroring is not regularly scheduled."
        else:
            message = "Outbound mirroring has been regularly scheduled to occur " + str(sched)
        return dict(message=message)

    def savePrefs(self, enabled, checkFreq, timeHour, timeDay, timeDayMonth):
        assert checkFreq.lower() in ("daily", "weekly", "monthly"), \
            "Unrecognized frequency value: '%s'." % (checkFreq)
        checkFreq = checkFreq.lower()
        assert int(timeHour) in range(0, 24), "Invalid hour: '%s'." % (timeHour)
        assert int(timeDay) in range(0, 7), "Invalid day: '%s'." % (timeDay)
        assert int(timeDayMonth) in range(1, 29), \
            "Invalid day of the month: '%s'." % (timeDayMonth)

        repeatings = repeatschedules.getCurrentRepeatingSchedules(self.taskId)

        if 1 <= len(repeatings):
            for schedId in repeatings.keys():
                # If we have a repeating schedule, then invalidate it.
                self.unschedule(schedId)

        # Add a new schedule that contains the given parameters.
        if not enabled:
            # Well, we're not checking at all, so just return.
            raa.web.getWebRoot().schedule.db.commit()
            return None

        # Get hour and random minute.
        hour = int(timeHour)
        minute = random.randint(0, 59)

        # Get the frequency and create the schedule.
        starttuple = datetime.now().timetuple()
        startlist = reduce(lambda x, y: x + [y], starttuple, [])
        startlist[3] = hour
        startlist[4] = minute
        start = time.mktime(startlist)

        # If the start time is before now, then set it to the next day.
        if start < time.time():
            startlist[2] += 1
            start = time.mktime(startlist)

        if "daily" == checkFreq:
            sched = schedule.ScheduleInterval(
                start, None, 1, schedule.ScheduleInterval.INTERVAL_DAYS)
        elif "weekly" == checkFreq:
            day = schedule.ScheduleWeekly.listDayVars[int(timeDay)]
            sched = schedule.ScheduleWeekly(start, None, daysOfTheWeek=day)
        elif "monthly" == checkFreq:
            sched = schedule.ScheduleMonthlyAbsolute(
                start, None, day=int(timeDayMonth))

        # Schedule this.
        schedId = self.schedule(sched, commit=False)
        raa.web.getWebRoot().schedule.db.commit()

        return sched

    @raa.web.expose(allow_json=True)
    def mirrorNow(self):
        schedId = self.schedule(schedule.ScheduleOnce())
        return dict(schedId=schedId)

    @raa.web.expose(allow_json=True)
    def checkMirrorStatus(self):
        if raa.web.getWebRoot().execution.getUnfinishedSchedules(types=schedule.typesValid, taskId=self.taskId):
            return dict(mirroring=True)
        else:
            return dict(mirroring=False)
