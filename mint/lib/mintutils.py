#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

"""
General utilities for use in the rBuilder codebase.
"""

import logging
import inspect

from conary.lib import util

FORMATS = {
        'apache': ('[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s',
            '%a %b %d %T %Y'),
        'console': ('%(levelname)s: %(message)s', None),
        'file': ('%(asctime)s %(levelname)s %(name)s : %(message)s', None),
        }


def setupLogging(logPath=None, consoleLevel=logging.WARNING,
        consoleFormat='console', fileLevel=logging.INFO, fileFormat='file',
        logger=''):

    logger = logging.getLogger(logger)
    logger.handlers = []
    logger.propagate = False
    level = 100

    # Console handler
    if consoleLevel is not None:
        if consoleFormat in FORMATS:
            consoleFormat = FORMATS[consoleFormat]
        consoleFormatter = logging.Formatter(*consoleFormat)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(consoleFormatter)
        consoleHandler.setLevel(consoleLevel)
        logger.addHandler(consoleHandler)
        level = min(level, consoleLevel)

    # File handler
    if logPath and fileLevel is not None:
        if fileFormat in FORMATS:
            fileFormat = FORMATS[fileFormat]
        logfileFormatter = logging.Formatter(*fileFormat)
        logfileHandler = logging.FileHandler(logPath)
        logfileHandler.setFormatter(logfileFormatter)
        logfileHandler.setLevel(fileLevel)
        logger.addHandler(logfileHandler)
        level = min(level, fileLevel)

    logger.setLevel(level)
    return logger


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
