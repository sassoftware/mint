# Copyright (c) 2005-2007 rPath, Inc
# All rights reserved

from raa.modules.raawebplugin import rAAWebPlugin
import raa
from raa.lib import repeatschedules
import cherrypy
import random
from datetime import datetime
import time
from raa.db import database, schedule
import math

class OutboundMirror(rAAWebPlugin):
    '''
    Schedule outbound mirroring
    '''
    displayName = _("Schedule Outbound Mirroring")

    @raa.expose(template="rPath.outboundmirror.index")
    def index(self):
        scheds = repeatschedules.getCurrentRepeatingSchedules(self.taskId)
        if len(scheds) == 1:
            sched = scheds.values()[0]
            checkFreq = {
                    schedule.ScheduleWeekly.type: "Weekly",
                    schedule.ScheduleInterval.type: "Daily",
                    schedule.ScheduleMonthlyAbsolute.type: "Monthly",
                }[sched.type]
            if sched.unit == schedule.ScheduleInterval.INTERVAL_HOURS:
                checkFreq = 'Hourly'
                hours = sched.interval / 3600
            else:
                hours = '1'
            timetuple = datetime.fromtimestamp(sched.start)
            timeHour = timetuple.hour
            if schedule.ScheduleWeekly.type == sched.type:
                timeDay = int(math.log(sched.daysOfTheWeek, 2))
            else:
                timeDay = timetuple.weekday()
            timeDayMonth = sched.interval
            enabled = True
        else:
            enabled = False
            checkFreq = "Hourly"
            timeHour = "1"
            timeDay = "1"
            timeDayMonth = "1"
            hours = "1"

        return dict(enabled=enabled, checkFreq=checkFreq, timeHour=timeHour, timeDay=timeDay, timeDayMonth=timeDayMonth, hours=hours)

    @raa.expose(allow_json=True)
    def prefsSave(
        self, checkFreq, timeHour, timeDay, timeDayMonth, hours, status = 'disabled'):

        sched = self.savePrefs(
            checkFreq, timeHour, timeDay, timeDayMonth, hours, status == 'enabled')

        if not sched:
            message = "Outbound mirroring is not regularly scheduled."
        else:
            message = "Outbound mirroring has been regularly scheduled to occur " + str(sched)
        return dict(message=message)

    def savePrefs(self, checkFreq, timeHour, timeDay, timeDayMonth, hours, status):
        assert checkFreq.lower() in ("daily", "weekly", "monthly", 'hourly'), \
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
        if not status:
            # Well, we're not checking at all, so just return.
            cherrypy.root.schedule.db.commit()
            return None

        # Get hour and random minute.
        hour = int(timeHour)
        minute = random.randint(0, 59)

        # Get the frequency and create the schedule.
        starttuple = datetime.now().timetuple()
        startlist = reduce(lambda x, y: x + [y], starttuple, [])
        if checkFreq != 'hourly':
            startlist[3] = hour
        startlist[4] = minute
        start = time.mktime(startlist)

        # If the start time is before now, then set it to the next day.
        if start < time.time():
            if checkFreq == 'hourly':
                startlist[3] += 1
            else:
                startlist[2] += 1
            start = time.mktime(startlist)

        if "hourly" == checkFreq:
            sched = schedule.ScheduleInterval(
                start, None, int(hours), schedule.ScheduleInterval.INTERVAL_HOURS)
        elif "daily" == checkFreq:
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
        cherrypy.root.schedule.db.commit()

        return sched

    @raa.expose(allow_json=True)
    def mirrorNow(self):
        schedId = self.schedule(schedule.ScheduleOnce())
        return dict(schedId=schedId)

    @raa.expose(allow_json=True)
    def checkMirrorStatus(self):
        if cherrypy.root.execution.getUnfinishedSchedules(types=schedule.typesValid, taskId=self.taskId):
            return dict(mirroring=True)
        else:
            return dict(mirroring=False)
