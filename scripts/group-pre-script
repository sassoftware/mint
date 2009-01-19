#!/bin/sh
#
# Copyright (c) 2008-2009 rPath, Inc.
# All rights reserved.
#
# This script is executed from the group before each update. It cleans
# up file conflicts and things that might need fixing before the
# actual contents are installed.
#
# NOTE: In the interests of avoiding cruft which no-one can explain 3
# years from now, all transitional migrations, workarounds, and anything
# that will not otherwise be self-explanatory in the future should be
# marked with a comment indicating when and for what version it was
# added as well as any relevant issue IDs.


# Delete old auto-generated filewall rules so the static ones can
# be installed.
#   -- 5.0 - 2009-01-19
if [ -f /etc/firewall ] \
    && grep -q "^## Firewall configuration managed by conary$"  /etc/firewall
then
    rm -f /etc/firewall
fi
