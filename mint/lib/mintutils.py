#
# Copyright (c) 2011 rPath, Inc.
#

"""
General utilities for use in the rBuilder codebase.
"""

import logging
import inspect
import itertools
import re
import time

from conary.lib import digestlib
from conary.lib import util
from conary.repository.netrepos import cache


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

class Transformations(object):
    RE_StringToCamelCase = re.compile('(.)_([a-z])')
    RE_StringToUnderscore_1 = re.compile('(.)([A-Z][a-z]+)')
    RE_StringToUnderscore_2 = re.compile('([a-z0-9])([A-Z])')
    S_Group = r'\1_\2'

    @classmethod
    def strToCamelCase(cls, name):
        return cls.RE_StringToCamelCase.sub(cls._repl, name)

    @classmethod
    def nodeToCamelCase(cls, node):
        for name in cls._FieldNames:
            v = getattr(node, name, None)
            if v is not None:
                setattr(node, name, cls.strToCamelCase(v))
        for child in node.childNodes:
            cls.nodeToCamelCase(child)

    @classmethod
    def strToUnderscore(cls, name):
        s1 = cls.RE_StringToUnderscore_1.sub(cls.S_Group, name)
        return cls.RE_StringToUnderscore_2.sub(cls.S_Group, s1).lower()

    @classmethod
    def nodeToUnderscore(cls, node):
        for name in cls._FieldNames:
            v = getattr(node, name, None)
            if v is not None:
                setattr(node, name, cls.strToUnderscore(v))
        for child in node.childNodes:
            cls.nodeToUnderscore(child)

    @classmethod
    def _repl(cls, m):
        return m.group()[:-2] + m.group()[-1].upper()

    _FieldNames = ['tagName', 'nodeName']


class CacheWrapper(object):

    def __init__(self, cacheServer, timeout=0.0):
        if cacheServer:
            self.cache = cache.getCache(cacheServer)
        else:
            self.cache = cache.EmptyCache()
        self.timeout = timeout

    def _keys(self, items, args, kwargs):
        if kwargs is None:
            kwargs = ()
        else:
            kwargs = tuple(sorted(kwargs.items()))
        common = digestlib.sha1(str(args + kwargs)).digest()
        return [digestlib.sha1(common + str(x)).hexdigest() for x in items]

    def coalesce(self, keyPrefix, innerFunc, items, *args, **kwargs):
        """Memoize a function call using the cache.

        The function should take a list of things as the first argument, and
        return a parallel list of results.
        """
        # Get from cache
        keys = self._keys(items, args, kwargs)
        cachedDict = self.cache.get_multi(keys, key_prefix=keyPrefix)
        allResults = [cachedDict.get(x) for x in keys]

        # Get missed results from inner function and store
        needed = [(i, x) for (i, x) in enumerate(items)
                if keys[i] not in cachedDict]
        if needed:
            newResults = innerFunc([x[1] for x in needed], *args, **kwargs)
            cacheUpdates = {}
            for (i, x), result in itertools.izip(needed, newResults):
                allResults[i] = result
                cacheUpdates[keys[i]] = result
            self.cache.set_multi(cacheUpdates,
                    key_prefix=keyPrefix,
                    time=self.timeout,
                    )
        return allResults
