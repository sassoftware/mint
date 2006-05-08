#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#
"""A handful of functions useful inside kid templates."""

import time

def downloadTracker(cfg, url):
    if cfg.googleAnalyticsTracker:
        return {"onclick": "javascript:urchinTracker('%s');" % url}
    else:
        return {}

def injectVersion(version):
    parts = version.split('/')
    parts[-1] = str(time.time()) + ':' + parts[-1]
    return '/'.join(parts)
