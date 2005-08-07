#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

kid_files =		\
	browse.kid	\
	error.kid	\
	files.kid	\
	notice.kid	\
	trove_info.kid

python_files = __init__.py

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
