#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#

kid_files = \
	joinRequest.kid		\
	registerNewUser.kid	\
	validateNewEmail.kid

python_files = __init__.py

extra_dist = Makefile

dist_files = $(extra_dist) $(kid_files) $(python_files)

all: default-all

install: kidfiles-install pyfiles-install

kidfiles-install:
	kidc --strip-dest-dir $$(pwd) $(kid_files)
	mkdir -p $(DESTDIR)$(mintdir)$(DIR)
	for f in $(kid_files) *.pyc; do \
                cp -a $$f $(DESTDIR)$(mintdir)$(DIR)/$$f; \
        done

dist: default-dist 

clean: default-clean

include ../../../Make.rules
# vim: set sts=8 sw=8 noexpandtab :
