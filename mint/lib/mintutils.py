#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

"""
General utilities for use in the rBuilder codebase.
"""

import logging
import inspect
import time

from conary.lib import util


def setupLogging(logPath=None, consoleLevel=logging.WARNING,
        consoleFormat='console', fileLevel=logging.INFO, fileFormat='file',
        logger=''):

    logger = logging.getLogger(logger)
    logger.handlers = []
    logger.propagate = False
    level = 100

    # Console handler
    if consoleLevel is not None:
        consoleFormatter = _getFormatter(consoleFormat)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(consoleFormatter)
        consoleHandler.setLevel(consoleLevel)
        logger.addHandler(consoleHandler)
        level = min(level, consoleLevel)

    # File handler
    if logPath and fileLevel is not None:
        logfileFormatter = _getFormatter(fileFormat)
        logfileHandler = logging.FileHandler(logPath)
        logfileHandler.setFormatter(logfileFormatter)
        logfileHandler.setLevel(fileLevel)
        logger.addHandler(logfileHandler)
        level = min(level, fileLevel)

    logger.setLevel(level)
    return logger


class ISOFormatter(logging.Formatter):
    """
    Logging formatter for ISO 8601 timestamps with milliseconds.
    """

    def formatTime(self, record, datefmt=None):
        timetup = time.localtime(record.created)
        if timetup.tm_isdst:
            tz_seconds = time.altzone
        else:
            tz_seconds = time.timezone
        tz_offset = abs(tz_seconds / 60)
        tz_sign = (time.timezone < 0 and '+' or '-')

        timestampPart = time.strftime('%F %T', timetup)
        return '%s.%03d%s%02d%02d' % (timestampPart, record.msecs, tz_sign,
                tz_offset / 60, tz_offset % 60)


FORMATS = {
        'console': '%(levelname)s: %(message)s',
        'apache': ISOFormatter(
            '[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s'),
        'file': ISOFormatter(
            '%(asctime)s %(levelname)s %(name)s : %(message)s'),
        }


def _getFormatter(format):
    """
    Logging formats can be:
     * A string - the record format
     * A tuple - the record format and the timestamp format
     * An instance of Formatter or a subclass
     * A string selecting a tuple or instance from FORMATS
    """
    if format in FORMATS:
        format = FORMATS[format]
    if isinstance(format, basestring):
        format = (format,)
    if isinstance(format, logging.Formatter):
        return format
    return logging.Formatter(*format)


class ArgFiller(object):
    """
    Tool for turning a function's positional + keyword arguments into a
    simple list as if positional.
    """
    _NO_DEFAULT = []

    def __init__(self, name, names, defaults):
        if not defaults:
            defaults = ()
        self.name = name
        self.names = tuple(names)
        self.numMandatory = len(names) - len(defaults)
        self.defaults = ((self._NO_DEFAULT,) * self.numMandatory) + defaults

    @classmethod
    def fromFunc(cls, func):
        names, posName, kwName, defaults = inspect.getargspec(func)
        assert not posName and not kwName # not supported [yet]
        return cls(func.func_name, names, defaults)

    def fill(self, args, kwargs):
        total = len(args) + len(kwargs)
        if total < self.numMandatory:
            raise TypeError("Got %d arguments but expected at least %d "
                    "to method %s" % (total, self.numMandatory, self.name))
        if len(args) + len(kwargs) > len(self.names):
            raise TypeError("Got %d arguments but expected no more than "
                    "%d to method %s" % (total, len(self.names), self.name))

        newArgs = []
        for n, (name, default) in enumerate(zip(self.names, self.defaults)):
            if n < len(args):
                # Input as positional
                newArgs.append(args[n])
                if name in kwargs:
                    raise TypeError("Got two values for argument %s to "
                            "method %s" % (name, self.name))
            elif name in kwargs:
                # Input as keyword
                newArgs.append(kwargs.pop(name))
            elif default is not self._NO_DEFAULT:
                # Not input but default available
                newArgs.append(default)
            else:
                # Missing
                raise TypeError("Missing argument %s to method %s"
                        % (name, self.name))

        if kwargs:
            raise TypeError("Got unexpected argument %s to method %s"
                    % (sorted(kwargs)[0], self.name))

        return tuple(newArgs)

def urlAddAuth(url, username, password):
    urlArr = list(util.urlSplit(url))
    if username is not None:
        urlArr[1] = username
    if password is not None:
        urlArr[2] = password
    return util.urlUnsplit(urlArr)
