#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

table = log_error = config_tree = server_root = SERVER_RETURN = parse_qs = \
        parse_qsl = None


# This snippet searches mod_python's apache.py for trivial references to
# _apache, and attempts to automatically stub them into this module.
#
# It is a delicious hack. You must eat it.
#
import sys, os.path, re
isconst = re.compile('^(\S+)\s*=\s*_apache\.\\1')
for x in sys.path:
    y = os.path.join(x, 'mod_python', 'apache.py')
    if os.path.exists(y):
        f = open(y)
        for line in f:
            m = isconst.search(line)
            if m:
                setattr(sys.modules[__name__], m.group(1), None)

mpm_query = lambda *P, **K: None
