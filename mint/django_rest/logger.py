#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
import sys

def getlogger():
    logger = logging.getLogger()
    
    logger.handlers = []

    hdlr = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S+00:00') 
    
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.NOTSET)

    return logger

def debug(msg):
    logger = getlogger()
    logger.debug(msg)
    
def info(msg):
    logger = getlogger()
    logger.info(msg)
    
def error(msg):
    logger = getlogger()
    logger.error(msg)

def exception(msg):
    logger = getlogger()
    logger.exception(msg)
