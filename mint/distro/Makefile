#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#

python_files = __init__.py\
               controlfile.py\
               distribution.py\
               flavorutil.py\
               imagegen.py\
               installable_iso.py\
               iso.py\
               jobdaemon.py\
               jobstatus.py\
               profiletypes.py\
               live_cf_image.py\
               live_iso.py\
               pkgid.py

extra_dist = Makefile installable_iso.conf mklivecd

dist_files = $(python_files) $(extra_dist)

all: default-all

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../../Make.rules
