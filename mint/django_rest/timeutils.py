#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import datetime
from dateutil import tz

class Datetime(object):
    TZUTC = tz.tzutc()

    @classmethod
    def fromtimestamp(cls, timestamp, tz=None):
        """
        Return a datetime object extracted from the UNIX timestamp.
        The timezone defaults to UTC (you don't want to change that).
        """
        if tz is None:
            tz = cls.TZUTC
        return datetime.datetime.fromtimestamp(float(timestamp), tz)

    @classmethod
    def now(cls):
        """
        Return current time
        """
        return datetime.datetime.now(cls.TZUTC)

TZUTC = Datetime.TZUTC
fromtimestamp = Datetime.fromtimestamp
now = Datetime.now
timedelta = datetime.timedelta
