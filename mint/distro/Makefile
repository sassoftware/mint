#
# Copyright (c) 2004-2005 rpath, Inc.
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
               live_cf_image.py\
               live_iso.py\
	       netboot_image.py\
               pkgid.py\
	       stub_image.py

extra_dist = Makefile

dist_files = $(python_files) $(extra_dist)

all: default-all

install: install-subdirs pyfiles-install

dist: default-dist

clean: default-clean

include ../../Make.rules
