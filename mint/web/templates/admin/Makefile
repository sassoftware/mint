#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

kid_files =			\
	add_outbound.kid	\
	frontPage.kid		\
	external.kid		\
	maintenance.kid		\
	notify.kid		\
	project.kid		\
	report.kid		\
	outbound.kid		\
	user.kid		\
	newUser.kid		\
	jobs.kid		\
	external.kid		\
	primeMirror.kid


python_files =

extra_dist = Makefile

dist_files = $(extra_dist) $(kid_files) $(python_files)

all: default-all

install: kidfiles-install pyfiles-install

kidfiles-install:
	kidc --strip-dest-dir $$(pwd) $$(pwd)
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(kid_files) *.pyc; do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

dist: default-dist

clean: default-clean

include ../../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
