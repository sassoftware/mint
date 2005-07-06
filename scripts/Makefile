#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All Rights Reserved
#

script_dist = job-server mklivecd mkinstroots.sh

extra_dist = Makefile installable_iso.conf

dist_files = $(script_dist) $(extra_dist)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)/$(datadir)/mint/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/mint/scripts/$$f; \
	done;
	install -m 644 installable_iso.conf $(DESTDIR)/$(datadir)/mint/scripts/

dist: default-dist

clean: default-clean

include ../Make.rules
