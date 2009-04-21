#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

"""
General utilities for use in the rBuilder codebase.
"""

import logging


def setupLogging(logPath=None, consoleLevel=logging.WARNING,
        fileLevel=logging.INFO, logger=''):

    logger = logging.getLogger(logger)
    level = 100

    # Console handler
    if consoleLevel is not None:
        consoleFormatter = logging.Formatter('%(levelname)s: %(message)s')
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(consoleFormatter)
        consoleHandler.setLevel(consoleLevel)
        logger.addHandler(consoleHandler)
        level = min(level, consoleLevel)

    # File handler
    if logPath and fileLevel is not None:
        logfileFormatter = logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s : %(message)s')
        logfileHandler = logging.FileHandler(logPath)
        logfileHandler.setFormatter(logfileFormatter)
        logfileHandler.setLevel(fileLevel)
        logger.addHandler(logfileHandler)
        level = min(level, fileLevel)

    logger.setLevel(level)
    return logger
