#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#

script_dist = adduser job-server mklivecd

extra_dist = Makefile

dist_files = $(script_dist) $(extra_dist)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)/$(datadir)/imagetool/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/imagetool/scripts/$$f; \
	done;

dist: default-dist

clean: default-clean

include ../Make.rules
