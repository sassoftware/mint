#
# Copyright (c) 2004-2005 rpath, Inc.
#
# All Rights Reserved
#

script_dist = job-server mklivecd mkinstroots reset update-package-index

extra_dist = Makefile installable_iso.conf live_iso.conf

dist_files = $(script_dist) $(extra_dist)

all: default-all

install: default-install
	mkdir -p $(DESTDIR)/$(datadir)/mint/scripts/
	for f in $(script_dist); do \
		install -m 755 $$f $(DESTDIR)/$(datadir)/mint/scripts/$$f; \
	done;
	mkdir -p $(DESTDIR)/$(confdir)
	install -m 644 installable_iso.conf $(DESTDIR)/$(confdir)
	install -m 644 live_iso.conf $(DESTDIR)/$(confdir)

dist: default-dist

clean: default-clean

include ../Make.rules
