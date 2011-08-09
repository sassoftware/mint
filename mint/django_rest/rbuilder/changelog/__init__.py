#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#
# pyflakes=ignore-file

# singalhandler has to get imported somewhere so that the signal handling gets
# connected in django.  
from mint.django_rest.rbuilder.changelog import signalhandler
