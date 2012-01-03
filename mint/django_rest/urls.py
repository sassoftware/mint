#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.conf.urls.defaults import url, patterns, include
import v1

urlpatterns = patterns('',
    r'^api/v1/', include('v1'),
  # '^api/v2/', include('urls.v2'),
)

