#
# Copyright (c) 2006 rPath, Inc.
#
# All Rights Reserved
#

TOPDIR=..

bin_files = \
       rbuilder

extra_dist = Makefile rbuilder-wrapper

dist_files = $(bin_files) $(extra_dist)

all: default-all
	mkdir -p $(TOPDIR)/bin
	install -m755 rbuilder-wrapper $(TOPDIR)/bin/rbuilder-wrapper
	for f in $(bin_files); do \
		ln -sf rbuilder-wrapper $(TOPDIR)/bin/$$f; \
	done

install-mkdirs:
	mkdir -p $(DESTDIR)$(bindir)

install: install-mkdirs
	for f in $(bin_files); do \
		install -m755 $$f $(DESTDIR)$(bindir)/$$f; \
	done

dist: default-dist

clean: default-clean

include $(TOPDIR)/Make.rules
