#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

NS_JOB_COMMIT_SOURCE = 'com.rpath.rbuilder.rmake.packages.commit'
NS_TASK_COMMIT_SOURCE = NS_JOB_COMMIT_SOURCE

NS_JOB_DOWNLOAD_FILES = 'com.rpath.rbuilder.rmake.packages.download-files'
NS_TASK_DOWNLOAD_FILES = NS_JOB_DOWNLOAD_FILES

NS_JOB_BUILD_SOURCE = 'com.rpath.rbuilder.rmake.packages.build'
NS_TASK_BUILD_SOURCE = NS_JOB_BUILD_SOURCE

class Codes(object):
    # 100
    MSG_START = 101
    MSG_STATUS = 102
    MSG_GENERIC = 110

    # 200
    OK = 200
    OK_1 = 201
    # 400
    ERR_AUTHENTICATION = 401
    ERR_NOT_FOUND = 404
    ERR_METHOD_NOT_ALLOWED = 405
    ERR_ZONE_MISSING = 420
    ERR_BAD_ARGS = 421
    ERR_GENERIC = 430
