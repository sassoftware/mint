#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#

SUBDIRS = 

python_files =			\
	fixowners.py		\
	fixownersconfig.py

cron_files = fixowners

conf = fixowners.conf

extra_dist = Makefile fixowners.conf fixowners

dist_files = $(python_files) $(extra_dist)

all: default-all default-subdirs

install: install-subdirs
	mkdir -p $(DESTDIR)$(maillistdir)/bin
	for f in $(python_files) $(conf); do \
		mkdir -p `dirname $(DESTDIR)/$(maillistdir)/bin/$$f`; \
		install $$f $(DESTDIR)/$(maillistdir)/bin/; \
	done
	mkdir -p $(DESTDIR)$(sysconfdir)/cron.hourly
	for f in $(cron_files); do \
		install $$f $(DESTDIR)$(sysconfdir)/cron.hourly; \
	done

dist: default-dist

clean: default-clean

include ../Make.rules

#vim: sts=0 noexpandtab ts=8
