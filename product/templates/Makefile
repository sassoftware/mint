#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = 

kid_files = \
	frontPage.kid		\
	layout.kid

python_files = __init__.py

extra_dist =

dist_files = $(extra_dist) $(kid_files) $(python_files)

all: default-all default-subdirs

install: kidfiles-install install-subdirs pyfiles-install

subdirs: default-subdirs

kidfiles-install:
	kidc --strip-dest-dir $$(pwd) $$(pwd)
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(kid_files) *.pyc; do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

dist: default-dist 

clean: default-clean

include ../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
