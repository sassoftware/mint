#
# Copyright (c) 2011 rPath, Inc.
#


PREFIX = 'com.rpath.rbuilder.image_gen'

# Windows Image Generator
WIG_PREFIX          = PREFIX + '.wig'
WIG_JOB             = WIG_PREFIX
WIG_TASK            = WIG_PREFIX

WIG_JOB_QUEUED      = 100
WIG_JOB_FETCHING    = 101
WIG_JOB_SENDING     = 102
WIG_JOB_RUNNING     = 103
WIG_JOB_CONVERTING  = 104
WIG_JOB_UPLOADING   = 105
WIG_JOB_DONE        = 200
WIG_JOB_FAILED      = 400

# Image Upload
IUP_PREFIX          = PREFIX + '.upload'
IUP_JOB             = IUP_PREFIX
IUP_TASK            = IUP_PREFIX

IUP_JOB_QUEUED      = 100
IUP_JOB_UPLOADING   = 101
IUP_JOB_PACKAGING   = 102
IUP_JOB_DONE        = 200
IUP_JOB_FAILED      = 400
