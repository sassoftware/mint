#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import logging
import sys
from django.conf import settings

def getlogger():
    logger = logging.getLogger()
    hdlr = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S') 
    
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.NOTSET)

    return logger

def debug(msg):
    logger = getlogger()
    logger.debug(msg)
    
def error(msg):
    logger = getlogger()
    logger.error(msg)

def exception(msg):
    logger = getlogger()
    logger.exception(msg)
