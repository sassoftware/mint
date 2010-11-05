#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#


PREFIX = 'com.rpath.rbuilder.image_gen'

# Windows Image Generator
WIG_PREFIX          = PREFIX + '.wig'
WIG_JOB             = WIG_PREFIX
WIG_TASK            = WIG_PREFIX

WIG_JOB_QUEUED      = 100
WIG_JOB_RUNNING     = 101
WIG_JOB_DONE        = 200
WIG_JOB_FAILED      = 400
